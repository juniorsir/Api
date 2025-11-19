import requests
import uuid
import time
import json
import os
import asyncio
import json
import websockets

APP_URL = "https://6mecpjpojj3wov-8188.proxy.runpod.net"

# -----------------------------
# Upload image to ComfyUI
# -----------------------------
def upload_image(file_path):
    url = f"{APP_URL}/upload/image"

    with open(file_path, "rb") as f:
        filename = os.path.basename(file_path)

        files = {"image": (filename, f, "image/jpeg")}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        return response.json().get("name")
    return None

class ComfyClient:
    def __init__(self):
        self.app_url = APP_URL
        self.ws_url = APP_URL.replace("http", "ws") + "/ws?clientId=api"

    # ------------------------
    # Upload Image to ComfyUI
    # ------------------------
    def upload_image(self, path):
        files = {"image": open(path, "rb")}
        response = requests.post(self.app_url + "/upload/image", files=files)
        return response.json()

    # ------------------------
    # Submit Workflow Prompt
    # ------------------------
    def send_prompt(self, workflow):
        res = requests.post(self.app_url + "/prompt", json=workflow)
        return res.json()["prompt_id"]

    # ------------------------
    # Track Progress (WebSocket)
    # ------------------------
    async def track_progress(self, prompt_id, callback):
        async with websockets.connect(self.ws_url) as ws:
            async for msg in ws:
                data = json.loads(msg)

                if data.get("type") == "progress":
                    v = data["data"]["value"]
                    m = data["data"]["max"]
                    percent = int((v / m) * 100)
                    callback(percent)

                if data.get("type") == "executed" and data["data"]["prompt_id"] == prompt_id:
                    callback(100)
                    break

# -----------------------------
# Build workflow
# -----------------------------
def create_workflow(image_name, prompt_text):
    
    return {
        "13": {
            "inputs": {"image": image_name},
            "class_type": "ImageLoader",
            "_meta": {"title": "Load Image Advanced"},
        },

        "14": {
            "inputs": {
                "text": prompt_text,
                "model": "Qwen3-VL-4B-Instruct",
                "quantization": "none",
                "keep_model_loaded": False,
                "temperature": 0.7,
                "max_new_tokens": 2048,
                "min_pixels": 200704,
                "max_pixels": 1003520,
                "seed": 616,
                "attention": "eager",
                "source_path": ["15", 0],
            },
            "class_type": "Qwen3_VQA",
            "_meta": {"title": "Qwen3 VQA"},
        },

        "15": {
            "inputs": {
                "inputcount": 1,
                "sample_fps": 1,
                "max_frames": 2,
                "use_total_frames": True,
                "use_original_fps_as_sample_fps": True,
                "Update inputs": None,
                "path_1": ["13", 2],
            },
            "class_type": "MultiplePathsInput",
            "_meta": {"title": "Multiple Paths Input"},
        },

        "17": {
            "inputs": {"text": ["14", 0]},
            "class_type": "DisplayText",
            "_meta": {"title": "Display Text"},
        },
    }


# -----------------------------
# Submit workflow
# -----------------------------
def submit_workflow(workflow):
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": client_id}

    response = requests.post(f"{APP_URL}/prompt", json=payload)

    if response.status_code != 200:
        return None

    return response.json().get("prompt_id")


# -----------------------------
# Wait for result
# -----------------------------
def wait_for_result(prompt_id):
    while True:
        time.sleep(2)
        response = requests.get(f"{APP_URL}/history/{prompt_id}")

        if response.status_code != 200:
            continue

        data = response.json()

        if prompt_id not in data:
            continue

        execution = data[prompt_id]

        if execution.get("status", {}).get("completed"):
            return execution

        if "error" in execution.get("status", {}):
            return None


# -----------------------------
# Extract output text
# -----------------------------
def extract_text(result_json):
    try:
        return result_json["outputs"]["17"]["text"][0][0]
    except:
        return None


# -----------------------------
# Public function
# -----------------------------
def describe_image(file_path, prompt_text=None):
    image_name = upload_image(file_path)
    if not image_name:
        return None

    if not prompt_text:
       prompt_text = "Describe this image in details."

    workflow = create_workflow(image_name, prompt_text)
    prompt_id = submit_workflow(workflow)

    if not prompt_id:
        return None

    result = wait_for_result(prompt_id)
    if not result:
        return None

    return extract_text(result)
