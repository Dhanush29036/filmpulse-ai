import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_gemini():
    print("--- Gemini API Test ---")
    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
        print("Please add your key to backend/.env and try again.")
        return

    print(f"Key found: {GEMINI_API_KEY[:4]}...{GEMINI_API_KEY[-4:]}")
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        print("Sending test message: 'Hello! Who are you?'")
        response = model.generate_content("Hello! Who are you?")
        
        print("\n--- Response ---")
        print(response.text)
        print("----------------")
        print("✅ SUCCESS: Gemini API is working correctly!")
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")

if __name__ == "__main__":
    test_gemini()
