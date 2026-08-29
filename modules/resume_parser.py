import fitz
def extract_resume_text(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(text_parts).strip()