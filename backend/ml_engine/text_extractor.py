"""
STEP 2: Text Extraction from CV (PDF)

Strategy: Run ALL 3 extraction methods, then pick the best output
using quality heuristics (character count, word diversity, structure).

Methods:
  1. pdfminer.six — Best for text-based PDFs with complex layouts
  2. PyMuPDF (fitz) — Fast, good for standard PDFs
  3. Tesseract OCR — For scanned PDFs / images

Selection: Compare outputs → pick the one with highest quality score.
"""
import os
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_with_pdfminer(pdf_path: str) -> str:
    """Extract text using pdfminer.six — handles complex layouts well."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        logger.warning(f"pdfminer extraction failed: {e}")
        return ""


def extract_with_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fitz) — fast and reliable."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")
        return ""


def extract_with_ocr(pdf_path: str) -> str:
    """
    Extract text using Tesseract OCR.
    Converts PDF pages to images first, then runs OCR on each.
    Best for scanned PDFs where text extraction fails.
    """
    try:
        import fitz  # PyMuPDF for PDF→image conversion
        import pytesseract
        from PIL import Image
        import io

        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(min(len(doc), 10)):  # Limit to 10 pages
            page = doc[page_num]
            # Render page as image at 300 DPI for good OCR quality
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            # Run OCR
            page_text = pytesseract.image_to_string(img, lang="eng")
            text_parts.append(page_text)

        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
        return ""


def calculate_quality_score(text: str) -> float:
    """
    Rate the quality of extracted text.
    Higher score = better extraction.

    Factors:
    - Character count (longer = more content extracted)
    - Word diversity (unique words / total words — catches garbage repetition)
    - Has structure indicators (emails, phone numbers, section headers)
    - Low garbage ratio (non-printable chars, excessive whitespace)
    """
    if not text or len(text) < 50:
        return 0.0

    score = 0.0

    # 1. Character count (log scale to not over-weight very long texts)
    import math
    char_score = min(math.log(len(text) + 1) / math.log(10000), 1.0) * 30
    score += char_score

    # 2. Word diversity
    words = text.lower().split()
    if len(words) > 10:
        diversity = len(set(words)) / len(words)
        score += diversity * 25  # Max 25 points

    # 3. Structure indicators (signs of a real CV)
    structure_patterns = [
        r"[\w\.-]+@[\w\.-]+",  # Email
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
        r"\b(experience|education|skills|projects|summary|objective)\b",
        r"\b(university|college|bachelor|master|phd|degree)\b",
        r"\b(python|java|javascript|react|django|sql|aws)\b",
        r"\b\d{4}\s*[-–]\s*(\d{4}|present|current)\b",  # Date ranges
    ]
    structure_hits = 0
    text_lower = text.lower()
    for pattern in structure_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            structure_hits += 1
    score += (structure_hits / len(structure_patterns)) * 25

    # 4. Garbage ratio (penalize non-printable chars)
    printable_ratio = sum(1 for c in text if c.isprintable() or c in "\n\t") / len(text)
    score += printable_ratio * 20

    return round(score, 2)


def extract_text_from_cv(pdf_path: str) -> Tuple[str, str, dict]:
    """
    Main extraction function — runs all 3 methods and picks the best.

    Returns:
        (best_text, method_used, all_results_dict)
    """
    logger.info(f"Extracting text from: {pdf_path}")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"CV file not found: {pdf_path}")

    # Run all 3 extractors
    results = {}

    pdfminer_text = extract_with_pdfminer(pdf_path)
    results["pdfminer"] = {
        "text": pdfminer_text,
        "quality": calculate_quality_score(pdfminer_text),
        "char_count": len(pdfminer_text),
    }

    pymupdf_text = extract_with_pymupdf(pdf_path)
    results["pymupdf"] = {
        "text": pymupdf_text,
        "quality": calculate_quality_score(pymupdf_text),
        "char_count": len(pymupdf_text),
    }

    ocr_text = extract_with_ocr(pdf_path)
    results["ocr"] = {
        "text": ocr_text,
        "quality": calculate_quality_score(ocr_text),
        "char_count": len(ocr_text),
    }

    # Pick the best by quality score
    best_method = max(results.keys(), key=lambda k: results[k]["quality"])
    best_text = results[best_method]["text"]

    # Fallback: if best text is too short, try combining
    if len(best_text) < 100:
        combined = "\n".join(
            r["text"] for r in results.values() if r["text"]
        )
        if len(combined) > len(best_text):
            best_text = combined
            best_method = "combined"

    logger.info(
        f"Best method: {best_method} "
        f"(pdfminer={results['pdfminer']['quality']}, "
        f"pymupdf={results['pymupdf']['quality']}, "
        f"ocr={results['ocr']['quality']})"
    )

    return best_text, best_method, results
