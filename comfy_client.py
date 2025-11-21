import requests
import uuid
import time
import json
import os

# Ensure APP_URL is defined, pointing to your ComfyUI instance
APP_URL = "https://6mecpjpojj3wov-8188.proxy.runpod.net" 

# --- Helper functions for ComfyUI API interaction ---

def upload_file(file_path):
    """
    Uploads a file (image or video) to the ComfyUI server.
    ComfyUI's /upload/image endpoint can handle various file types.
    """
    url = f"{APP_URL}/upload/image"
    try:
        with open(file_path, "rb") as f:
            filename = os.path.basename(file_path)
            # The key 'image' is used by ComfyUI's API for file uploads in general
            files = {"image": (filename, f)}
            response = requests.post(url, files=files)
            response.raise_for_status() # Raises an exception for bad status codes
            data = response.json()
            # The 'name' is the filename ComfyUI uses internally
            return data.get("name")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def submit_workflow(workflow):
    """Submits a workflow prompt to the ComfyUI server."""
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": client_id}
    try:
        response = requests.post(f"{APP_URL}/prompt", json=payload)
        response.raise_for_status()
        return response.json().get("prompt_id")
    except Exception as e:
        print(f"Error submitting workflow: {e}")
        return None

def wait_for_result(prompt_id):
    """Waits for the workflow execution to complete and retrieves the result."""
    while True:
        time.sleep(2)
        try:
            response = requests.get(f"{APP_URL}/history/{prompt_id}")
            response.raise_for_status()
            data = response.json()

            if prompt_id not in data:
                continue

            execution = data[prompt_id]
            status = execution.get("status", {})

            if status.get("completed"):
                return execution
            if "error" in status or status.get("success") is False:
                print(f"Execution failed for prompt {prompt_id}")
                return None
        except Exception as e:
            print(f"Error checking history: {e}")
            time.sleep(5) # Wait longer on error

def extract_text(result_json):
    """Extracts the output text from the result JSON."""
    try:
        # The output text comes from the 'DisplayText' node, which is ID '17'
        return result_json["outputs"]["17"]["text"][0][0]
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error extracting text from result: {e}")
        return None

def create_workflow_from_template(template_path, file_name, file_type, prompt_text):
    """
    Loads a workflow template from a JSON file and configures it for the specific job.
    """
    with open(template_path, 'r') as f:
        workflow = json.load(f)

    # Set the user's prompt in the VQA node (14)
    workflow["14"]["inputs"]["text"] = prompt_text

    # The key is to correctly configure the MultiplePathsInput node (22)
    # It will only have one input, either from the image loader or video loader.
    workflow["22"]["inputs"]["inputcount"] = 1

    if file_type == 'image':
        # Use ImageLoader (node 13)
        workflow["13"]["inputs"]["image"] = file_name
        # Connect MultiplePathsInput (22) to the output of ImageLoader (13)
        workflow["22"]["inputs"]["path_1"] = ["13", 2]
        # Clean up the unused path input
        if "path_2" in workflow["22"]["inputs"]:
            del workflow["22"]["inputs"]["path_2"]

    elif file_type == 'video':
        # Use VideoLoader (node 18)
        workflow["18"]["inputs"]["file"] = file_name
        # Connect MultiplePathsInput (22) to the output of VideoLoader (18)
        workflow["22"]["inputs"]["path_1"] = ["18", 1]
        # Clean up the unused path input
        if "path_2" in workflow["22"]["inputs"]:
            del workflow["22"]["inputs"]["path_2"]
    else:
        raise ValueError("Unsupported file type specified.")

    return workflow


# --- Public function ---

def describe_media(file_path, file_type, prompt_text=None):
    """
    Uploads an image or video, runs the VQA workflow, and returns the description.
    
    Args:
        file_path (str): The local path to the image or video file.
        file_type (str): Either 'image' or 'video'.
        prompt_text (str, optional): The prompt for the VQA model.
    """
    # 1. Upload the media file to ComfyUI
    uploaded_filename = upload_file(file_path)
    if not uploaded_filename:
        print("File upload failed.")
        return None

    # 2. Use a default prompt if none is provided
    if not prompt_text:
       prompt_text = "Describe this in detail. If it's a video, describe the sequence of events."

    # 3. Create the workflow from the JSON template
    try:
        workflow = create_workflow_from_template(
            template_path="Ivtop.json",
            file_name=uploaded_filename,
            file_type=file_type,
            prompt_text=prompt_text
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error creating workflow: {e}")
        return None
    
    # 4. Submit the workflow
    prompt_id = submit_workflow(workflow)
    if not prompt_id:
        print("Workflow submission failed.")
        return None
    print(f"Workflow submitted with prompt_id: {prompt_id}")

    # 5. Wait for the result
    result = wait_for_result(prompt_id)
    if not result:
        print("Failed to get result.")
        return None

    # 6. Extract and return the text
    return extract_text(result)
