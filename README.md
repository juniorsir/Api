# 🖼️ Img2txt-ComfyUI

<img align="right" width="120" src="https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/logo.svg">

**Img2txt-ComfyUI** is a Python project that integrates **image-to-text (img2txt)** functionality with ComfyUI workflows — enabling automatic generation of descriptive text captions from images. It includes API support and a lightweight client to interact with ComfyUI.

> This project is ideal for users who want to automate image captioning workflows or plug image understanding into ComfyUI-based AI pipelines. 1

---

## 🚀 Features

✔ Generate textual descriptions/captions from images  
✔ Designed to work with ComfyUI or custom Python workflows  
✔ Lightweight API server included (`api.py`)  
✔ Client utilities for interacting with the server (`comfy_client.py`)  
✔ Easy to install with `requirements.txt`

---

## 📂 Repository Structure

Img2txt-comfyui/ ├── api.py                # Main API server for img2txt requests ├── comfy_client.py       # Client module to talk with the ComfyUI backend ├── Ivtop.json            # Example config or workflow definition ├── requirements.txt      # Dependencies required to run ├── pycache/          # Python cache └── README.md             # Project documentation

---

## 🧠 What Is img2txt?

“Img2txt” refers to converting the content of an image into natural language text — often used to generate **captions**, **descriptions**, or **semantic summaries** of an image’s contents. This is typically powered by vision-language models like BLIP or Llava within a node-based workflow UI such as ComfyUI. 2

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/juniorsir/Img2txt-comfyui.git
cd Img2txt-comfyui
```
Create and activate a Python environment
```
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```
3. Install dependencies
```
pip install -r requirements.txt
```
##▶ Running the API Server
Start the API server which handles image-to-text requests:
```
python api.py
```
You should see something like:
```

Serving img2txt API on http://localhost:PORT
```
##Now your server is ready to accept image captioning requests!

🧩 Using the Client
In another script or interactive session, you can import and use the client interface to send images:
```
from comfy_client import Img2TxtClient

client = Img2TxtClient("http://localhost:PORT")

result = client.caption_image("path/to/image.jpg")
print("Caption:", result)
```
#Adjust host and endpoint based on your API server configuration.

🛠️ Configuration
The file Ivtop.json likely contains configuration or a ComfyUI workflow definition associated with this project. You can customize it (e.g., model names, workflows, prompt formats) based on your needs.
🧩 How It Works
API Server (api.py) receives image data.
Client Module (comfy_client.py) interacts with the server or directly with a local model.
Models (e.g., BLIP, Llava) process the image to generate text.
The generated caption/text is returned to the caller and can be used for downstream workflows within ComfyUI.
