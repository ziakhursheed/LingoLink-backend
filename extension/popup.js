const recordBtn = document.getElementById("recordBtn");
const statusEl = document.getElementById("status");
const detectedTextEl = document.getElementById("detectedText");
const translatedTextEl = document.getElementById("translatedText");
const targetLangEl = document.getElementById("targetLang");
const audioPlayer = document.getElementById("audioPlayer");

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// ✅ Your Flask backend
const backendURL = "http://127.0.0.1:5000";

recordBtn.addEventListener("click", async () => {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    isRecording = true;

    recordBtn.textContent = "⏹ Stop Recording";
    recordBtn.classList.add("recording");
    statusEl.textContent = "🎙️ Listening...";

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
      statusEl.textContent = "⏳ Processing...";
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      await processAudio(audioBlob);
    };

    // Automatically stop after 5 seconds (optional)
    setTimeout(() => {
      if (isRecording) stopRecording();
    }, 5000);

    mediaRecorder.start();
  } catch (err) {
    console.error(err);
    alert("Microphone access denied or unavailable!");
  }
}

function stopRecording() {
  isRecording = false;
  recordBtn.textContent = "🎤 Start Recording";
  recordBtn.classList.remove("recording");
  statusEl.textContent = "⏹ Stopped.";
  mediaRecorder.stop();
}

async function processAudio(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "speech.webm");
  formData.append("target_lang", targetLangEl.value);

  try {
    const response = await fetch(`${backendURL}/process_audio`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.error) throw new Error(data.error);

    // ✅ Update UI
    detectedTextEl.textContent = `🧠 Detected: ${data.original_text} (${data.source_lang})`;
    translatedTextEl.textContent = `🌍 Translated: ${data.translated_text}`;

    // ✅ Fix audio path
    if (data.audio_url) {
      const audioFile = `${backendURL}${data.audio_url}`;
      audioPlayer.src = audioFile;
      audioPlayer.style.display = "block";
      await audioPlayer.play();
    }

    statusEl.textContent = "✅ Done!";
  } catch (err) {
    console.error("⚠️ Could not process:", err);
    statusEl.textContent = "⚠️ Could not process audio.";
  }
}