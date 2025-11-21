import requests
import uuid
import time
import json
import os
import logging

# --- Setup basic logging ---
# On a real server, this would be configured more formally.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure APP_URL is defined, pointing to your ComfyUI instance
APP_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8080") 
# Using an environment variable is better for deployment on Render.

# --- Helper functions for ComfyUI API interaction ---

def upload_file(file_path):
    """
    Uploads a file to ComfyUI. Returns the internal filename on success, None on failure.
    """
    url = f"{APP_URL}/upload/image"
    logging.info(f"Uploading file: {os.path.basename(file_path)} to {url}")
    try:
        with open(file_path, "rb") as f:
            files = {"image": (os.path.basename(file_path), f)}
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            filename = data.get("name")
            if not filename:
                logging.error("Upload API response did not contain a 'name' field.")
                return None
            logging.info(f"File uploaded successfully as: {filename}")
            return filename
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error during file upload: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during file upload: {e}")
        return None

def submit_workflow(workflow):
    """Submits a workflow. Returns prompt_id on success, None on failure."""
    url = f"{APP_URL}/prompt"
    logging.info("Submitting workflow to ComfyUI.")
    try:
        payload = {"prompt": workflow, "client_id": str(uuid.uuid4())}
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            logging.error(f"Submit API response did not contain a 'prompt_id'. Response: {data}")
            return None
        logging.info(f"Workflow submitted successfully. Prompt ID: {prompt_id}")
        return prompt_id
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error during workflow submission: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during workflow submission: {e}")
        return None

def wait_for_result(prompt_id):
    """Waits for completion. Returns the result JSON on success, None on failure."""
    url = f"{APP_URL}/history/{prompt_id}"
    logging.info(f"Waiting for result for prompt ID: {prompt_id}")
    # Set a timeout to avoid waiting forever
    start_time = time.time()
    timeout_seconds = 180 # 3 minutes

    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if prompt_id in data:
                execution = data[prompt_id]
                status = execution.get("status", {})
                if status.get("completed"):
                    logging.info(f"Execution completed for prompt {prompt_id}.")
                    return execution
                if "error" in status or status.get("success") is False:
                    logging.error(f"Execution failed for prompt {prompt_id}. Status: {status}")
                    return None
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while waiting for result: {e}")
            time.sleep(5) # Wait longer on network error before retrying
        except Exception as e:
            logging.error(f"An unexpected error occurred while waiting for result: {e}")
            return None
    
    logging.error(f"Timeout reached waiting for result for prompt ID: {prompt_id}")
    return None

def extract_text(result_json):
    """Extracts text from result. Returns the text on success, None on failure."""
    try:
        text = result_json["outputs"]["17"]["text"][0][0]
        logging.info("Successfully extracted text from result.")
        return text
    except (KeyError, IndexError, TypeError) as e:
        logging.error(f"Error extracting text from result JSON: {e}. Result data: {result_json}")
        return None

def create_workflow_from_template(template_path, file_name, file_type, prompt_text):
    """Loads and configures workflow. Returns workflow dict on success, None on failure."""
    try:
        with open(template_path, 'r') as f:
            workflow = json.load(f)
        
        workflow["14"]["inputs"]["text"] = prompt_text
        workflow["22"]["inputs"]["inputcount"] = 1
        
        if "path_2" in workflow["22"]["inputs"]:
            del workflow["22"]["inputs"]["path_2"] # Only use one path

        if file_type == 'image':
            workflow["13"]["inputs"]["image"] = file_name
            workflow["22"]["inputs"]["path_1"] = ["13", 2]
        elif file_type == 'video':
            workflow["18"]["inputs"]["file"] = file_name
            workflow["22"]["inputs"]["path_1"] = ["18", 1]
        
        return workflow
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to create workflow from template '{template_path}': {e}")
        return None

# --- Public function ---

def describe_media(file_path, file_type, prompt_text=None):
    """
    Main function to process media. Returns description string on success, None on failure.
    """
    uploaded_filename = upload_file(file_path)
    if not uploaded_filename:
        return None

    if not prompt_text:
       prompt_text = "Describe this in detail. If it's a video, describe the sequence of events."

    workflow = create_workflow_from_template(
        template_path="Ivtop.json",
        file_name=uploaded_filename,
        file_type=file_type,
        prompt_text=prompt_text
    )
    if not workflow:
        return None
    
    prompt_id = submit_workflow(workflow)
    if not prompt_id:
        return None

    result = wait_for_result(prompt_id)
    if not result:
        return None

    return extract_text(result)
