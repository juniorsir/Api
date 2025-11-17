from fastapi import FastAPI, File, UploadFile
from comfy_client import describe_image
import tempfile

app = FastAPI()


@app.post("/describe_image")
async def api_describe_image(file: UploadFile = File(...)):
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result_text = describe_image(tmp_path)

    if not result_text:
        return {"error": "Generation failed"}

    return {"description": result_text}
