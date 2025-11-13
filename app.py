# app.py (complete - replace your existing file)
import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer, util
import pickle
import os
from typing import Tuple, List

st.set_page_config(page_title="Gita RAG", layout="centered")
st.title("Gita Question Answering (RAG)")

# ---------- Config ----------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANED_PKL = os.path.join(APP_DIR, "cleaned_text.pkl")
EMB_PATH = os.path.join(APP_DIR, "vector_embeddings.pt")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"  # fast & small
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TOP_K = 5  # number of retrieved passages
MAX_CONTEXT_TOKENS = 2000  # used heuristically when assembling prompt
# ----------------------------

st.sidebar.markdown(f"**Device:** {DEVICE}")
st.sidebar.markdown("If `vector_embeddings.pt` is missing, app will compute them from `cleaned_text.pkl` (may take time).")

@st.cache_resource(show_spinner=False)
def load_embedding_model(embedding_model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(embedding_model_name)

@st.cache_resource(show_spinner=False)
def ensure_data_and_embeddings() -> Tuple[List[str], torch.Tensor]:
    """
    Loads cleaned_text.pkl. If vector_embeddings.pt missing, compute embeddings and save them.
    Returns: cleaned_text (list of strings), embeddings (CPU tensor)
    """
    if not os.path.exists(CLEANED_PKL):
        raise FileNotFoundError(f"{CLEANED_PKL} not found. Please put cleaned_text.pkl in the app folder.")

    # load cleaned_text
    with open(CLEANED_PKL, "rb") as f:
        cleaned_text = pickle.load(f)

    # Basic validation
    if isinstance(cleaned_text, dict):
        # Try to extract common structures; if not clear, raise to force inspection.
        # Many repos store text as list; adapt here if your structure is different.
        raise ValueError("cleaned_text.pkl is a dict — inspect its structure and adapt the loader.")

    # if embeddings exist, load and return
    if os.path.exists(EMB_PATH):
        embeddings = torch.load(EMB_PATH, map_location="cpu")
        # ensure shape matches
        if embeddings.shape[0] != len(cleaned_text):
            st.warning("Number of embeddings does not match cleaned_text length. Recomputing embeddings.")
        else:
            return cleaned_text, embeddings

    # compute embeddings
    st.info("Embeddings not found or mismatched — computing embeddings now (may take a few minutes).")
    embed_model = load_embedding_model()
    # sentence-transformers returns numpy or tensor depending on settings; convert to torch.Tensor
    # compute in batches to avoid OOM
    batch_size = 64
    embs = []
    for i in range(0, len(cleaned_text), batch_size):
        batch = cleaned_text[i:i+batch_size]
        emb = embed_model.encode(batch, convert_to_tensor=True, show_progress_bar=False)
        embs.append(emb.cpu())
    embeddings = torch.cat(embs, dim=0)
    torch.save(embeddings, EMB_PATH)
    st.success(f"Saved embeddings to {EMB_PATH} (shape: {embeddings.shape})")
    return cleaned_text, embeddings

@st.cache_resource(show_spinner=False)
def try_load_model(model_name: str = "meta-llama/Llama-3.2-3B-Instruct") -> Tuple[object, object]:
    """
    Try to load model with bitsandbytes 4-bit config. If bitsandbytes not available,
    try fallback load.
    """
    tokenizer = None
    model = None

    # First try 4-bit load if bitsandbytes available
    try:
        import bitsandbytes  # may raise
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if DEVICE.type == "cuda" else None,
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_safetensors=True, trust_remote_code=True)
        tokenizer.pad_token_id = tokenizer.eos_token_id
        return model, tokenizer
    except Exception as e:
        st.warning("4-bit load failed or bitsandbytes missing; attempting fallback load. (" + str(e)[:200] + ")")

    # Fallback: try normal load (may be large for CPU)
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto" if DEVICE.type == "cuda" else None, trust_remote_code=True)
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_safetensors=True, trust_remote_code=True)
        tokenizer.pad_token_id = tokenizer.eos_token_id
        return model, tokenizer
    except Exception as e:
        st.error("Failed to load model. Error: " + str(e)[:300])
        return None, None

def build_prompt_from_context(query: str, contexts: List[str]) -> str:
    system = (
        "You are a compassionate guide. Answer questions based ONLY on the given context of the Bhagavad Gita. "
        "Quote the text you used from the Gita context. If the question is NOT related to the context, reply: "
        "'this is not relate dto bhagabat gita'. Keep language simple (understandable by a 15-year-old). "
        "Answer must be <= 200 words and do not use markdown."
    )
    joined_context = "\n\n---\n\n".join(contexts)
    prompt = f"{system}\n\nGita CONTEXT:\n{joined_context}\n\nUser: {query}\nAssistant:"
    return prompt

