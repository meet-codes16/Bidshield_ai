from pathlib import Path
import fitz, json, re
from app.core.config import settings
def extract_pdf_pages(path: str):
    doc=fitz.open(path); pages=[]
    for i,p in enumerate(doc):
        pages.append({"page":i+1,"text":p.get_text("text").strip()})
    return pages
def is_valid_pdf(content: bytes) -> bool:
    if not content.startswith(b"%PDF"): return False
    try:
        doc=fitz.open(stream=content,filetype="pdf"); doc.close(); return True
    except Exception: return False
def save_extracted(document_id,pages):
    out=Path(settings.EXTRACTED_DIR); out.mkdir(parents=True,exist_ok=True)
    # default=str handles document_id being a uuid.UUID (json.dumps can't serialize UUID natively).
    (out/f"{document_id}.json").write_text(json.dumps({"document_id":str(document_id),"pages":pages},indent=2,default=str),encoding="utf-8")
def chunk_pages(pages,max_chars=1200):
    chunks=[]
    for page in pages:
        text=page["text"]
        if not text: continue
        parts=re.split(r"\n\s*\n",text)
        current=""
        for part in parts:
            part=part.strip()
            if not part: continue
            if len(current)+len(part)+1<=max_chars: current=(current+"\n"+part).strip()
            else:
                if current: chunks.append({"page":page["page"],"text":current})
                current=part
        if current: chunks.append({"page":page["page"],"text":current})
    return chunks
