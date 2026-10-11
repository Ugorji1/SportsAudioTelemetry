import os
import sys
import zipfile
import urllib.request

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "models"
ZIP_NAME = "vosk-model-small-en-us-0.15.zip"
EXTRACTED_FOLDER_NAME = "vosk-model-small-en-us-0.15"

def download_and_extract_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    target_model_path = os.path.join(MODEL_DIR, EXTRACTED_FOLDER_NAME)
    
    if os.path.exists(target_model_path):
        print(f"[OK] Model already exists at: {target_model_path}")
        return

    zip_path = os.path.join(MODEL_DIR, ZIP_NAME)
    print(f"[*] Downloading Vosk model from: {MODEL_URL}")
    print("This may take 1-2 minutes depending on your connection (~40MB)...")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
            sys.stdout.flush()

    urllib.request.urlretrieve(MODEL_URL, zip_path, reporthook=report_progress)
    print("\n[*] Download complete. Extracting archive...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(MODEL_DIR)

    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"[SUCCESS] Model ready at: {target_model_path}")

if __name__ == "__main__":
    download_and_extract_model()
