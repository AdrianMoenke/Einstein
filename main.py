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
                json.dump({"facts": [], "reminders": [], "tasks": [], "journals": [], "api_keys": {}}, f)
            os.chmod(file_path, 0o666)
        self.load()

    def load(self):
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=2)
        os.chmod(self.file_path, 0o666)

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

    def add_task(self, task: str):
        self.data["tasks"].append({"task": task, "done": False})
        self.save()

    def list_tasks(self):
        return [t for t in self.data["tasks"] if not t["done"]]

    def complete_task(self, task: str):
        for t in self.data["tasks"]:
            if t["task"].lower() == task.lower() and not t["done"]:
                t["done"] = True
                self.save()
                return True
        return False

    def remove_task_by_index(self, index: int):
        removed = self.data["tasks"].pop(index)
        self.save()
        return removed

    def add_journal_entry(self, entry: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.data["journals"].append({"time": timestamp, "entry": entry})
        self.save()

    def get_recent_journal(self, limit=3):
        return self.data["journals"][-limit:]

    def save_api_key(self, service: str, key: str):
        self.data.setdefault("api_keys", {})
        self.data["api_keys"][service] = key
        self.save()

    def get_api_key(self, service: str):
        return self.data.get("api_keys", {}).get(service)


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

    if user_input.startswith("add task"):
        task = user_input.replace("add task", "").strip()
        memory.add_task(task)
        confirmation = f"Task added: {task}"
        print(format_message("system_output", confirmation, data))
        audio_client.speak(confirmation)
        return True

    if user_input.startswith("list tasks"):
        tasks = memory.list_tasks()
        if tasks:
            task_list = ", ".join([t["task"] for t in tasks])
            response = f"Your tasks are: {task_list}"
        else:
            response = "You have no tasks."
        print(format_message("system_output", response, data))
        audio_client.speak(response)
        return True

    if user_input.startswith("complete task"):
        task = user_input.replace("complete task", "").strip()
        if memory.complete_task(task):
            response = f"Task '{task}' marked as complete."
        else:
            response = f"Task '{task}' not found."
        print(format_message("system_output", response, data))
        audio_client.speak(response)
        return True

    if user_input.startswith("remove task"):
        task = user_input.replace("remove task", "").strip()
        index = int(task)
        removed = memory.remove_task_by_index(index)
        response = f"Removed task: {removed['task']}"
        print(format_message("system_output", response, data))
        audio_client.speak(response)
        return True

    if user_input.startswith("write journal"):
        entry = user_input.replace("write journal", "").strip()
        memory.add_journal_entry(entry)
        confirmation = "Journal entry saved."
        print(format_message("system_output", confirmation, data))
        audio_client.speak(confirmation)
        return True

    if user_input.startswith("read journal"):
        entries = memory.get_recent_journal()
        if entries:
            response = "Here are your recent journal entries: " + " | ".join(
                [f"[{e['time']}] {e['entry']}" for e in entries]
            )
        else:
            response = "Your journal is empty."
        print(format_message("system_output", response, data))
        audio_client.speak(response)
        return True

    if user_input.startswith("save api key"):
        rest = user_input.replace("save api key", "").strip()
        parts = rest.split(" ", 1)
        service = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        memory.save_api_key(service, key)
        confirmation = f"API key for {service} saved."
        print(format_message("system_output", confirmation, data))
        audio_client.speak(confirmation)
        return True

    if user_input.startswith("show api key"):
        service = user_input.replace("show api key", "").strip()
        key = memory.get_api_key(service)
        if key:
            response = f"API key for {service} is: {key}"
        else:
            response = f"No API key saved for {service}."
        print(format_message("system_output", response, data))
        audio_client.speak(response)
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
