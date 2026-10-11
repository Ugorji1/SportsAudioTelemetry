import os
import sys
import zipfile
import urllib.request
import shutil

FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
TARGET_EXE = "ffmpeg.exe"

def download_ffmpeg():
    if os.path.exists(TARGET_EXE):
        print(f"[OK] ffmpeg.exe already exists in project folder.")
        return

    print(f"[*] Downloading standalone FFmpeg for Windows from: {FFMPEG_ZIP_URL}")
    print("This may take 1-3 minutes (~80MB)...")
    
    zip_path = "ffmpeg_temp.zip"
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
            sys.stdout.flush()

    try:
        req = urllib.request.Request(FFMPEG_ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_file:
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            block_size = 65536
            while True:
                buffer = resp.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if total_size > 0:
                    percent = downloaded * 100 / total_size
                    sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
                    sys.stdout.flush()
        
        print("\n[*] Download complete. Extracting ffmpeg.exe...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe"):
                    with zip_ref.open(member) as source, open(TARGET_EXE, "wb") as target:
                        shutil.copyfileobj(source, target)
                    print(f"[SUCCESS] ffmpeg.exe extracted directly to project folder!")
                    break
                    
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    except Exception as e:
        print(f"\n[ERROR] Failed to auto-download FFmpeg: {e}")
        print("Please download ffmpeg-release-essentials.zip manually from https://www.gyan.dev/ffmpeg/builds/ and place ffmpeg.exe in this folder.")

if __name__ == "__main__":
    download_ffmpeg()
