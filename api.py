from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from comfy_client import describe_media # <-- Import the updated function
import tempfile
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/describe_media") # <-- Renamed endpoint for clarity
async def api_describe_media(
    file: UploadFile = File(...),
    text: str = Form(None)  # <-- optional text support
):
    # Determine file type based on MIME type
    content_type = file.content_type
    if content_type.startswith("image/"):
        file_type = "image"
    elif content_type.startswith("video/"):
        file_type = "video"
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {content_type}. Please upload an image or video."
        )

    # Save uploaded file to a temporary path
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Call the updated function with the detected file type
        result_text = describe_media(tmp_path, file_type, prompt_text=text)

    finally:
        # Clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not result_text:
        raise HTTPException(status_code=500, detail="Generation failed on the backend.")

    default_prompt = "Describe this in detail. If it's a video, describe the sequence of events."
    return {
        "description": result_text,
        "prompt_used": text if text else default_prompt,
        "file_type_processed": file_type
    }
