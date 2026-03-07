"""Aura OCR Module

Handles optical character recognition for extracting text
from images and scanned documents to feed into the AI.
"""

import os
from loguru import logger

# Try importing EasyOCR safely
try:
    import easyocr
    import cv2
    import numpy as np
    
    # Initialize the reader only once, dynamically.
    # Warning: Model will be downloaded on first run!
    _reader = None
    
    def get_reader():
        global _reader
        if _reader is None:
            logger.info("Initializing EasyOCR reader for the first time... this may take a moment.")
            # Use English by default. Add more languages as needed.
            _reader = easyocr.Reader(['en'], gpu=False) # CPU by default for broader compatibility
        return _reader

    OCT_AVAILABLE = True

except ImportError:
    logger.warning("EasyOCR or cv2 not installed. Image text extraction will be disabled.")
    OCT_AVAILABLE = False


def extract_text_from_image(image_path: str, max_chars: int = 2000) -> str:
    """Extract text from an image file using EasyOCR.
    
    Args:
        image_path: Path to the image file (png, jpg, jpeg)
        max_chars: Maximum characters to return (to prevent massive prompts)
        
    Returns:
        Extracted text as a string, or empty string on failure.
    """
    if not OCT_AVAILABLE:
        return ""
        
    try:
        reader = get_reader()
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to read image for OCR: {image_path}")
            return ""
            
        # Convert to grayscale to improve OCR slightly
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Run OCR
        # detail=0 returns just the text, not bounding boxes
        results = reader.readtext(gray, detail=0)
        
        text = " ".join(results)
        
        # Cap the length
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            
        if text.strip():
            logger.debug(f"OCR extracted {len(text)} chars from {os.path.basename(image_path)}")
            return text
        return ""
        
    except Exception as e:
        logger.error(f"OCR error on {image_path}: {e}")
        return ""
