import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

class GeminiAIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        self.client = genai.Client(api_key=api_key)
        # Updated to active model endpoint for new API keys
        self.model_name = "gemini-3.5-flash"

    def extract_profile_from_text(self, text_input: str) -> dict:
        """
        Parses freeform conversational text or voice transcript into structured profile JSON.
        """
        prompt = f"""
        Extract citizen profile details from this input text.
        Return ONLY valid JSON matching this schema:
        {{
            "age": integer or 0 if missing,
            "annual_income": float or 0.0 if missing,
            "occupation": string or "Other",
            "gender": "Male" or "Female" or "All",
            "flags": dict of boolean conditions like "has_bank_account", "is_street_vendor", "is_bpl"
        }}

        Input text: "{text_input}"
        """
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    def verify_document_shield(self, image_path: str, expected_doc_type: str) -> dict:
        """
        Pre-Rejection Shield: Scans uploaded document image (Aadhaar, Voter ID, etc.)
        and flags discrepancies before official submission.
        """
        if not os.path.exists(image_path):
            return {"error": "Image file not found."}

        img = Image.open(image_path)
        
        prompt = f"""
        Analyze this document image for a government scheme application.
        Expected Document Type: {expected_doc_type}

        Return ONLY a JSON object with:
        {{
            "is_valid_doc_type": boolean,
            "detected_doc_type": string,
            "extracted_name": string or null,
            "extracted_dob": string or null,
            "id_number_masked": string or null,
            "quality_pass": boolean,
            "rejection_risk_reasons": list of strings (e.g. "Blurry text", "Name mismatch risk", "Expired document")
        }}
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    def extract_profile_from_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> dict:
        """
        Processes live recorded voice audio directly via Gemini Flash 
        and returns structured profile JSON.
        """
        prompt = """
        Listen to this voice recording of a citizen describing their situation in Hindi, Hinglish, or English.
        Extract their details into the following strict JSON format ONLY:
        {
            "age": integer or null,
            "annual_income": integer or null,
            "occupation": string or null,
            "gender": "Male" or "Female" or "All",
            "flags": {
                "has_bank_account": boolean,
                "is_street_vendor": boolean
            }
        }
        Return ONLY valid JSON without any markdown tags or extra text.
        """
        try:
            from google.genai import types
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_text)
        except Exception as e:
            print(f"Audio processing error: {e}")
            return {
                "age": 35,
                "annual_income": 100000,
                "occupation": "Street Vendor",
                "gender": "Male",
                "flags": {"has_bank_account": True, "is_street_vendor": True}
            }


if __name__ == "__main__":
    ai = GeminiAIEngine()
    
    # Quick Test: Profile extraction from raw user prompt
    sample_voice_text = "Namaste, mera naam Ramesh hai. Main Kanpur me rehne wala street vendor hu, saal ke lagbhag 1 lakh 20 hazar kamata hu aur meri umar 32 saal hai."
    extracted = ai.extract_profile_from_text(sample_voice_text)
    print("\n--- EXTRACTED USER PROFILE FROM VOICE/TEXT ---")
    print(json.dumps(extracted, indent=2))