"""
Test Configuration - Verify Portkey setup
"""
import os
from portkey_ai import Portkey

def test_portkey_connection():
    """Test basic Portkey connection"""
    print("Testing Portkey connection...")
    
    api_key = os.getenv("PORTKEY_API_KEY")
    
    if not api_key:
        print("❌ PORTKEY_API_KEY not set!")
        print("\nSet it with:")
        print("  Windows: $env:PORTKEY_API_KEY='your-key'")
        print("  Linux/Mac: export PORTKEY_API_KEY='your-key'")
        return False
    
    try:
        # Test with OpenAI (Model Catalog format)
        client = Portkey(
            api_key=api_key
        )
        
        response = client.chat.completions.create(
            model="@openai/gpt-4o-mini",  # Model Catalog format
            messages=[{"role": "user", "content": "Say 'test successful' in 2 words"}]
        )
        
        result = response.choices[0].message.content
        print(f"✅ Portkey connection successful!")
        print(f"   Response: {result}")
        print(f"   Tokens: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure you:")
        print("  1. Have a Portkey account at app.portkey.ai")
        print("  2. Added API keys for providers (openai, anthropic, grok) in Model Catalog")
        print("  3. Set PORTKEY_API_KEY environment variable")
        print("  4. Provider slugs match what's in your Portkey dashboard")
        return False


if __name__ == "__main__":
    print("="*60)
    print("PORTKEY CONFIGURATION TEST")
    print("="*60 + "\n")
    
    success = test_portkey_connection()
    
    print("\n" + "="*60)
    if success:
        print("✅ Configuration is correct! You're ready to run main.py")
    else:
        print("❌ Configuration needs fixing. See errors above.")
    print("="*60 + "\n")
