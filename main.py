# Project Idea: Create Einstein your personal AI Assistant
import playsound
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from dotenv import load_dotenv
import sounddevice as sd
from melo.api import TTS
import speech_recognition as sr
import whisper
import time
import numpy as np
import wave

def init():
    init_message = "Hello Sir! I am Einstein. How can I help you today?"

def voice_recognizer(audio_file: str):
    model = whisper.load_model("turbo")
    result = model.transcribe(audio_file)
    return result["text"]

def listen_for_codeword(mic_index = None):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Idle...")
        while True:
            audio = recognizer.listen(source)
            with open("system_output.wav", "wb") as f:
                f.write(audio.get_wav_data())
            output = voice_recognizer("system_output.wav").lower()
            try:
                if "einstein" in output:
                    listen_for_command(mic_index)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Fehler bei der Anfrage: {e}")

def listen_for_command(mic_index = None):
    SAMPLE_RATE = 44100  # Abtastrate
    CHUNK_DURATION = 0.5  # Dauer eines Chunks in Sekunden
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)  # Größe der Chunks
    SILENCE_THRESHOLD = 0.00001  # Schwelle für Stille (zwischen 0 und 1)
    SILENCE_DURATION = 2  # Sekunden, die Stille dauern muss, um zu stoppen
    DEBUG = True  # Debug-Modus für Lautstärkeinformationen
    output_file = "user_output.wav"

    print("Starte Aufnahme...")
    audio_frames = []  # Liste, um die Audio-Chunks zu speichern
    silent_duration = 0  # Dauer der Stille
    is_recording = True
    start_time = time.time()

    def callback(indata, frames, time, status):
        """Callback-Funktion, die für jeden Chunk aufgerufen wird."""
        nonlocal silent_duration, is_recording, audio_frames

        # Lautstärke des aktuellen Chunks berechnen
        volume_norm = np.linalg.norm(indata) / len(indata)
        if DEBUG:
            print(f"Lautstärke (Normwert): {volume_norm:.6f}")

        # Prüfen, ob der aktuelle Chunk als Stille gilt
        if volume_norm < SILENCE_THRESHOLD:
            silent_duration += CHUNK_DURATION
        else:
            silent_duration = 0  # Stille-Count zurücksetzen, wenn Ton erkannt wird

        # Audio-Chunk speichern
        audio_frames.append(indata.copy())

        # Aufnahme stoppen, wenn die Stille die Schwelle erreicht
        if silent_duration >= SILENCE_DURATION:
            print(f"Stille erkannt nach {silent_duration:.2f} Sekunden.")
            is_recording = False

    try:
        # Mikrofon-Stream starten
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback, blocksize=CHUNK_SIZE,
                            device=mic_index):
            while is_recording:
                sd.sleep(int(CHUNK_DURATION * 1000))  # Wartezeit pro Chunk
    except Exception as e:
        print(f"Fehler während der Aufnahme: {e}")

    print("Aufnahme gestoppt.")
    print(f"Gesamtdauer der Aufnahme: {time.time() - start_time:.2f} Sekunden")

    # Aufnahme speichern
    print("Speichere Aufnahme...")
    frames_np = np.concatenate(audio_frames, axis=0)
    with wave.open(output_file, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-Bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((frames_np * 32767).astype(np.int16).tobytes())

    print(f"Aufnahme gespeichert als {output_file}")

def list_microphones():
    """Listet verfügbare Mikrofone auf."""
    devices = sd.query_devices()
    print("Verfügbare Audio-Geräte:")
    for idx, device in enumerate(devices):
        print(f"{idx}: {device['name']}")

def get_device_info(index):
    """Gibt Informationen über ein bestimmtes Gerät zurück."""
    device_info = sd.query_devices(index)
    max_input_channels = device_info["max_input_channels"]
    print(f"Gerät: {device_info['name']} | Max. Eingabekanäle: {max_input_channels}")
    return max_input_channels

def running_jarvis(user_input):
    print("User:" + user_input)
    if user_input == "Shutdown" or user_input == "shutdown" or user_input == "shut down" or user_input == "Shut down" or user_input == "Shut Down" or user_input == "shut Down":
        client.close()
        return
    output = chain.invoke({"question": user_input})
    print("J.A.R.V.I.S: " + output)

    data = client.tts(output, options, 'Play3.0-mini-http')
    chunks: bytearray = bytearray()

    for chunk in data:
        chunks.extend(chunk)
    with open("output.wav", "wb") as f:
        f.write(chunks)

    playsound.playsound("output.wav")

def main():
    list_microphones()
    mic_index = int(input("Wähle die Nummer deines Mikrofons: "))
    listen_for_codeword(mic_index)
    load_dotenv()
    template = """You are a Jarvis, an AI voice Assistant. You can help with many different tasks and provide information
                    on everything. You refer to me as sir and answer short and direct.

                    Question: {question}

                    Answer: Answer short and direct and refer to me as sir"""
    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="llama3.2")
    chain = prompt | model
    text = ""
    speed = 1.0
    device = 'cpu'
    text_2 = "test"


if __name__ == '__main__':
    main()
