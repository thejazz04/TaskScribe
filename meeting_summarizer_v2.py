"""
Meeting Summarizer V2 - Improved extraction of summary, decisions, and action items
Uses a multi-stage approach with better prompting and structured extraction
"""
import os
import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Dict, List, Any

# Configuration
TRANSCRIPTION_FILE = "transcription.txt"
OUTPUT_JSON = "meeting_summary.json"
OUTPUT_TXT = "meeting_summary.txt"
MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"  # Better for instruction following

class MeetingSummarizer:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(self.device_str)
        print(f"Using device: {self.device}")
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """Load the LLM model with quantization if available"""
        print(f"Loading model: {self.model_name}")
        
        try:
            # Try 4-bit quantization for efficiency (only on CUDA)
            if self.device.type == "cuda":
                try:
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                    )
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        quantization_config=bnb_config,
                        device_map="auto",
                        trust_remote_code=True,
                    )
                    print("Loaded with 4-bit quantization")
                except Exception as e:
                    print(f"4-bit loading failed: {e}")
                    print("Trying standard loading...")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        device_map="auto",
                        trust_remote_code=True,
                    )
            else:
                # CPU loading
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map=None,
                    trust_remote_code=True,
                )
                self.model.to(self.device)
        except Exception as e:
            print(f"Model loading failed: {e}")
            raise
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        print("Model loaded successfully!")
    
    def generate_response(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate response from the model"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4000)
        
        # Determine the correct device for inputs
        # When using device_map="auto", inputs must be on the same device as the model's embedding layer
        try:
            # Try to get the device from the model's first parameter (embedding layer)
            first_param = next(self.model.parameters())
            input_device = first_param.device
        except (StopIteration, AttributeError):
            # Fallback: use the device we set
            input_device = self.device
        
        # Move inputs to the correct device
        inputs = {k: v.to(input_device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.3,  # Lower temperature for more focused output
                top_p=0.9,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return response.strip()
    
    def extract_summary(self, transcript: str) -> str:
        """Extract concise meeting summary"""
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a professional meeting assistant. Create a concise executive summary of the meeting.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the following meeting transcript and write a concise summary in 4-6 sentences. Focus on:
- Main topics discussed
- Key outcomes
- Overall purpose of the meeting

Do NOT copy the transcript verbatim. Synthesize the information.

TRANSCRIPT:
{transcript[:3000]}

SUMMARY:<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""
        
        summary = self.generate_response(prompt, max_tokens=300)
        return summary
    
    def extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions made during the meeting"""
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a meeting assistant that extracts decisions from meeting transcripts. A decision is a conclusion, agreement, or resolution reached by the team. Examples: "We decided to use Python", "The team agreed on the deadline", "It was decided that John will lead the project".<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the meeting transcript and extract ALL DECISIONS that were made. Look for phrases like:
- "We decided to..."
- "The team agreed..."
- "It was decided..."
- "We will..."
- "Let's go with..."
- Any conclusion or agreement reached

Return ONLY a valid JSON array of decision strings. Example format:
["Decision 1 text", "Decision 2 text"]

If no decisions found, return: []

TRANSCRIPT:
{transcript[:3500]}

Return ONLY the JSON array, nothing else:<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""
        
        response = self.generate_response(prompt, max_tokens=600)
        print(f"DEBUG - Decisions raw response: {response[:200]}...")
        decisions = self.parse_json_array(response)
        
        # Fallback: try to extract decisions from text if JSON parsing fails
        if not decisions:
            decisions = self.fallback_extract_decisions(response, transcript)
        
        print(f"DEBUG - Extracted {len(decisions)} decisions")
        return decisions
    
    def extract_action_items(self, transcript: str) -> List[Dict[str, Any]]:
        """Extract action items with owner and due date"""
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a meeting assistant that extracts action items from meetings. An action item is a task, assignment, or todo that someone needs to complete. Look for phrases like: "John will...", "We need to...", "Task: ...", "Action: ...", "Follow up on...".<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Read the meeting transcript and extract ALL ACTION ITEMS. Look for:
- Tasks assigned to people ("John will prepare the report")
- Follow-up items ("We need to review the proposal")
- To-do items ("Send the email by Friday")
- Any work that needs to be done

Return ONLY a valid JSON array. Example:
[
  {{"task": "Prepare quarterly report", "owner": "John", "due_date": "Friday", "notes": null}},
  {{"task": "Review proposal", "owner": null, "due_date": null, "notes": "Urgent"}}
]

If no action items found, return: []

TRANSCRIPT:
{transcript[:3500]}

Return ONLY the JSON array, nothing else:<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""
        
        response = self.generate_response(prompt, max_tokens=800)
        print(f"DEBUG - Action items raw response: {response[:200]}...")
        action_items = self.parse_json_array(response)
        
        # Ensure proper structure
        if action_items and isinstance(action_items, list):
            for item in action_items:
                if isinstance(item, dict):
                    item.setdefault("task", "")
                    item.setdefault("owner", None)
                    item.setdefault("due_date", None)
                    item.setdefault("notes", None)
                elif isinstance(item, str):
                    # Convert string items to dict format
                    action_items[action_items.index(item)] = {
                        "task": item,
                        "owner": None,
                        "due_date": None,
                        "notes": None
                    }
        
        # Fallback: try to extract from text if JSON parsing fails
        if not action_items:
            action_items = self.fallback_extract_action_items(response, transcript)
        
        print(f"DEBUG - Extracted {len(action_items)} action items")
        return action_items if action_items else []
    
    def parse_json_array(self, text: str) -> List:
        """Parse JSON array from model output"""
        # Try to find JSON array in the text
        text = text.strip()
        
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'^json\s*', '', text, flags=re.IGNORECASE)
        
        # Remove any leading/trailing text before/after JSON
        # Find JSON array pattern
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                result = json.loads(json_str)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError as e:
                print(f"DEBUG - JSON parse error: {e}")
                # Try to fix common JSON issues
                json_str = json_str.replace("'", '"')  # Replace single quotes
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re.sub(r',\s*]', ']', json_str)
                try:
                    result = json.loads(json_str)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass
        
        # Try parsing the whole text
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        return []
    
    def fallback_extract_decisions(self, response: str, transcript: str) -> List[str]:
        """Fallback method to extract decisions from text if JSON parsing fails"""
        decisions = []
        
        # Look for numbered lists
        numbered = re.findall(r'\d+\.\s*([^\n]+)', response)
        if numbered:
            decisions.extend([d.strip() for d in numbered if len(d.strip()) > 10])
        
        # Look for bullet points
        bullets = re.findall(r'[-•*]\s*([^\n]+)', response)
        if bullets:
            decisions.extend([b.strip() for b in bullets if len(b.strip()) > 10])
        
        # Look for quoted strings
        quoted = re.findall(r'"([^"]+)"', response)
        if quoted:
            decisions.extend([q.strip() for q in quoted if len(q.strip()) > 10])
        
        return decisions[:10]  # Limit to 10 decisions
    
    def fallback_extract_action_items(self, response: str, transcript: str) -> List[Dict[str, Any]]:
        """Fallback method to extract action items from text if JSON parsing fails"""
        action_items = []
        
        # Look for task patterns in the response
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue
            
            # Try to extract task information
            task_match = re.search(r'(?:task|action|todo|item)[:\-]?\s*(.+)', line, re.IGNORECASE)
            if task_match:
                task = task_match.group(1).strip()
                owner_match = re.search(r'(?:owner|assigned to|by)\s*:?\s*([A-Z][a-z]+)', line, re.IGNORECASE)
                due_match = re.search(r'(?:due|deadline|by)\s*:?\s*([^\n,]+)', line, re.IGNORECASE)
                
                action_items.append({
                    "task": task,
                    "owner": owner_match.group(1) if owner_match else None,
                    "due_date": due_match.group(1).strip() if due_match else None,
                    "notes": None
                })
        
        # If no structured items found, extract simple tasks
        if not action_items:
            numbered = re.findall(r'\d+\.\s*([^\n]+)', response)
            for item in numbered[:5]:  # Limit to 5
                if len(item.strip()) > 10:
                    action_items.append({
                        "task": item.strip(),
                        "owner": None,
                        "due_date": None,
                        "notes": None
                    })
        
        return action_items
    
    def summarize_meeting(self, transcript_path: str) -> Dict[str, Any]:
        """Main method to summarize a meeting"""
        # Read transcript
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
        
        print(f"Transcript length: {len(transcript)} characters")
        
        # Load model if not already loaded
        if self.model is None:
            self.load_model()
        
        # Extract components
        print("\n1. Extracting summary...")
        summary = self.extract_summary(transcript)
        print(f"Summary: {summary[:200]}...")
        
        print("\n2. Extracting decisions...")
        decisions = self.extract_decisions(transcript)
        print(f"Found {len(decisions)} decisions")
        
        print("\n3. Extracting action items...")
        action_items = self.extract_action_items(transcript)
        print(f"Found {len(action_items)} action items")
        
        return {
            "summary": summary,
            "decisions": decisions,
            "action_items": action_items
        }
    
    def save_results(self, results: Dict[str, Any], json_path: str, txt_path: str):
        """Save results to JSON and TXT files"""
        # Save JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved JSON to: {json_path}")
        
        # Save TXT
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MEETING SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("SUMMARY:\n")
            f.write("-" * 80 + "\n")
            f.write(results["summary"] + "\n\n")
            
            f.write("DECISIONS:\n")
            f.write("-" * 80 + "\n")
            if results["decisions"]:
                for i, decision in enumerate(results["decisions"], 1):
                    f.write(f"{i}. {decision}\n")
            else:
                f.write("No decisions recorded.\n")
            f.write("\n")
            
            f.write("ACTION ITEMS:\n")
            f.write("-" * 80 + "\n")
            if results["action_items"]:
                for i, item in enumerate(results["action_items"], 1):
                    f.write(f"\n{i}. {item.get('task', 'N/A')}\n")
                    f.write(f"   Owner: {item.get('owner') or 'Not assigned'}\n")
                    f.write(f"   Due Date: {item.get('due_date') or 'Not specified'}\n")
                    if item.get('notes'):
                        f.write(f"   Notes: {item.get('notes')}\n")
            else:
                f.write("No action items recorded.\n")
        
        print(f"Saved TXT to: {txt_path}")


def main():
    """Main execution function"""
    summarizer = MeetingSummarizer()
    
    try:
        results = summarizer.summarize_meeting(TRANSCRIPTION_FILE)
        summarizer.save_results(results, OUTPUT_JSON, OUTPUT_TXT)
        
        print("\n" + "=" * 80)
        print("MEETING SUMMARIZATION COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
