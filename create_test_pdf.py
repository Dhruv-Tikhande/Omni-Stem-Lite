import fitz
import sys

def create_test_pdf():
    doc = fitz.open()
    page = doc.new_page()
    
    # Let's create some dummy rectangles to insert as images
    rects = [
        fitz.Rect(50, 50, 200, 200),
        fitz.Rect(50, 250, 200, 400),
        fitz.Rect(50, 450, 200, 600)
    ]
    
    colors = [
        (1, 0, 0), # red
        (0, 1, 0), # green
        (0, 0, 1)  # blue
    ]
    
    # We will use some small real images or create raw images
    # since we need actual image extraction to work. PyMuPDF can insert images.
    from PIL import Image
    import io
    
    for i, color in enumerate(colors):
        img = Image.new('RGB', (100, 100), color=tuple(int(c * 255) for c in color))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        page.insert_image(rects[i], stream=img_byte_arr.getvalue())
        
    doc.save("test_3_images.pdf")
    print("Created test_3_images.pdf")

if __name__ == "__main__":
    create_test_pdf()
