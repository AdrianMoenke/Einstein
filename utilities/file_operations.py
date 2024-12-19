import os
import json

output_dir = "output"
file_path = str(os.path.join(output_dir, "system_output.wav"))

def create_wave_system_output(audio):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(file_path, "wb") as f:
        f.write(audio.get_wav_data())

def get_output_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "output/system_output.wav")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return file_path

def load_json():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "data.json")

    with open(json_path, "r") as f:
        data = json.load(f)
    return data

def format_message(message_type, message, prefixes):
    prefix = prefixes["prefixes"].get(message_type, "[UNKNOWN]")
    return f"{prefix} {message}"