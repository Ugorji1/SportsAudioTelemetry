import os
import sys
import re
import json
import time
import subprocess
import urllib.request
from datetime import datetime, timezone

def resolve_mixlr_stream(url: str) -> str:
    """Resolves Mixlr channel URLs directly to live progressive stream audio endpoints."""
    match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9_-]+)\.mixlr\.com', url)
    if not match:
        match = re.search(r'https?://(?:www\.)?mixlr\.com/([a-zA-Z0-9_-]+)', url)
        
    if match:
        raw_slug = match.group(1)
        slugs_to_try = [raw_slug, raw_slug.replace('-', '')]
        
        for slug in slugs_to_try:
            api_url = f"https://apicdn.mixlr.com/v3/channel_view/{slug}"
            try:
                req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    for inc in data.get('included', []):
                        if inc.get('type') == 'broadcast':
                            stream_url = inc['attributes'].get('progressive_stream_url')
                            b_title = inc['attributes'].get('title', '')
                            if stream_url:
                                print(f"[Mixlr Live Detected] Broadcast: '{b_title}' -> {stream_url}")
                                return stream_url
            except Exception as e:
                pass
    return url

def resolve_stream_url(url: str) -> str:
    if "mixlr.com" in url:
        return resolve_mixlr_stream(url)

    if "youtube.com" in url or "youtu.be" in url or "twitch.tv" in url:
        print(f"[*] Resolving video stream endpoint via yt-dlp: {url}")
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'mweb']}}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if direct_url:
                    return direct_url
        except Exception as e:
            print(f"[!] Stream resolver note: {e}")
            return url
    return url

def test_stream(raw_url: str):
    stream_url = resolve_stream_url(raw_url)
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]}] Testing connection to stream: {stream_url}")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-reconnect", "1",
        "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "2",
        "-i", stream_url,
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        "-"
    ]

    try:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        start_time = time.time()
        total_bytes = 0
        chunks_received = 0
        
        print("[*] Waiting for initial audio packet stream...")
        
        while chunks_received < 10:
            chunk = process.stdout.read(4000)
            if not chunk:
                break
            
            if chunks_received == 0:
                first_byte_latency = (time.time() - start_time) * 1000
                print(f"[OK] First audio chunk received in {first_byte_latency:.1f}ms!")
            
            total_bytes += len(chunk)
            chunks_received += 1
            time.sleep(0.05)
            
        process.terminate()
        if chunks_received > 0:
            print(f"[SUCCESS] Stream is healthy. Received {total_bytes} bytes across {chunks_received} test chunks.")
        else:
            print(f"[ERROR] Stream returned 0 bytes. Check if the URL is valid or currently broadcasting.")
        
    except FileNotFoundError:
        print("[ERROR] 'ffmpeg' not found on system PATH. Make sure FFmpeg is installed.")
    except Exception as e:
        print(f"[ERROR] Stream test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                target_url = cfg.get("matches", [{}])[0].get("stream_url", "")
        except Exception:
            target_url = ""

    if not target_url or target_url.startswith("http://example.com"):
        print("Usage: python stream_tester.py <STREAM_URL>")
    else:
        test_stream(target_url)
