# main.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from utilities.file_operations import format_message, load_json
from modules.audio import Audio
import json
import os
from datetime import datetime


class Memory:
    def __init__(self, file_path="einstein_memory.json"):
        self.file_path = file_path
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({"facts": [], "reminders": []}, f, indent=2)
        self.load()

    def load(self):
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_fact(self, fact: str):
        self.data["facts"].append(fact)
        self.save()

    def add_reminder(self, text: str, time: str):
        self.data["reminders"].append({"text": text, "time": time})
        self.save()

    def get_due_reminders(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        due = [r for r in self.data["reminders"] if r["time"] == now]
        self.data["reminders"] = [r for r in self.data["reminders"] if r not in due]
        self.save()
        return due


def init(audio_client):
    init_message = "Hello! I am Einstein, your personal AI assistant. How can I help you?"
    print(format_message("system_output", init_message, data))
    audio_client.speak(init_message)


def shutdown(audio_client):
    shutdown_message = "Goodbye! I hope I was able to help you."
    print(format_message("system_output", shutdown_message, data))
    audio_client.speak(shutdown_message)


def running_einstein(audio_client, memory: Memory):
    reminders = memory.get_due_reminders()
    for r in reminders:
        reminder_message = f"Reminder: {r['text']}"
        print(format_message("system_output", reminder_message, data))
        audio_client.speak(reminder_message)

    user_input = audio_client.listen_for_codeword().lower()
    print(format_message("user_input", user_input, data))

    if user_input in ["goodbye.", "bye.", "see you.", "ciao.", "later.", "take care."]:
        shutdown(audio_client)
        return False

    if user_input.startswith("remind me"):
        if "about" in user_input:
            parts = user_input.split("about", 1)
            reminder_text = parts[1].strip()
            # store with current date + time fallback (for demo, real impl needs NLP datetime parsing)
            reminder_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            memory.add_reminder(reminder_text, reminder_time)
            confirmation = f"Got it, I will remind you about: {reminder_text} (saved for {reminder_time})"
            print(format_message("system_output", confirmation, data))
            audio_client.speak(confirmation)
            return True

    if user_input.startswith("remember"):
        fact = user_input.replace("remember", "").strip()
        memory.add_fact(fact)
        confirmation = f"Okay, I remembered: {fact}"
        print(format_message("system_output", confirmation, data))
        audio_client.speak(confirmation)
        return True

    template = """You are Einstein, an AI voice assistant. You can help with many different tasks
                  and provide information about everything. Always keep answers short and direct.

                  Question: {Question}

                  Answer: Reply politely, short, and direct.
               """

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="llama3.2")
    chain = prompt | model
    system_output = chain.invoke({"Question": user_input})
    print(format_message("system_output", system_output, data))
    audio_client.speak(system_output)
    return True


def main():
    audio_client = Audio()
    memory = Memory()
    init(audio_client)
    running = True
    while running:
        running = running_einstein(audio_client, memory)


if __name__ == '__main__':
    data = load_json()
    main()