def generate_answer(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    model.to(DEVICE)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_CONTEXT_TOKENS).to(DEVICE)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            do_sample=True,
            max_new_tokens=max_new_tokens,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
            top_p=0.95,
            temperature=0.7,
        )
    generated_tokens = out[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    return text.strip()

# ---------------------- UI / Flow ----------------------
with st.expander("Status / Setup", expanded=True):
    st.write(f"Running on device: **{DEVICE}**")
    st.write("Model will not load until you press 'Load model and embeddings' — this prevents the UI from freezing.")
    if st.button("Load model and embeddings"):
        try:
            with st.spinner("Loading data & embeddings..."):
                embedding_model = load_embedding_model()
                cleaned_text, embeddings = ensure_data_and_embeddings()
            if cleaned_text is None or embeddings is None:
                st.error("Failed to load data or embeddings.")
                st.stop()
            with st.spinner("Loading LLM (may take a while)..."):
                model, tokenizer = try_load_model()
            if model is None or tokenizer is None:
                st.stop()
            st.session_state["model_loaded"] = True
            st.session_state["model"] = model
            st.session_state["tokenizer"] = tokenizer
            st.session_state["embedding_model"] = embedding_model
            st.session_state["cleaned_text"] = cleaned_text
            st.session_state["embeddings"] = embeddings
            st.success("Model and data loaded successfully.")
        except Exception as e:
            st.error(f"Error during load: {e}")

# use from session state if available
if st.session_state.get("model_loaded", False):
    model = st.session_state["model"]
    tokenizer = st.session_state["tokenizer"]
    embedding_model = st.session_state["embedding_model"]
    cleaned_text = st.session_state["cleaned_text"]
    embeddings = st.session_state["embeddings"]
else:
    model = tokenizer = embedding_model = cleaned_text = embeddings = None

# Main query UI
query = st.text_area("Ask your question about the Gita:", height=120)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Get Answer"):
        if model is None or tokenizer is None or embedding_model is None or cleaned_text is None or embeddings is None:
            st.error("Model and embeddings not loaded. Click 'Load model and embeddings' first.")
        elif not query or query.strip() == "":
            st.error("Please enter a question.")
        else:
            with st.spinner("Searching context and generating answer..."):
                # compute query embedding
                q_emb = embedding_model.encode([query], convert_to_tensor=True)
                # ensure embeddings on CPU for similarity computation (sentence-transformers util expects cpu tensors)
                if isinstance(embeddings, torch.Tensor):
                    embeddings_cpu = embeddings.cpu()
                else:
                    embeddings_cpu = torch.tensor(embeddings)  # fallback
                sims = util.cos_sim(q_emb, embeddings_cpu)  # shape [1, N]
                # get topk
                topk_vals, topk_idx = torch.topk(sims, k=min(TOP_K, embeddings_cpu.shape[0]), largest=True)
                topk_idx = topk_idx.squeeze(0).tolist()
                # collect contexts
                contexts = [cleaned_text[i] for i in topk_idx]
                # show what was retrieved
                st.markdown("**Retrieved contexts (quoted):**")
                for rank, idx in enumerate(topk_idx, start=1):
                    st.write(f"**#{rank} (index {idx})**: {cleaned_text[idx][:400]}{'...' if len(cleaned_text[idx])>400 else ''}")
                # build prompt and generate
                prompt = build_prompt_from_context(query, contexts)
                answer = generate_answer(model, tokenizer, prompt, max_new_tokens=256)
                st.markdown("### Answer")
                st.write(answer)

with col2:
    st.markdown("### Debug / Info")
    if embeddings is not None:
        st.write(f"Embeddings shape: {embeddings.shape}")
    if cleaned_text is not None:
        st.write(f"Docs: {len(cleaned_text)}")
    st.write("Tip: If the LLM fails to load on CPU, use a smaller model or enable GPU.")

# allow saving a debug copy of the prompt
if st.button("Show (and download) last prompt"):
    if 'prompt' in locals():
        st.code(prompt)
        # save
        with open(os.path.join(APP_DIR, "last_prompt.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        st.success("Saved last_prompt.txt")
    else:
        st.info("No prompt generated yet.")
