"""
Test script to verify the meeting summarizer setup
"""
import sys
import subprocess

def test_python_version():
    """Check Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def test_ffmpeg():
    """Check if ffmpeg is installed"""
    print("\nTesting FFmpeg...")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.split('\n')[0]
        print(f"✓ {version_line}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg not found")
        print("  Install: https://ffmpeg.org/download.html")
        return False

def test_package(package_name, import_name=None):
    """Test if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} not found")
        return False

def test_packages():
    """Test all required Python packages"""
    print("\nTesting Python packages...")
    
    packages = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("whisper", "whisper"),
        ("accelerate", "accelerate"),
        ("bitsandbytes", "bitsandbytes"),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(test_package(pkg_name, import_name))
    
    return all(results)

def test_cuda():
    """Test CUDA availability"""
    print("\nTesting CUDA...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available")
            print(f"  Device: {torch.cuda.get_device_name(0)}")
            print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            return True
        else:
            print("⚠ CUDA not available (will use CPU)")
            return True  # Not a failure, just slower
    except ImportError:
        print("✗ Cannot test CUDA (torch not installed)")
        return False

def test_files():
    """Check for required files"""
    print("\nChecking project files...")
    import os
    
    files = [
        "meeting_summarizer_v2.py",
        "complete_pipeline.py",
        "requirements.txt"
    ]
    
    results = []
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file}")
            results.append(True)
        else:
            print(f"✗ {file} not found")
            results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("=" * 80)
    print("MEETING SUMMARIZER - SETUP TEST")
    print("=" * 80)
    
    tests = [
        ("Python Version", test_python_version),
        ("FFmpeg", test_ffmpeg),
        ("Python Packages", test_packages),
        ("CUDA Support", test_cuda),
        ("Project Files", test_files),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Ready to run!")
        print("\nNext steps:")
        print("  1. Place your meeting video as 'meeting.mp4'")
        print("  2. Run: python complete_pipeline.py")
    else:
        print("✗ SOME TESTS FAILED - Please fix the issues above")
        print("\nCommon fixes:")
        print("  - Install FFmpeg: https://ffmpeg.org/download.html")
        print("  - Install packages: pip install -r requirements.txt")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
