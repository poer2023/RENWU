from fastapi import APIRouter, UploadFile, File, HTTPException

from ..utils.ocr import extract_text

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

@router.post("/")
async def ocr_image(file: UploadFile = File(...)):
    """OCR图片文字识别"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        content = await file.read()
        text = extract_text(content)
        return {"text": text, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}") 