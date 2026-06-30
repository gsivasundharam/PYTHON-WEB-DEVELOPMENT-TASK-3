"""
Speech to Image Generation
Flask backend:
  1. Receives audio from browser (any language)
  2. Transcribes with Google Speech Recognition (via SpeechRecognition)
  3. Sends prompt to MonsterAPI txt2img
  4. Returns generated image URL to frontend
"""

import os
import time
import requests
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import base64

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
MONSTER_API_KEY = os.environ.get("MONSTER_API_KEY", "YOUR_MONSTER_API_KEY_HERE")
MONSTER_BASE    = "https://api.monsterapi.ai/v1"

HEADERS = {
    "Authorization": f"Bearer {MONSTER_API_KEY}",
    "Content-Type":  "application/json",
}

# ── Audio Transcription ───────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Convert audio bytes → text using Google Speech Recognition.
    Supports any language audio sent from the browser.
    """
    recognizer = sr.Recognizer()

    # Save to temp file and convert to WAV via pydub
    suffix = ".webm" if "webm" in mime_type else \
             ".mp4"  if "mp4"  in mime_type else \
             ".wav"  if "wav"  in mime_type else ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    tmp_wav_path = tmp_in_path.replace(suffix, "_conv.wav")

    try:
        # Convert to WAV (16kHz mono) — pydub handles all common formats
        audio_seg = AudioSegment.from_file(tmp_in_path)
        audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
        audio_seg.export(tmp_wav_path, format="wav")

        with sr.AudioFile(tmp_wav_path) as source:
            audio_data = recognizer.record(source)

        # language=None → auto-detect (Google chooses best language)
        text = recognizer.recognize_google(audio_data, language=None, show_all=False)
        return text

    except sr.UnknownValueError:
        raise ValueError("Could not understand the audio. Please speak clearly.")
    except sr.RequestError as e:
        raise ValueError(f"Speech recognition service error: {e}")
    finally:
        for p in [tmp_in_path, tmp_wav_path]:
            try:
                os.unlink(p)
            except Exception:
                pass


# ── MonsterAPI Image Generation ───────────────────────────────────────────────

def generate_image(prompt: str,
                   style: str = "photorealistic",
                   steps: int = 30,
                   guidance: float = 7.5) -> str:
    """
    Send prompt to MonsterAPI txt2img (Stable Diffusion).
    Returns the generated image URL.
    """
    style_modifiers = {
        "photorealistic": "photorealistic, ultra detailed, 8k, sharp focus, DSLR",
        "anime":          "anime style, vibrant colors, Studio Ghibli, detailed",
        "oil_painting":   "oil painting, impressionist, rich colors, textured canvas",
        "watercolor":     "watercolor painting, soft edges, pastel colors, artistic",
        "digital_art":    "digital art, concept art, trending on ArtStation, vibrant",
        "sketch":         "pencil sketch, detailed linework, black and white, artistic",
    }

    enhanced_prompt = f"{prompt}, {style_modifiers.get(style, '')}"
    negative_prompt = "blurry, low quality, distorted, ugly, watermark, text, bad anatomy"

    # Step 1: Submit generation request
    payload = {
        "model":    "sdxl-base",
        "data": {
            "prompt":          enhanced_prompt,
            "negprompt":       negative_prompt,
            "samples":         1,
            "steps":           steps,
            "cfg_scale":       guidance,
            "aspect_ratio":    "square",
            "safe_filter":     True,
        }
    }

    resp = requests.post(
        f"{MONSTER_BASE}/generate/txt2img",
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    if resp.status_code != 200:
        raise ValueError(f"MonsterAPI error {resp.status_code}: {resp.text}")

    process_id = resp.json().get("process_id")
    if not process_id:
        raise ValueError("No process_id returned from MonsterAPI.")

    # Step 2: Poll for result (max 3 minutes)
    for _ in range(36):
        time.sleep(5)
        status_resp = requests.get(
            f"{MONSTER_BASE}/status/{process_id}",
            headers=HEADERS,
            timeout=15
        )
        if status_resp.status_code != 200:
            continue

        data   = status_resp.json()
        status = data.get("status", "").lower()

        if status == "completed":
            result = data.get("result", {})
            # MonsterAPI returns output list with image URLs
            output = result.get("output", [])
            if output:
                return output[0]
            # Sometimes it's nested differently
            images = result.get("images", [])
            if images:
                return images[0]
            raise ValueError("Generation completed but no image URL found.")

        elif status in ("failed", "error"):
            msg = data.get("result", {}).get("error_message", "Generation failed.")
            raise ValueError(f"MonsterAPI generation failed: {msg}")

    raise ValueError("Image generation timed out after 3 minutes.")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe_route():
    """Receives audio blob, returns transcribed text."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received."}), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()
    mime_type   = audio_file.content_type or "audio/webm"

    if len(audio_bytes) < 1000:
        return jsonify({"error": "Audio too short. Please speak for at least 1 second."}), 400

    try:
        text = transcribe_audio(audio_bytes, mime_type)
        return jsonify({"text": text})
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500


@app.route("/generate", methods=["POST"])
def generate_route():
    """Receives prompt + style, returns image URL."""
    data    = request.get_json()
    prompt  = data.get("prompt", "").strip()
    style   = data.get("style", "photorealistic")
    steps   = int(data.get("steps", 30))
    guidance= float(data.get("guidance", 7.5))

    if not prompt:
        return jsonify({"error": "No prompt provided."}), 400
    if len(prompt) > 500:
        return jsonify({"error": "Prompt too long (max 500 chars)."}), 400
    if MONSTER_API_KEY == "YOUR_MONSTER_API_KEY_HERE":
        return jsonify({"error": "Monster API key not set. Add it to app.py or set MONSTER_API_KEY env variable."}), 400

    try:
        image_url = generate_image(prompt, style, steps, guidance)
        return jsonify({"image_url": image_url, "prompt": prompt})
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500


@app.route("/speech-to-image", methods=["POST"])
def speech_to_image_route():
    """One-shot: audio → transcribe → generate image."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file received."}), 400

    audio_file  = request.files["audio"]
    audio_bytes = audio_file.read()
    mime_type   = audio_file.content_type or "audio/webm"
    style       = request.form.get("style", "photorealistic")

    if len(audio_bytes) < 1000:
        return jsonify({"error": "Audio too short."}), 400
    if MONSTER_API_KEY == "YOUR_MONSTER_API_KEY_HERE":
        return jsonify({"error": "Monster API key not set."}), 400

    try:
        text      = transcribe_audio(audio_bytes, mime_type)
        image_url = generate_image(text, style)
        return jsonify({"text": text, "image_url": image_url})
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Failed: {str(e)}"}), 500


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if MONSTER_API_KEY == "YOUR_MONSTER_API_KEY_HERE":
        print("\n⚠️  WARNING: Set your MonsterAPI key!")
        print("   Option 1: Edit MONSTER_API_KEY in app.py")
        print("   Option 2: export MONSTER_API_KEY='your_key_here'\n")
    app.run(debug=True, port=5000)
