import os
import json

output_dir = "output"
file_path = os.path.join(output_dir, "system_output.wav")

def create_wave_system_output(audio):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(file_path, "wb") as f:
        f.write(audio.get_wav_data())

def get_wave_file():
    return file_path

def load_json():
    with open("data.json", "r") as f:
        data = json.load(f)
    return data

def format_message(message_type, message, prefixes):
    prefix = prefixes["prefixes"].get(message_type, "[UNKNOWN]")
    return f"{prefix} {message}"