import io
from pypdf import PdfReader


def parse_pdf_bytes(file_bytes: bytes) -> list[dict]:
    """
    Parse PDF from bytes in memory — never writes to disk.
    Returns list of {"page_number": int, "content": str}
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({
                "page_number": i + 1,
                "content": text.strip(),
            })

    return pages