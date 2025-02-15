import json
import httpx
from typing import Dict, List, Tuple
from django.conf import settings

class LLMService:
    """Service class to handle interactions with Google's Gemini Flash API."""
    
    def __init__(self):
        self.api_key = settings.GEMINY_FLASH_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-1.5-flash"
    
    async def extract_actionable_steps(self, note_text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract actionable steps from doctor's notes using Gemini Flash.
        
        Args:
            note_text: The doctor's note text to analyze
            
        Returns:
            Tuple of (checklist_items, plan_items)
        """
        prompt = f"""
        Analyze this doctor's note and extract two types of actionable items:
        1. Checklist: One-time tasks that need to be done
        2. Plan: Scheduled tasks that need to be repeated
        
        Format the response as a JSON with two lists: "checklist" and "plan"
        Each checklist item should have: "description"
        Each plan item should have: "description", "frequency", "duration"
        
        Doctor's Note:
        {note_text}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "parts":[{"text": prompt}]
                        }]
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                text_response = data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract the JSON portion from the response
                try:
                    extracted_data = json.loads(text_response)
                except json.JSONDecodeError:
                    # If the response isn't valid JSON, try to extract JSON-like content
                    import re
                    json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                    if json_match:
                        extracted_data = json.loads(json_match.group())
                    else:
                        # Fallback structure if no JSON found
                        extracted_data = {
                            "checklist": [],
                            "plan": []
                        }
                
                checklist_items = extracted_data.get("checklist", [])
                plan_items = extracted_data.get("plan", [])
                
                return checklist_items, plan_items
                
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return [], []
        except Exception as e:
            print(f"Error occurred: {e}")
            return [], []