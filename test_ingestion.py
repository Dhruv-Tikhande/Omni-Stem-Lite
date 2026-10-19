import os
import sys
from dotenv import load_dotenv
load_dotenv()
from PIL import Image

# Import from backend
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from ingestion_engine import process_pdf, ingest_document

def analyze_extraction(pdf_path):
    print("--- 2. IMAGE EXTRACTION ---")
    text_content, images = process_pdf(pdf_path)
    for img in images:
        img_path = img["path"]
        md5_hash = img["hash"]
        
        # Get dimensions
        with Image.open(img_path) as pil_img:
            width, height = pil_img.size
            format = pil_img.format
            
        file_size = os.path.getsize(img_path)
        
        print(f"Extracted image: {os.path.basename(img_path)}")
        print(f"  Format/Ext: {format} / {os.path.splitext(img_path)[1]}")
        print(f"  Dimensions: {width} x {height}")
        print(f"  File size: {file_size} bytes")
        print(f"  Hash: {md5_hash}")
        print()

def test_ingestion(pdf_path):
    print("--- 5. ACTUAL TEST ---")
    ingest_document(pdf_path, "http://localhost:8000")

if __name__ == "__main__":
    analyze_extraction("test_3_images.pdf")
    test_ingestion("test_3_images.pdf")
