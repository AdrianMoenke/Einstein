import json
import whisper
import speech_recognition as sr
import time
import numpy as np
import sounddevice as sd
import wave
from main import listen_for_command
from utilities.file_operations import create_wave_system_output, get_wave_file, format_message, load_json


class Audio:
    def __init__(self):
        self.recognition_model = whisper.load_model("turbo")
        self.recognizer = sr.Recognizer
        self.json_file = load_json()


    def recognize_voice(self, audio_file: str):
        result = self.recognition_model.transcribe(audio_file)
        return result["text"]


    def listen_for_command(self):
        SAMPLE_RATE = 44100
        CHUNK_DURATION = 0.5
        CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
        SILENCE_THRESHOLD = 0.00001
        SILENCE_DURATION = 2

        print(format_message("info", "Listening...", self.json_file))
        audio_frames = []
        silent_duration = 0
        is_recording = True
        start_time = time.time()

        def callback(indata):
            nonlocal silent_duration, is_recording, audio_frames
            volume_norm = np.linalg.norm(indata) / len(indata)
            print(format_message("debug", f"Volume : {volume_norm:.6f}", self.json_file))
            if volume_norm < SILENCE_THRESHOLD:
                silent_duration += CHUNK_DURATION
            else:
                silent_duration = 0

            audio_frames.append(indata.copy())
            if silent_duration >= SILENCE_DURATION:
                print(format_message("debug", f"Silence detected after : {silent_duration:.2f} seconds.", self.json_file))
                is_recording = False

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback, blocksize=CHUNK_SIZE):
                while is_recording:
                    sd.sleep(int(CHUNK_DURATION * 1000))  # Wartezeit pro Chunk
        except Exception as e:
            print(format_message("error", "Error during listening.", self.json_file))

        print(format_message("info", "Done listening.", self.json_file))
        print(format_message("debug", f"Duration of request: {time.time() - start_time:.2f} seconds", self.json_file))

        frames_np = np.concatenate(audio_frames, axis=0)

        with wave.open(get_wave_file(), "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-Bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((frames_np * 32767).astype(np.int16).tobytes())


    def listen_for_codeword(self):
        with sr.Microphone() as source:
            print(format_message("info", "Waiting for Codeword...", self.json_file))
            while True:
                audio = self.recognizer.listen(source)
                create_wave_system_output(audio)
                output = self.recognition_model(get_wave_file()).lower()
                try:
                    for codeword in self.json_file["codewords"]:
                        if codeword.lower() in output:
                            listen_for_command(self)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print(format_message("error", "Request Error.", self.json_file))
                except FileNotFoundError:
                    print(format_message("error", "File not found.", self.json_file))
                except json.JSONDecodeError:
                    print(format_message("error", "Couldn't interpret file as JSON.", self.json_file))