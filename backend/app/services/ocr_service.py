from PIL import Image
import pytesseract, fitz
def ocr_pdf(path: str):
    doc=fitz.open(path); pages=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
        pages.append({"page":i+1,"text":pytesseract.image_to_string(img).strip()})
    return pages
