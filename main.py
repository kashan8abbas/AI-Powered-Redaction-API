from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uuid, shutil, os, cv2
from utils.redact_image_ai import redact_image_ai

app = FastAPI()

@app.post("/redact")
async def redact(file: UploadFile = File(...), phrase: str = Form(...)):
    filename = f"{uuid.uuid4().hex}.jpg"
    input_path = os.path.join("temp", filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    
    img = cv2.imread(input_path)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    output_path = redact_image_ai(input_path, phrase)
    return FileResponse(output_path, media_type="image/jpeg", filename=os.path.basename(output_path))
