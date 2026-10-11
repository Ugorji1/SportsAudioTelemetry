import os
import sys
import re
import json
import time
import math
import struct
import threading
import subprocess
import urllib.request
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

# Try importing modern faster-whisper first, with fallback to Vosk
HAS_WHISPER = False
WHISPER_LOAD_ERROR = None

# On Windows, ensure DLL search path includes ctranslate2 directories
if sys.platform == "win32":
    for path in sys.path:
        ct2_dir = os.path.join(path, "ctranslate2")
        if os.path.exists(ct2_dir) and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(ct2_dir)
            except Exception:
                pass

try:
    import numpy as np
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except (ImportError, OSError, Exception) as e:
    WHISPER_LOAD_ERROR = str(e)
    HAS_WHISPER = False

try:
    from vosk import Model, KaldiRecognizer
    HAS_VOSK = True
except (ImportError, OSError, Exception):
    HAS_VOSK = False

CONFIG_FILE = "config.json"
LOG_FILE = "telemetry.log"
TELEMETRY_PORT = 8765

log_lock = threading.Lock()
telemetry_state_lock = threading.Lock()

recent_audio_triggers = []
recent_sporty_locks = []

REJECTION_TOKENS = [
    "off the post",
    "wide",
    "side netting",
    "great save",
    "denied by",
    "flag is up",
    "offside",
    "over the bar",
    "penalty area",
    "penalty box",
    "penalty spot",
    "goal keeper",
    "goalkeeper",
    "goal kick",
    "goalline",
    "goal line",
    "first half goal",
    "previous goal",
    "goal difference"
]

SCORELINE_TOKENS = [
    "one nil", "two nil", "three nil", "four nil",
    "one one", "two one", "three one", "four one",
    "two two", "three two", "four two",
    "three three", "equalizer", "equaliser", "takes the lead"
]

def get_ffmpeg_executable() -> str:
    local_ffmpeg = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    if os.path.exists("ffmpeg.exe"):
        return os.path.abspath("ffmpeg.exe")
    return "ffmpeg"

def calculate_rms_volume(pcm_data: bytes) -> float:
    count = len(pcm_data) // 2
    if count == 0:
        return -100.0
    shorts = struct.unpack(f"{count}h", pcm_data)
    sum_squares = sum(s * s for s in shorts)
    rms = math.sqrt(sum_squares / count)
    if rms > 0:
        return 20 * math.log10(rms)
    return -100.0

def resolve_mixlr_stream(url: str) -> str:
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
            except Exception:
                pass
    return url

def resolve_stream_url(url: str) -> str:
    if "mixlr.com" in url:
        return resolve_mixlr_stream(url)

    if "youtube.com" in url or "youtu.be" in url or "twitch.tv" in url:
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
        except Exception:
            return url
    return url

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        return json.loads(content, strict=False)

def log_event(match_name: str, event_type: str, keyword: str, timestamp_str: str, latency_ms: float = 0.0):
    log_line = f"[{timestamp_str}] MATCH='{match_name}' | TYPE={event_type} | EVENT={keyword} | POST_LATENCY={latency_ms:.1f}ms\n"
    with log_lock:
        print(f"[*] {log_line.strip()}")
        with open(LOG_FILE, "a", encoding="utf-8") as lf:
            lf.write(log_line)

def send_telegram_alert(bot_token: str, chat_id: str, match_name: str, event_type: str, trigger_info: str, timestamp_str: str, snippet: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    text = (
        f"🚨 *HIGH-CONVICTION EVENT DETECTED*\n\n"
        f"⚽ *Match:* `{match_name}`\n"
        f"• *Event:* `{event_type.upper()}`\n"
        f"• *Trigger Detail:* `{trigger_info}`\n"
        f"• *Timestamp (UTC):* `{timestamp_str}`\n"
        f"• *Transcript Snippet:* `\"{snippet}\"`\n"
        f"• *Status:* `CONFIRMED_SIGNAL`"
    )
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=2.5)
        post_lat = (time.time() - start_time) * 1000
        if response.status_code == 200:
            log_event(match_name, "TELEGRAM_SUCCESS", event_type, timestamp_str, post_lat)
        else:
            log_event(match_name, "TELEGRAM_FAILED", f"HTTP {response.status_code}", timestamp_str, post_lat)
    except Exception as e:
        post_lat = (time.time() - start_time) * 1000
        log_event(match_name, "TELEGRAM_ERROR", str(e), timestamp_str, post_lat)

