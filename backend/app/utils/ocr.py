from PIL import Image
from io import BytesIO
from typing import Optional
import os
import subprocess

# Set environment variable for tesseract
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata'
os.environ['PATH'] = '/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

def extract_text(image_bytes: bytes, lang: str = "eng+chi_sim") -> str:
    """
    Extract text from image bytes using Tesseract OCR
    
    Args:
        image_bytes: Raw image bytes
        lang: Tesseract language parameter (default: eng+chi_sim for English and Chinese)
    
    Returns:
        Extracted text as string
    """
    import tempfile
    
    # Save image to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_file.write(image_bytes)
        temp_file_path = temp_file.name
    
    try:
        # Call tesseract directly using subprocess
        result = subprocess.run([
            '/usr/bin/tesseract', 
            temp_file_path, 
            'stdout', 
            '-l', lang,
            '--tessdata-dir', '/usr/share/tesseract-ocr/5/tessdata'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            text = result.stdout.strip()
            return text
        else:
            raise ValueError(f"Tesseract subprocess failed (code {result.returncode}): {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise ValueError("OCR processing timed out")
    except Exception as e:
        raise ValueError(f"OCR processing failed: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

def get_available_languages() -> str:
    """
    Get list of available Tesseract languages
    
    Returns:
        String of available languages
    """
    try:
        result = subprocess.run([
            '/usr/bin/tesseract', '--list-langs'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "eng"  # fallback to English only
    except Exception:
        return "eng"  # fallback to English only