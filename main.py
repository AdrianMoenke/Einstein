# Project Idea: Create J.A.R.V.I.S your personal AI Assistant
import playsound
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from pyht import Client
from dotenv import load_dotenv
from pyht.client import TTSOptions
import os
from vosk import Model, KaldiRecognizer
import argparse
import queue
import sys
import sounddevice as sd
import json
import wx

def starting_up_jarvis():
    data = client.tts("Hello Sir! I am Jarvis. How can I help you today?", options, 'Play3.0-mini-http')
    chunks: bytearray = bytearray()

    for chunk in data:
        chunks.extend(chunk)
    with open("output.wav", "wb") as f:
        f.write(chunks)

    playsound.playsound("output.wav")



def int_or_str(text2):
    """Helper function for argument parsing."""
    try:
        return int(text2)
    except ValueError:
        return text2

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def listen():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-l", "--list-devices", action="store_true",
        help="show list of audio devices and exit")
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        "-f", "--filename", type=str, metavar="FILENAME",
        help="audio file to store recording to")
    parser.add_argument(
        "-d", "--device", type=int_or_str,
        help="input device (numeric ID or substring)")
    parser.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate")
    parser.add_argument(
        "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
    args = parser.parse_args(remaining)

    try:
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, "input")
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info["default_samplerate"])

        if args.model is None:
            model = Model(lang="de")
        else:
            model = Model(lang=args.model)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                               dtype="int16", channels=1, callback=callback):

            print("#############")
            print("Listening....")
            print("#############")

            rec = KaldiRecognizer(model, args.samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    global text
                    user_input = json.loads(rec.Result())
                    text = user_input['text']
                    if "Jarvis" in text or "jarvis" in text:
                        return
                if dump_fn is not None:
                    dump_fn.write(data)

    except KeyboardInterrupt:
        print("\nDone")
        parser.exit(0)



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

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500, 500))

        self.button = wx.Button(self, label="My simple app.")
        self.Bind(
            wx.EVT_BUTTON, self.handle_button_click, self.button
        )

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.button)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.Show()

    def handle_button_click(self, event):
        self.Close()


def buildUI():
    app = wx.App(False)
    w = MainWindow(None, "Hello World")
    app.MainLoop()


if __name__ == '__main__':
    text = ""

    client = Client(
        user_id=os.getenv("PLAY_HT_USER_ID"),
        api_key=os.getenv("PLAY_HT_API_KEY"),
    )

    options = TTSOptions(
        voice="s3://voice-cloning-zero-shot/9f1ee23a-9108-4538-90be-8e62efc195b6/charlessaad/manifest.json")

    template = """You are a Jarvis, an AI voice Assistant. You can help with many different tasks and provide information
            on everything. You refer to me as sir and answer short and direct.

            Question: {question}

            Answer: Answer short and direct and refer to me as sir"""

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="llama3.2")
    chain = prompt | model

    load_dotenv()
    q = queue.Queue()
    #buildUI()
    starting_up_jarvis()
    while True:
        listen()
        running_jarvis(text)