def send_telegram_delta_report(bot_token: str, chat_id: str, match_name: str, delta_ms: float, audio_ts: str, sporty_ts: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    if delta_ms > 0:
        headline = "🟢 *LATENCY ADVANTAGE CONFIRMED (FASTER THAN SPORTYBET)*"
        edge_text = f"⚡ *You were {delta_ms:.0f} ms ({delta_ms/1000:.2f}s) FASTER than SportyBet's lock!*"
    else:
        headline = "🔴 *LATENCY DEFICIT (SPORTYBET WAS FASTER)*"
        edge_text = f"⏱ *SportyBet locked {-delta_ms:.0f} ms ({-delta_ms/1000:.2f}s) before audio arrival.*"

    text = (
        f"{headline}\n\n"
        f"⚽ *Match:* `{match_name}`\n"
        f"{edge_text}\n\n"
        f"• *Audio Trigger (UTC):* `{audio_ts}`\n"
        f"• *SportyBet Lock (UTC):* `{sporty_ts}`\n"
        f"• *Computed ΔL:* `{delta_ms:+.1f} ms`"
    )
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=2.5)
    except Exception:
        pass

# -------------------------------------------------------------
# Local Telemetry Receiver for SportyBet Browser Lock Hook
# -------------------------------------------------------------
class SportyBetTelemetryHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

        try:
            payload = json.loads(post_data.decode('utf-8'))
            sporty_epoch = payload.get('client_timestamp_ms', time.time() * 1000) / 1000.0
            sporty_utc = payload.get('iso_utc', datetime.now(timezone.utc).isoformat())
            match_title = payload.get('match_title', 'SportyBet Match')
            detail = payload.get('detail', 'Market Lock')

            with telemetry_state_lock:
                recent_sporty_locks.append({
                    'timestamp_epoch': sporty_epoch,
                    'utc_str': sporty_utc,
                    'detail': detail,
                    'match_title': match_title
                })
                if len(recent_sporty_locks) > 10:
                    recent_sporty_locks.pop(0)

                matched_trigger = None
                for trig in reversed(recent_audio_triggers):
                    if abs(sporty_epoch - trig['timestamp_epoch']) <= 45.0:
                        matched_trigger = trig
                        break

            if matched_trigger:
                delta_sec = sporty_epoch - matched_trigger['timestamp_epoch']
                delta_ms = delta_sec * 1000.0

                with log_lock:
                    print("\n" + "="*65)
                    print(f"📊 [REAL-TIME TELEMETRY] ΔL LATENCY BENCHMARK REPORT")
                    print("="*65)
                    print(f"⚽ Match: '{matched_trigger['match_name']}'")
                    print(f"• Audio Trigger:    {matched_trigger['utc_str']} UTC ({matched_trigger['event_type']})")
                    print(f"• SportyBet Lock:   {sporty_utc} UTC ({detail})")
                    if delta_ms > 0:
                        print(f"🟢 RESULT: YOU WERE +{delta_ms:.0f} ms ({delta_ms/1000:.2f}s) FASTER THAN SPORTYBET! ⚡")
                    else:
                        print(f"🔴 RESULT: SPORTYBET WAS {-delta_ms:.0f} ms ({-delta_ms/1000:.2f}s) FASTER THAN AUDIO.")
                    print("="*65 + "\n")

                cfg = load_config()
                telegram_cfg = cfg.get("telegram", {})
                if telegram_cfg.get("enabled", True):
                    send_telegram_delta_report(
                        telegram_cfg.get("bot_token"),
                        telegram_cfg.get("chat_id"),
                        matched_trigger['match_name'],
                        delta_ms,
                        matched_trigger['utc_str'],
                        sporty_utc
                    )
            else:
                with log_lock:
                    print(f"\n🔒 [SPORTYBET LOCK LOGGED] at {sporty_utc} UTC | Waiting for matching audio event...")

        except Exception as e:
            print(f"[Telemetry Server Error]: {e}")

    def log_message(self, format, *args):
        return

