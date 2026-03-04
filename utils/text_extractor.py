import os

def extract_text(filepath, original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()

    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    elif ext == 'pdf':
        text = ''
        # Try pdfplumber first (best quality)
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
            if text.strip():
                return text
        except Exception:
            pass

        # Fallback: PyPDF2
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + '\n'
            if text.strip():
                return text
        except Exception:
            pass

        raise Exception("Could not extract text from PDF. Make sure pdfplumber is installed: pip install pdfplumber")

    elif ext == 'docx':
        try:
            from docx import Document
            doc = Document(filepath)
            return '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        except ImportError:
            raise Exception("python-docx not installed: pip install python-docx")

    return ''
