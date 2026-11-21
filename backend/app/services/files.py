from pathlib import Path
from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

def extract_text(path: str) -> str:
    p = Path(path); ext = p.suffix.lower()
    try:
        if ext == ".pdf": return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
        if ext == ".docx": return "\n".join(x.text for x in Document(path).paragraphs)
        if ext in (".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css", ".sql", ".xml"):
            return p.read_text(encoding="utf-8", errors="replace")
        if ext == ".xlsx":
            wb = load_workbook(path, read_only=True, data_only=True)
            return "\n".join(" | ".join(str(c) if c is not None else "" for c in row) for ws in wb for row in ws.iter_rows(values_only=True))
        if ext == ".pptx":
            prs = Presentation(path)
            return "\n".join(shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text"))
    except Exception as exc: return f"[Extraction warning: {type(exc).__name__}: {exc}]"
    return f"[No text extractor for {ext}; file is still stored for reference]"
