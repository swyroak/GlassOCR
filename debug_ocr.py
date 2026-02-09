import fitz
import pytesseract
from PIL import Image
import io
import os

# Configuration
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

target_pdf = "sample.pdf" # Replace with your PDF file path
page_num = 11
page_index = 10 # Testing Page 11 (Body text?)

configs = [
    {"name": "Zoom 3, jpn_vert, psm 5", "zoom": 3, "lang": "jpn_vert", "config": "--psm 5"},
    {"name": "Zoom 3, jpn_vert, psm 6", "zoom": 3, "lang": "jpn_vert", "config": "--psm 6"},
    {"name": "Zoom 3, jpn_vert, psm 3", "zoom": 3, "lang": "jpn_vert", "config": "--psm 3"},
    {"name": "Zoom 3, jpn_vert, psm 1", "zoom": 3, "lang": "jpn_vert", "config": "--psm 1"},
    {"name": "Zoom 3, jpn, psm 6", "zoom": 3, "lang": "jpn", "config": "--psm 6"},
]

doc = fitz.open(target_pdf)
page = doc.load_page(page_index)

print(f"Testing on Page {page_index+1}")

for cfg in configs:
    print(f"\n--- Testing: {cfg['name']} ---")
    
    mat = fitz.Matrix(cfg['zoom'], cfg['zoom'])
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_data))
    
    # Check if rotation is requested
    if cfg.get('rotate'):
        image = image.rotate(cfg['rotate'], expand=True)
    
    # Don't convert to grayscale unless specified (removed for now)
    
    try:
        text = pytesseract.image_to_string(image, lang=cfg['lang'], config=cfg['config'])
        print(f"--- Output ({len(text)} chars) ---\n{text[:200].replace(chr(10), ' ')}") 
    except Exception as e:
        print(f"Error: {e}")
