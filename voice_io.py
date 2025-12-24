import pyttsx3
import pyaudio
import pvporcupine
from vosk import Model, KaldiRecognizer
import json
import os
from dotenv import load_dotenv

load_dotenv()

class VoiceIO:
    def __init__(self, wake_word=True, offline=True):
        # TTS - Female Voice
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        for v in voices:
            if "female" in v.name.lower() or v.gender == "female":
                self.engine.setProperty('voice', v.id)
                break
        self.engine.setProperty('rate', 180)

        # Wake Word
        self.wake_word = wake_word
        if self.wake_word:
            try:
                self.porcupine = pvporcupine.create(
                    access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
                    keyword_paths=["nia_custom.ppn"]  # Your custom model
                )
                self.wake_words = ["Hey Nia", "Nia", "Hello", "Can you help me"]
                self.pa = pyaudio.PyAudio()
                self.audio_stream = self.pa.open(
                    rate=self.porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=self.porcupine.frame_length
                )
            except Exception as e:
                print("⚠️ Wake word disabled:", e)
                self.wake_word = False

        # Speech Recognition
        self.offline = offline
        if offline and not os.path.exists("vosk-model-small-en-us-0.15"):
            raise Exception("❌ Missing Vosk model! Download from https://alphacephei.com/vosk/models")
        if offline:
            self.vosk_model = Model("vosk-model-small-en-us-0.15")

    def speak(self, text):
        print(f"Nia: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def wait_for_wake_word(self):
        if not self.wake_word:
            return
        print("💤 Listening for: 'Hey Nia', 'Nia', 'Hello', or 'Can you help me'...")
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = [int.from_bytes(pcm[i:i+2], byteorder='little', signed=True) for i in range(0, len(pcm), 2)]
            result = self.porcupine.process(pcm)
            if result >= 0:
                detected = self.wake_words[result] if result < len(self.wake_words) else "custom phrase"
                print(f"✨ Detected: '{detected}'")
                self.speak("Yes? How can I help?")
                return

    def listen(self):
        if self.wake_word:
            self.wait_for_wake_word()
        if self.offline:
            return self._listen_vosk()

    def _listen_vosk(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        rec = KaldiRecognizer(self.vosk_model, 16000)
        print("🎙️ Listening for command...")
        while True:
            data = stream.read(4000)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    return text