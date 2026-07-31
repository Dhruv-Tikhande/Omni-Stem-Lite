from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

# Import the ultra-fast AI engine you built earlier!
from fast_model_engine import generate_stem_response

# Initialize the API
app = FastAPI(title="Omni-STEM API", description="AI Backend for Accessibility Assistant")

# CORS Middleware: This allows your teammate's React app to talk to your Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all connections (Frontend can be on any port)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a temporary folder to hold images sent by the frontend
os.makedirs("temp_uploads", exist_ok=True)

@app.get("/")
def health_check():
    return {"status": "Omni-STEM Backend is actively running 🚀"}

@app.post("/api/analyze")
async def analyze_diagram(
    image: UploadFile = File(...),
    query: str = Form(...)
):
    print(f"📥 Received Request: '{query}' with image '{image.filename}'")
    
    # 1. Save the incoming image to our temp folder
    temp_path = f"temp_uploads/{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    try:
        # 2. Send the image and query to your Qwen2-VL engine
        response_text, latency = generate_stem_response(temp_path, query)
        
        # 3. Clean up the temp image to save space
        os.remove(temp_path)
        
        # 4. Return the structured JSON that the React frontend expects
        return {
            "success": True,
            "query": query,
            "ai_response": response_text,
            "latency_seconds": round(latency, 2)
        }
        
    except Exception as e:
        print(f"❌ Error during AI generation: {str(e)}")
        return {"success": False, "error": str(e)}