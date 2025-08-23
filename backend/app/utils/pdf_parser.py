from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text content from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""
