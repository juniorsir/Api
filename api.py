from fastapi import FastAPI, File, UploadFile, Form
from comfy_client import describe_image
import tempfile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/describe_image")
async def api_describe_image(
    file: UploadFile = File(...),
    text: str = Form(None)  # <-- optional text support
):
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Use default text if user didn't send any
    result_text = describe_image(tmp_path, prompt_text=text)

    if not result_text:
        return {"error": "Generation failed"}

    return {
        "description": result_text,
        "prompt_used": text if text else "Default text"
    }

