import time
import json
import base64
import requests
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any

class VisionAnalysis(BaseModel):
    diagram_type: str = Field(default="Unknown")
    components: List[Dict[str, str]] = Field(default_factory=list)
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    clarification_required: bool = Field(default=False)
    candidate_entities: List[str] = Field(default_factory=list)

def fallback_json_parser(raw_text: str) -> dict:
    """Attempts to extract and parse JSON from a raw model response."""
    # First, try to parse directly
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass
        
    # Second, try finding a JSON block (e.g., inside ```json ... ``` or just {...})
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw_text[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass
            
    # Absolute fallback if all parsing fails
    print("⚠️ Failed to parse valid JSON from model response. Using fallback schema.")
    return {
        "diagram_type": "Parse Error",
        "components": [{"error": "Could not parse components"}],
        "relationships": [],
        "clarification_required": True,
        "candidate_entities": []
    }

def analyze_diagram_remote(image_path: str, user_query: str, colab_url: str):
    start_time = time.time()
    import os
    
    print(f"🚀 Sending request to Remote Colab Server at {colab_url}...")
    try:
        # Send multipart/form-data request to the remote Colab server
        with open(image_path, "rb") as image_file:
            files = {"file": (os.path.basename(image_path), image_file, "image/png")}
            data = {"user_query": user_query}
            
            response = requests.post(f"{colab_url.rstrip('/')}/analyze", files=files, data=data, timeout=120)
            response.raise_for_status()
            
        resp_json = response.json()
        
        if resp_json.get("status") == "success":
            parsed_json = resp_json.get("data", {})
        else:
            raw_output = resp_json.get("raw", "{}")
            print(f"⚠️ Colab parsing error: {resp_json.get('message')}. Attempting local fallback parse on raw output...")
            parsed_json = fallback_json_parser(raw_output)
            
    except Exception as e:
        print(f"❌ Error communicating with Colab: {e}")
        parsed_json = fallback_json_parser("{}")
        
    latency = time.time() - start_time
    print(f"✨ Response Received in {latency:.2f}s!")
    
    try:
        validated_data = VisionAnalysis(**parsed_json)
    except ValidationError as e:
        print(f"⚠️ Validation Error: {e}")
        # Use fallback if validation fails completely
        validated_data = VisionAnalysis(
            diagram_type="Validation Error",
            clarification_required=True
        )
        
    return validated_data.model_dump(), latency

# --- Local Test Execution ---
if __name__ == "__main__":
    # Replace with a test image, query and your actual Colab ngrok URL
    try:
        res, lat = analyze_diagram_remote(
            "processed_images/page_1_300dpi.png", 
            "What is shown in this diagram?", 
            "http://localhost:8000"
        )
        print(f"Test Result:\n{json.dumps(res, indent=2)}")
    except Exception as e:
        print(f"Test failed: {e}")