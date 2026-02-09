import sys
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Configuration
# Attempt to find tesseract if not in PATH
possible_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

tesseract_cmd = None
# Check if tesseract is in PATH
try:
    pytesseract.get_tesseract_version()
    print("Tesseract found in PATH.")
except:
    print("Tesseract not in PATH. Checking common locations...")
    for path in possible_paths:
        if os.path.exists(path):
            tesseract_cmd = path
            print(f"Tesseract found at: {path}")
            break

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    # If we still haven't found it, we might fail, but let's try proceed and see if user has it set elsewhere or let it error naturally if not found
    pass

def ocr_pdf(pdf_path, output_dir=None, progress_callback=None, zoom=3, psm=5, lang='jpn_vert', tesseract_cmd=None):
    if output_dir is None:
        output_dir = os.getcwd()

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
    print(f"Processing: {pdf_path} (Zoom: {zoom}, PSM: {psm}, Lang: {lang})")
    
    # The original error handling for file existence and opening PDF is removed from here.
    # It's implied that these checks should happen before calling ocr_pdf, or the function
    # will now raise an exception if the file doesn't exist or is invalid.
    doc = fitz.open(pdf_path)
    base_name = os.path.basename(pdf_path)
    output_filename = os.path.splitext(base_name)[0] + "_output.txt"
    output_path = os.path.join(output_dir, output_filename)

    print(f"Writing to: {output_path}")

    # Check/Validate language (Optional validation, but we trust the input mostly)
    # If user provided a custom lang, we try to use it. 
    # If they want auto-fallback logic, we could keep it, but for now let's respect the argument.
    print(f"Using language: {lang}")

    with open(output_path, "w", encoding="utf-8") as f:
        # Process the entire book.
        total_pages = len(doc)
        for i in range(total_pages):
            if progress_callback:
                progress_callback(i + 1, total_pages)
                
            page = doc.load_page(i)
            print(f"  Converting page {i+1}/{total_pages}...")
            
            # Render page to image (higher resolution for better OCR)
            # zoom = 3  # Start using parameter
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Preprocessing
            # Convert to grayscale
            image = image.convert('L')
            
            # Perform OCR
            # --psm 5: Assume a single uniform block of vertically aligned text.
            # This proved effective for the body text in testing.
            config_str = f'--psm {psm}'
            try:
                text = pytesseract.image_to_string(image, lang=lang, config=config_str)
            except Exception as e:
                print(f"OCR Error on page {i}: {e}")
                text = ""
            
            f.write(f"--- Page {i+1} ---\n")
            f.write(text)
            f.write("\n\n")
            
    print(f"Done. Saved to {output_filename}")

if __name__ == "__main__":
    source_dir = os.path.expanduser("~")
    # output_dir = r"C:\Users\947x9\.gemini\antigravity\scratch\ocr_project" # Current directory
    
    # Get list of all PDF files
    pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
    
    # Load processed history
    history_file = "processed_log.txt"
    processed_files = set()
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            processed_files = set(f.read().splitlines())
    
    print(f"Found {len(pdf_files)} PDF files in {source_dir}")
    print(f"Already processed: {len(processed_files)} files")
    
    for filename in pdf_files:
        if filename in processed_files:
            print(f"Skipping {filename} (already processed).")
            continue

        pdf_path = os.path.join(source_dir, filename)
        print(f"\nProcessing: {filename}")
        
        try:
            ocr_pdf(pdf_path)
            print(f"Successfully processed {filename}")
            # Identify success and log
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(filename + "\n")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
