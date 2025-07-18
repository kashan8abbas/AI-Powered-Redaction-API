from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uuid, shutil, os, pathlib
from utils.redact_image_ai import redact_image_ai
from utils.redact_pdf import redact_pdf
from utils.redact_docx import redact_docx

app = FastAPI()

@app.post("/redact")
async def redact(file: UploadFile = File(...), phrase: str = Form(...)):
    # Use only safe file extension
    ext = pathlib.Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    input_path = os.path.join("temp", filename)

    file.file.seek(0)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if not os.path.exists(input_path):
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # Process by file type
    if ext in (".jpg", ".jpeg", ".png"):
        output_path = redact_image_ai(input_path, phrase)
        media_type = "image/jpeg"
    elif ext == ".pdf":
        output_path = redact_pdf(input_path, phrase, similarity_threshold=70)
        media_type = "application/pdf"
    elif ext == ".docx":
        output_path = redact_docx(input_path, phrase)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    return FileResponse(output_path, media_type=media_type, filename=os.path.basename(output_path))