def start_telemetry_receiver():
    server = HTTPServer(('127.0.0.1', TELEMETRY_PORT), SportyBetTelemetryHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[*] SportyBet Zero-Latency Telemetry Hook Receiver: RUNNING on http://127.0.0.1:{TELEMETRY_PORT}")

# -------------------------------------------------------------
# Real-Time Context & Scoring Engine
# -------------------------------------------------------------
def is_valid_sports_trigger(text: str, kw: str) -> bool:
    for reject in REJECTION_TOKENS:
        if reject in text:
            if any(sc in text for sc in SCORELINE_TOKENS) or any(act in text for act in ["scores", "penalty given", "points to the spot", "in the net"]):
                return True
            return False
    return True

def match_worker(match_cfg: dict, shared_model, global_keywords: list, audio_settings: dict, telegram_cfg: dict):
    match_name = match_cfg.get("name", "Unknown Match")
    raw_stream_url = match_cfg.get("stream_url")
    custom_keywords = match_cfg.get("custom_keywords", [])
    
    all_keywords = list(set([kw.lower() for kw in (global_keywords + custom_keywords)]))
    
    sample_rate = audio_settings.get("sample_rate", 16000)
    chunk_size = audio_settings.get("chunk_size", 4000)
    debounce_secs = audio_settings.get("debounce_seconds", 4.0)

    bot_token = telegram_cfg.get("bot_token")
    chat_id = telegram_cfg.get("chat_id")
    telegram_enabled = telegram_cfg.get("enabled", True) and bot_token != "YOUR_TELEGRAM_BOT_TOKEN"

    # Set up Vosk recognizer if running in Vosk mode
    vosk_recognizer = None
    if not HAS_WHISPER and HAS_VOSK and shared_model is not None:
        vosk_recognizer = KaldiRecognizer(shared_model, sample_rate)
        vosk_recognizer.SetWords(True)

    stream_url = resolve_stream_url(raw_stream_url)
    ffmpeg_bin = get_ffmpeg_executable()

    print(f"[{match_name}] Connecting to stream endpoint: {stream_url}")

    # FFmpeg Dynamic Audio Compressor + De-Clipper Filter
    # - compand: smooths scream peaks and prevents digital clipping
    # - alimiter: hard-limits volume to prevent waveform blowout
    ffmpeg_cmd = [
        ffmpeg_bin,
        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-reconnect", "1",
        "-reconnect_at_eof", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "2",
        "-i", stream_url,
        "-af", "compand=attacks=0.02:decays=0.2:points=-80/-80|-45/-30|-20/-15|0/-5:gain=3,alimiter=level_in=1:level_out=0.9:limit=0.95:attack=5:release=50",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", str(sample_rate),
        "-"
    ]

    try:
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"[ERROR] FFmpeg not found for [{match_name}].")
        return

    last_triggers = {}
    rolling_db = 60.0
    surge_accumulator = 0.0
    
    # Audio buffer for faster-whisper (accumulates 1.0s of audio)
    whisper_audio_buffer = bytearray()
    whisper_chunk_target = sample_rate * 2 * 1.2  # 1.2 seconds of 16-bit PCM

    while True:
        try:
            data = process.stdout.read(chunk_size)
            if not data or len(data) == 0:
                time.sleep(2)
                stream_url = resolve_stream_url(raw_stream_url)
                ffmpeg_cmd[8] = stream_url
                process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                continue

            now_ts = time.time()
            utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            # 1. Real-time Acoustic Energy Tracking
            current_db = calculate_rms_volume(data)
            rolling_db = (rolling_db * 0.96) + (current_db * 0.04)

            # Adaptive Dynamic Surge (+11 dB above baseline)
            if current_db > (rolling_db + 11.0):
                surge_accumulator += 0.25
                if surge_accumulator >= 0.5:
                    last_spike = last_triggers.get("ACOUSTIC_SPIKE", 0)
                    if now_ts - last_spike >= debounce_secs:
                        last_triggers["ACOUSTIC_SPIKE"] = now_ts
                        surge_accumulator = 0.0
                        
                        with telemetry_state_lock:
                            recent_audio_triggers.append({
                                'match_name': match_name,
                                'timestamp_epoch': now_ts,
                                'utc_str': utc_str,
                                'event_type': 'ACOUSTIC_CROWD_SURGE'
                            })
                            if len(recent_audio_triggers) > 10:
                                recent_audio_triggers.pop(0)

                        with log_lock:
                            print(f"\n⚡ [{match_name}] ACOUSTIC SURGE DETECTED ({current_db:.1f} dB vs {rolling_db:.1f} dB baseline, +{current_db-rolling_db:.1f}dB) at {utc_str} UTC")
                        
                        if telegram_enabled:
                            threading.Thread(
                                target=send_telegram_alert,
                                args=(bot_token, chat_id, match_name, "ACOUSTIC_CROWD_SURGE", f"+{current_db - rolling_db:.1f} dB Volume Spike", utc_str, "Acoustic roar/yelling surge detected"),
                                daemon=True
                            ).start()
            else:
                surge_accumulator = max(0.0, surge_accumulator - 0.15)

            # 2. Speech Recognition (faster-whisper or Vosk fallback)
            text_to_check = ""

            if HAS_WHISPER and shared_model is not None:
                whisper_audio_buffer.extend(data)
                # Transcribe every 1.2s of audio or immediately on acoustic surge
                if len(whisper_audio_buffer) >= whisper_chunk_target or (surge_accumulator >= 0.4 and len(whisper_audio_buffer) >= sample_rate):
                    # Convert PCM bytes to float32 numpy array
                    audio_np = np.frombuffer(whisper_audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
                    whisper_audio_buffer.clear()
                    try:
                        segments, _ = shared_model.transcribe(
                            audio_np,
                            language="en",
                            beam_size=1,
                            condition_on_previous_text=False
                        )
                        text_to_check = " ".join([seg.text for seg in segments]).strip().lower()
                    except Exception:
                        pass
            elif vosk_recognizer is not None:
                if vosk_recognizer.AcceptWaveform(data):
                    res = json.loads(vosk_recognizer.Result())
                    text_to_check = res.get("text", "").lower()
                else:
                    pres = json.loads(vosk_recognizer.PartialResult())
                    text_to_check = pres.get("partial", "").lower()

            if text_to_check:
                # Check scoreline delta
                matched_score = None
                for sc in SCORELINE_TOKENS:
                    if sc in text_to_check:
                        matched_score = sc
                        break

                # Check match keywords
                matched_kw = None
                for kw in all_keywords:
                    if kw in text_to_check:
                        if is_valid_sports_trigger(text_to_check, kw):
                            matched_kw = kw
                            break

                trigger_event = matched_score or matched_kw

                if trigger_event:
                    last_t = last_triggers.get(trigger_event, 0)
                    if now_ts - last_t >= debounce_secs:
                        last_triggers[trigger_event] = now_ts
                        
                        with telemetry_state_lock:
                            recent_audio_triggers.append({
                                'match_name': match_name,
                                'timestamp_epoch': now_ts,
                                'utc_str': utc_str,
                                'event_type': trigger_event
                            })
                            if len(recent_audio_triggers) > 10:
                                recent_audio_triggers.pop(0)

                        with log_lock:
                            print(f"\n🚨 [{match_name}] MATCH TRIGGER: '{trigger_event.upper()}' at {utc_str} UTC | Heard: '{text_to_check}'")
                        
                        if telegram_enabled:
                            threading.Thread(
                                target=send_telegram_alert,
                                args=(bot_token, chat_id, match_name, trigger_event, "Match Keyword Trigger", utc_str, text_to_check),
                                daemon=True
                            ).start()

                        if vosk_recognizer:
                            vosk_recognizer.Reset()

        except Exception as e:
            print(f"[{match_name}] Loop error: {e}")
            time.sleep(0.5)

def run_multi_monitor():
    cfg = load_config()
    telegram_cfg = cfg.get("telegram", {})
    global_keywords = cfg.get("global_keywords", [])
    audio_settings = cfg.get("audio_settings", {})
    matches = cfg.get("matches", [])

    active_matches = [m for m in matches if m.get("enabled", True)]
    
    if not active_matches:
        print("[ERROR] No active matches enabled in config.json. Set 'enabled': true for at least one match.")
        sys.exit(1)

    shared_model = None

    if HAS_WHISPER:
        print("[*] Initializing Modern faster-whisper Engine (tiny.en quantized INT8)...")
        shared_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        print("[*] faster-whisper Model loaded into RAM successfully! ⚡")
    elif HAS_VOSK:
        if WHISPER_LOAD_ERROR:
            print("[*] faster-whisper C++ runtime missing (Run install_vcredist.bat to enable).")
            print("[*] Falling back to Vosk + FFmpeg Dynamic Audio Compressor...")
        model_path = cfg.get("model_path", "models/vosk-model-small-en-us-0.15")
        if not os.path.exists(model_path):
            print(f"[!] Vosk model not found at '{model_path}'. Running setup_model.py...")
            from setup_model import download_and_extract_model
            download_and_extract_model()
        print(f"[*] Initializing Shared Vosk STT Model into RAM: {model_path}")
        shared_model = Model(model_path)
    else:
        print("[ERROR] Neither faster-whisper nor Vosk is installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    print("\n=================================================================")
    print(f"   QUANTITATIVE SPORTS TELEMETRY & ΔL BENCHMARK ENGINE  ")
    print(f"   ASR Engine: {'faster-whisper (Tiny.en INT8)' if HAS_WHISPER else 'Vosk (Kaldi)'}")
    print("=================================================================\n")

    start_telemetry_receiver()

    threads = []
    for match in active_matches:
        t = threading.Thread(
            target=match_worker,
            args=(match, shared_model, global_keywords, audio_settings, telegram_cfg),
            daemon=True
        )
        t.start()
        threads.append(t)
        time.sleep(0.2)

    print(f"[*] All {len(active_matches)} match channels are live and listening concurrently!")
    print("[*] FFmpeg Dynamic Audio Compressor + De-Clipper: ACTIVE")
    print("[*] Adaptive Acoustic Surge Detector: ACTIVE (+11.0 dB)")
    print("[*] Scoreline Delta & Match Keyword Scorer: ACTIVE\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping all audio channels...")

if __name__ == "__main__":
    run_multi_monitor()
