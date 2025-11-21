from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from comfy_client import describe_media
import tempfile
import os
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configure logging for the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/describe_media")
async def api_describe_media(
    file: UploadFile = File(...),
    text: str = Form(None)
):
    # --- The Ultimate Safety Net ---
    try:
        # 1. Determine file type
        content_type = file.content_type
        if content_type.startswith("image/"):
            file_type = "image"
        elif content_type.startswith("video/"):
            file_type = "video"
        else:
            logger.warning(f"Unsupported file type uploaded: {content_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {content_type}. Please upload an image or video."
            )

        # 2. Save uploaded file to a temporary path
        tmp_path = None
        try:
            # Use a context manager to ensure the temp file is handled properly
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            logger.info(f"File saved to temporary path: {tmp_path}")
            
            # 3. Call the backend processing function
            result_text = describe_media(tmp_path, file_type, prompt_text=text)

        finally:
            # 4. Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.info(f"Cleaned up temporary file: {tmp_path}")

        # 5. Handle processing failure
        if result_text is None:
            logger.error("describe_media returned None, indicating a backend failure.")
            raise HTTPException(
                status_code=503, # 503 Service Unavailable is a good code for backend failure
                detail="The media processing service failed. This could be due to a timeout or an error in the backend. Please try again later."
            )

        # 6. Return success response
        default_prompt = "Describe this in detail. If it's a video, describe the sequence of events."
        return {
            "description": result_text,
            "prompt_used": text if text else default_prompt,
            "file_type_processed": file_type
        }

    except HTTPException as e:
        # Re-raise HTTPExceptions as they are intentional error responses
        raise e
    except Exception as e:
        # Catch ANY other unexpected error
        logger.critical(f"An unhandled exception occurred in /describe_media endpoint: {e}", exc_info=True)
        # Return a generic 500 error to the client
        raise HTTPException(
            status_code=500,
            detail="An unexpected internal server error occurred."
        )
