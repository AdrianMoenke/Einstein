# Project Idea: Create Einstein your personal AI Assistant
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from utilities.file_operations import format_message, load_json
from modules.audio import Audio

def init(audio_client):
    init_message = "Hallo! Ich bin Einstein dein persönlicher KI Assistent. Wie kann ich dir helfen?"
    print(format_message("system_output", init_message, data))
    audio_client.speak(init_message)


def shutdown(audio_client):
    shutdown_message = "Auf Wiedersehen! Ich hoffe ich konnte dir weiterhelfen."
    print(format_message("system_output", shutdown_message, data))
    audio_client.speak(shutdown_message)


def running_einstein(audio_client):
    user_input = audio_client.listen_for_codeword().lower()
    print(format_message("user_input", user_input, data))

    if user_input == "auf wiedersehen." or user_input == "tschüss." or user_input == "bis dann." or user_input == "tschau." or user_input == "ciao." or user_input == "hauste rin.":
        shutdown(audio_client)
        return

    template = """Du bist Einstein, ein KI Sprachassistent. Du kannst mit vielen verschiedenen Aufgaben helfen
                  und Informationen zu allem bereitstellen. Du kannst mich gerne dutzen. Du antwortest immer sehr kurz und direkt.

                  Frage: {Frage}

                  Antwort: Antworte höflich, kurz, direkt und dutze mich
               """

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model="llama3.2")
    chain = prompt | model
    system_output = chain.invoke({"Frage": user_input})
    print(format_message("system_output", system_output, data))
    audio_client.speak(system_output)


def main():
    audio_client = Audio()
    init(audio_client)
    while True:
        running_einstein(audio_client)


if __name__ == '__main__':
    data = load_json()
    main()
