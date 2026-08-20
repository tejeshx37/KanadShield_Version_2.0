from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PageExtraction:
    page_number: int
    text: str
    needs_ocr: bool  # true when the page has no extractable text layer


@dataclass
class PDFExtractionResult:
    pages: list[PageExtraction]
    full_text: str


# A page with fewer than this many characters of native text is treated as
# a scanned image and routed to OCR rather than trusted as "no content".
_MIN_NATIVE_TEXT_CHARS = 20


def extract_pdf_text(pdf_bytes: bytes) -> PDFExtractionResult:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[PageExtraction] = []
    try:
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            pages.append(
                PageExtraction(
                    page_number=i + 1,
                    text=text,
                    needs_ocr=len(text) < _MIN_NATIVE_TEXT_CHARS,
                )
            )
    finally:
        doc.close()
    full_text = "\n\n".join(p.text for p in pages if p.text)
    return PDFExtractionResult(pages=pages, full_text=full_text)


def render_page_to_png(pdf_bytes: bytes, page_number: int, *, dpi: int = 200) -> bytes:
    """Renders one page (1-indexed) to PNG bytes for OCR fallback."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    finally:
        doc.close()
