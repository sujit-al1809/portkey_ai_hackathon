"""
Quick Start Script - Get up and running fast
"""
import os
import sys

def print_header(text):
    print("\n" + "="*70)
    print(text)
    print("="*70)

def check_requirements():
    """Check if dependencies are installed"""
    try:
        import portkey_ai
        return True
    except ImportError:
        return False

def main():
    print_header("PORTKEY HACKATHON - COST-QUALITY OPTIMIZER")
    print("\nQuick Start Guide\n")
    
    # Step 1: Check dependencies
    print("Step 1: Checking dependencies...")
    if not check_requirements():
        print("❌ Dependencies not installed")
        print("\nRun: pip install -r requirements.txt")
        return
    print("✅ Dependencies installed\n")
    
    # Step 2: Check API key
    print("Step 2: Checking Portkey API key...")
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        print("❌ PORTKEY_API_KEY not set")
        print("\nSet it with:")
        print("  Windows PowerShell:")
        print("    $env:PORTKEY_API_KEY='your-key-here'")
        print("\n  Linux/Mac:")
        print("    export PORTKEY_API_KEY='your-key-here'")
        print("\nGet your key at: https://app.portkey.ai")
        return
    print("✅ API key found\n")
    
    # Step 3: Test connection
    print("Step 3: Testing Portkey connection...")
    print("Run: python test_config.py")
    print("\nIf the test passes, you're ready!\n")
    
    # Step 4: Next steps
    print_header("READY TO GO!")
    print("\nWhat would you like to do?\n")
    print("1. Test configuration:")
    print("   python test_config.py")
    print("\n2. Run single optimization cycle (demo):")
    print("   python main.py")
    print("\n3. Run continuous monitoring mode:")
    print("   python continuous_mode.py")
    print("\n4. Read documentation:")
    print("   - README.md: Full documentation")
    print("   - SETUP.md: Detailed setup guide")
    print("   - PITCH.md: Hackathon pitch")
    
    print("\n" + "="*70)
    print("Questions? Check SETUP.md or README.md")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
