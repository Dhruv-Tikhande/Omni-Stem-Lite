import fitz  # PyMuPDF
import os

def pdf_to_300dpi_image(pdf_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Standard PDF DPI is 72. To get 300 DPI, we zoom by 300/72 = 4.166
        zoom_factor = 300 / 72
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        
        # Render the page to an image pixel map
        pix = page.get_pixmap(matrix=mat)
        
        output_path = f"{output_folder}/page_{page_num+1}_300dpi.png"
        pix.save(output_path)
        print(f"Successfully saved high-res patch: {output_path}")

# Test the script
pdf_to_300dpi_image("sample_circuit.pdf", "processed_images")