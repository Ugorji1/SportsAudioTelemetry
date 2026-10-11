# ⚡ CourtSide: Real-Time Sports Audio Telemetry & AI Acoustic Surge Monitor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![ASR: faster--whisper](https://img.shields.io/badge/ASR-faster--whisper%20%7C%20Vosk-orange.svg)](https://github.com/SYSTRAN/faster-whisper)
[![Detection Latency](https://img.shields.io/badge/Surge%20Latency-%3C50ms-red.svg)]()
[![Target: SportyBet & Exchanges](https://img.shields.io/badge/Target-SportyBet%20%7C%20Prediction%20Markets-purple.svg)]()

> **Beat in-play sports betting market freezes by 1.5 – 3.0 seconds.**  
> A high-frequency audio telemetry engine that ingests direct stadium press-box feeds, detects explosive crowd/commentator acoustic surges in **<50ms**, and transcribes speech using dynamic audio compressors and neural speech models (`faster-whisper` / `Vosk`).

---

## 🎯 The Core Thesis: Latency Arbitrage ($\Delta L$)

In live in-play sports betting and prediction markets, bookmakers rely on in-stadium human scouts (or secondary optical trackers) to press a handheld button that suspends odds when a goal, penalty, or red card occurs.

$$\Delta L = (L_{\text{scout\_to\_bookmaker}} + T_{\text{suspension}}) - (L_{\text{audio\_stream}} + T_{\text{detection}} + T_{\text{execution}})$$

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LATENCY HIERARCHY COMPARISON                    │
├────────────────────────────────────────┬───────────────────────────────┤
│ Consumer Video / TV / YouTube          │ 45.0s – 120.0s (Too Slow ❌)  │
│ Commercial Radio Web Player (HLS/DASH) │ 15.0s – 30.0s (Too Slow ❌)  │
│ In-Stadium Scout on SportyBet          │ 2.5s – 5.0s (Handheld delay)  │
│ COURTSIDE DIRECT AUDIO + RMS SURGE     │ 1.0s – 2.5s (YOUR EDGE ⚡)     │
└────────────────────────────────────────┴───────────────────────────────┘
```

When you listen to television or standard web streams, you are **at least 30 to 120 seconds behind real life**. But direct touchline feeds (Mixlr press-box uplinks and direct BBC IP relays) operate with only **1.0 to 2.5 seconds** of transport delay.

**CourtSide exploits this asymmetry:** by detecting the acoustic explosion of a goal or penalty in `<50ms`, you receive the signal **before the bookmaker locks the market**.

---

## ⚡ Key Features

* **Instant Acoustic Decibel Spike Detection ($<50\text{ms}$):** Real-time Root-Mean-Square (RMS) audio energy tracker. The millisecond the commentator screams or the stadium crowd roars ($>+11\text{dB}$ surge), it fires an instant trigger before speech transcription even finishes.
* **FFmpeg Dynamic Audio Compressor & De-Clipper:** When commentators scream into headsets, raw audio clips and distorts. CourtSide passes the audio through lookahead dynamic limiters (`compand` & `alimiter`) so the voice stays crisp and decipherable.
* **Modern Transformer ASR (`faster-whisper` with Vosk fallback):** Uses quantized INT8 `faster-whisper-tiny` running in ~40ms on CPU, trained on noisy sports commentary and regional accents.
* **Zero-Latency SportyBet Browser Hook (`sportybet_telemetry_hook.js`):** Client-side Tampermonkey script that detects when odds buttons turn gray / lock in your browser and automatically computes $\Delta L$ down to the millisecond.
* **Negative Rejection & Scoreline Delta Scoring:** Automatically cancels false alarms (*"wide"*, *"off the post"*, *"penalty area"*) and mathematically validates goals via spoken scoreline changes (*"two nil"*, *"three one"*).
* **Multi-Match Concurrency:** Monitors 3 to 5 matches simultaneously in parallel background threads sharing a single model in RAM.
* **Telegram Sub-200ms Dispatch:** Direct markdown notifications pushed straight to your phone.

---

## 🏗️ System Architecture

```
                       [ Live Touchline / Mixlr / BBC Stream ]
                                          │
                                          ▼
                      [ FFmpeg Dynamic Range Compressor / AGC ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [ RMS Audio Energy Surge ]                       [ Neural ASR Transcriber ]
    • Detects volume jump (+11dB)                   • faster-whisper / Vosk
    • Triggers in < 50ms ⚡                          • Context & Scoreline Delta
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                              [ Finite State Scorer ]
                             (Filters near-miss groans)
                                          │
                                          ▼
                         [ Sub-200ms Telegram Dispatch ]
                                          ▲
                                          │ (Local POST ping)
                      [ SportyBet Browser Hook (Tampermonkey) ]
```

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.10+
* Windows 10/11 / Windows Server VPS (or Linux/macOS)
* [FFmpeg](https://ffmpeg.org/download.html) (Windows installer will fetch automatically if missing)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/CourtSide-Audio.git
cd CourtSide-Audio

# Windows: 1-click install
install.bat

# Or manual install via pip:
python -m venv venv
# Windows: venv\Scripts\activate | Linux: source venv/bin/activate
pip install -r requirements.txt
```

*(Note for Windows VPS users: if `faster-whisper` asks for C++ dependencies, double-click `install_vcredist.bat` to install the official Microsoft Visual C++ runtime in 30 seconds).*

### 2. Configuration

Copy `config.example.json` to `config.json` and configure your Telegram bot credentials and match targets:

```json
{
  "telegram": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID",
    "enabled": true
  },
  "audio_settings": {
    "sample_rate": 16000,
    "chunk_size": 4000,
    "debounce_seconds": 4.0
  },
  "matches": [
    {
      "id": "match_1",
      "name": "Live Matchday Commentary",
      "enabled": true,
      "stream_url": "https://sports-live95.mixlr.com/",
      "custom_keywords": ["penalty", "goal"]
    }
  ]
}
```

### 3. Run the Telemetry Monitor

```bash
# Windows
run.bat

# Linux / Mac
python monitor.py
```

---

## 📊 Live $\Delta L$ Benchmarking (SportyBet Setup)

To measure the exact millisecond time advantage over the bookmaker:

1. Open your match on **SportyBet** in Chrome or Edge.
2. Install the **Tampermonkey** extension and paste the contents of [`sportybet_telemetry_hook.js`](sportybet_telemetry_hook.js) *(or paste directly into your browser DevTools Console)*.
3. When a goal is scored and the market freezes, your terminal and Telegram will output:

```
=================================================================
📊 [REAL-TIME TELEMETRY] ΔL LATENCY BENCHMARK REPORT
=================================================================
⚽ Match: 'Torquay United vs Folkestone'
• Audio Trigger:    2026-10-11 19:42:10.120 UTC (ACOUSTIC_CROWD_SURGE)
• SportyBet Lock:   2026-10-11 19:42:12.350 UTC (Market Lock)
🟢 RESULT: YOU WERE +2,230 ms (2.23s) FASTER THAN SPORTYBET! ⚡
=================================================================
```

---

## 📻 Verified Stream Endpoints

See the comprehensive **[Master Stream Catalog](Master_Catalog_Sports_Audio_Streams.md)** (available in Markdown, HTML, and PDF) for 100% verified, active direct stream endpoints covering:
* **UK National League & North/South** (BBC Radio London, BBC Essex, BBC Manchester, BBC Solent, etc.)
* **League of Ireland** (Live 95 Sport, LMFM Sport, Radio Kerry, Highland Radio)
* **Scottish Lower Leagues** (BBC Radio Scotland FM/MW)
* **South African PSL & Motsepe Foundation Championship** (Ukhozi FM, Thobela FM, Lesedi FM)

---

## ⚠️ Disclaimer

This software is developed strictly for **educational, quantitative research, and latency benchmarking purposes**. Users are responsible for complying with the terms of service of all broadcast providers and betting platforms. The authors accept no liability for financial decisions made using this software.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
