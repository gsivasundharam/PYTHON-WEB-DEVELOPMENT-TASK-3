# 🎨 VoiceCanvas — Speech to Image Generation

Records voice in **any language**, transcribes it, and generates an image
using **MonsterAPI** (Stable Diffusion XL).

---

## 📁 Project Structure

```
speech2image/
├── app.py                  ← Flask backend
├── templates/
│   └── index.html          ← Full frontend UI
├── requirements.txt
└── README.md
```

---

## ⚙️ Step 0 — Install system dependencies

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg portaudio19-dev python3-pyaudio
```

**macOS:**
```bash
brew install ffmpeg portaudio
```

**Windows:**
- Download ffmpeg: https://ffmpeg.org/download.html → add to PATH
- PyAudio installs via pip

---

## ⚙️ Step 1 — Install Python packages

```bash
pip install -r requirements.txt
```

---

## 🔑 Step 2 — Get your MonsterAPI key

1. Go to **https://monsterapi.ai** and sign up (free tier available)
2. Dashboard → API Keys → Create key
3. Copy the key

**Set the key (choose one method):**

**Option A — Edit app.py directly:**
```python
MONSTER_API_KEY = "your_actual_key_here"
```

**Option B — Environment variable (recommended):**
```bash
# Linux/macOS:
export MONSTER_API_KEY="your_actual_key_here"

# Windows:
set MONSTER_API_KEY=your_actual_key_here
```

---

## 🚀 Step 3 — Run the app

```bash
python app.py
```

Open: **http://localhost:5000**

---

## 🎤 How to use

1. Click the **mic button** and speak your image description
2. The app transcribes your speech (any language supported)
3. Edit the transcribed text if needed
4. Choose an **image style** (photorealistic, anime, oil painting, etc.)
5. Click **Generate Image**
6. Wait ~30–60 seconds for Stable Diffusion to render

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Main UI |
| `/transcribe` | POST | Audio file → transcribed text |
| `/generate` | POST | Text prompt → image URL |
| `/speech-to-image` | POST | Audio file → image (one-shot) |

---

## 🎨 Supported Image Styles

| Style | Description |
|---|---|
| photorealistic | Ultra-detailed 8K DSLR quality |
| digital_art | ArtStation concept art style |
| anime | Studio Ghibli inspired |
| oil_painting | Impressionist canvas texture |
| watercolor | Soft pastel strokes |
| sketch | Black & white pencil linework |

---

## 🌍 Supported Languages

Any language supported by Google Speech Recognition — English, Tamil,
Hindi, Japanese, French, Spanish, German, Arabic, and 100+ more.
The language is auto-detected from your speech.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg not found` | Install ffmpeg (see Step 0) |
| Mic not working in browser | Use Chrome/Firefox, allow mic permission |
| `Monster API key not set` | Set MONSTER_API_KEY (see Step 2) |
| Generation timeout | MonsterAPI free tier can be slow — wait up to 3 min |
| `Could not understand audio` | Speak clearly, reduce background noise |
