import json
import playsound
import whisper
import speech_recognition as sr
import time
import numpy as np
import sounddevice as sd
import wave
from utilities.file_operations import create_wave_system_output, get_output_file, format_message, load_json
from piper.voice import PiperVoice


class Audio:
    def __init__(self):
        self.recognition_model = whisper.load_model("turbo")
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.json_file = load_json()
        self.tts_model = "utilities/voice_model.onnx"
        self.voice = PiperVoice.load(self.tts_model)


    def recognize_voice(self, audio_file):
        result = self.recognition_model.transcribe(audio_file)
        return result["text"]


    def speak(self, text):
        try:
            wave_file: wave.Wave_write = wave.open(get_output_file(), "wb")
            self.voice.synthesize(text, wave_file)
        except IOError as e:
            print(format_message("error", "Something went wrong during I/O operations: \n" + e, self.json_file))

        playsound.playsound(get_output_file())


    def listen_for_codeword(self):
        with self.microphone as mic:
            print(format_message("info", "Waiting for Codeword...", self.json_file))
            while True:
                audio = self.recognizer.listen(mic)
                create_wave_system_output(audio)
                output = self.recognize_voice(get_output_file()).lower()
                try:
                    for codeword in self.json_file["codewords"]:
                        if codeword.lower() in output:
                            return self.listen_for_command()
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    print(format_message("error", "Request Error.", self.json_file))
                except FileNotFoundError:
                    print(format_message("error", "File not found.", self.json_file))
                except json.JSONDecodeError:
                    print(format_message("error", "Couldn't interpret file as JSON.", self.json_file))


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

        def callback(indata, frames, time, status):
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
                    sd.sleep(int(CHUNK_DURATION * 1000))
        except Exception:
            print(format_message("error", "Error during listening.", self.json_file))

        print(format_message("info", "Done listening.", self.json_file))
        print(format_message("debug", f"Duration of request: {time.time() - start_time:.2f} seconds", self.json_file))

        frames_np = np.concatenate(audio_frames, axis=0)

        with wave.open(get_output_file(), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes((frames_np * 32767).astype(np.int16).tobytes())
            return self.recognize_voice(get_output_file())