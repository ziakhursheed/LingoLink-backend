import os
import uuid
import warnings
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
from gtts import gTTS
from deep_translator import GoogleTranslator

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ FFmpeg setup (Linux compatible for Render)
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

print("✅ FFmpeg path set successfully.")
print("   FFmpeg:", FFMPEG_BIN)
print("   FFprobe:", FFPROBE_BIN)

# ✅ Load Whisper model
print("⏳ Loading Whisper model...")
model = whisper.load_model("small")
print("✅ Whisper model loaded successfully.")

# ✅ Root route (for Render check)
@app.route('/')
def home():
    return jsonify({"message": "LingoLink backend is live!"})

# ✅ Helper: Convert WEBM → WAV
def convert_to_wav(input_path, output_path):
    try:
        subprocess.run(
            [FFMPEG_BIN, "-i", input_path, "-ac", "1", "-ar", "16000", output_path, "-y"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return True
    except Exception as e:
        print("❌ FFmpeg conversion error:", e)
        return False

# ✅ Helper: Detect + Translate
def detect_and_translate(text, target_lang="en"):
    try:
        detected = GoogleTranslator(source="auto", target=target_lang)
        translated = detected.translate(text)
        src_lang = detected.source  # auto-detected source language
        return translated, src_lang
    except Exception as e:
        print("❌ Translation error:", e)
        return text, "unknown"

# ✅ Helper: Text-to-Speech
def text_to_speech(text, lang="en"):
    try:
        filename = f"translated_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
        return filename
    except Exception as e:
        print("❌ TTS generation error:", e)
        return None

# ✅ API Endpoint
@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        # Get target language from frontend (default = English)
        target_lang = request.form.get("target_lang", "en")

        # Save uploaded file
        file = request.files["audio"]
        temp_input = os.path.join(UPLOAD_FOLDER, "temp_audio.webm")
        file.save(temp_input)
        print("📂 Audio file saved:", temp_input)
        print("📏 File size:", os.path.getsize(temp_input), "bytes")

        # Convert to WAV
        temp_output = os.path.join(UPLOAD_FOLDER, "temp_audio.wav")
        print("🔄 Converting WEBM → WAV using FFmpeg...")
        convert_to_wav(temp_input, temp_output)

        # Transcribe speech
        result = model.transcribe(temp_output)
        text = result["text"].strip()
        print("🗣️ Recognized speech:", text)

        # Translate
        print("🌍 Detecting language and translating...")
        translated_text, src_lang = detect_and_translate(text, target_lang)
        print("🌍 Detected Language:", src_lang)
        print("💬 Translation:", translated_text)

        # Generate TTS
        print("🎶 Generating TTS audio...")
        tts_filename = text_to_speech(translated_text, target_lang)
        if not tts_filename:
            return jsonify({"error": "TTS generation failed"}), 500

        print(f"✅ Saved translated speech to {os.path.join(UPLOAD_FOLDER, tts_filename)}")

        return jsonify({
            "original_text": text,
            "translated_text": translated_text,
            "source_lang": src_lang,
            "target_lang": target_lang,
            "audio_url": f"/uploads/{tts_filename}"
        })

    except Exception as e:
        print("❌ Error in /process_audio:", e)
        return jsonify({"error": str(e)}), 500

# ✅ Serve audio files
@app.route("/uploads/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


