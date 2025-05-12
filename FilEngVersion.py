import openai
import speech_recognition as sr
import pyttsx3
import numpy as np
from gtts import gTTS
import pygame
from openai.error import RateLimitError, AuthenticationError
import time
from langdetect import detect  # Language detection library

# Set default language to English
language = 'en'

# Hardcoded API Key
openai.api_key = ""  # Replace with your actual key

r = sr.Recognizer()
tts_engine = 'gtts'  # or 'pyttsx3' or 'openai'

engine = pyttsx3.init()
voice = engine.getProperty('voices')[2]
engine.setProperty('voice', voice.id)

model = 'gpt-3.5-turbo'
name = "User"
greetings = [f"whats up {name}", "yeah?", "hello there!", f"Ahoy, {name}!", "How can I help?", "what is it?"]

messages = [{"role": "system", "content": "You are a helpful personal assistant. Keep answers under 100 words."}]

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

def speak_text(text, language):
    if tts_engine == 'pyttsx3':
        engine.say(text)
        engine.runAndWait()
    elif tts_engine == 'gtts':
        tts = gTTS(text=text, lang=language)
        tts.save('response.mp3')
        play_audio('response.mp3')
    elif tts_engine == 'openai':
        response = openai.Audio.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file('response.mp3')
        play_audio('response.mp3')

def stream_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=1,
            stream=True
        )
        full_response = ""
        for chunk in response:
            if "choices" in chunk:
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content", "")
                print(content, end="", flush=True)
                full_response += content
        print()
        return full_response
    except RateLimitError:
        print("Rate limit exceeded.")
        return "I'm sorry, I'm being rate-limited right now."
    except AuthenticationError:
        print("Invalid API key.")
        return "I'm sorry, I have a problem with my credentials."

def handle_conversation(language):
    with sr.Microphone() as source:
        play_audio("listen_chime.mp3")
        try:
            print(f"Listening for question in {language}...")
            time.sleep(0.5)
            audio = r.listen(source, timeout=5)
            user_input = r.recognize_google(audio, language=language)  # Use the specified language
            print(f"You said: {user_input}")

            messages.append({"role": "user", "content": user_input})
            assistant_response = stream_response(messages)
            messages.append({"role": "assistant", "content": assistant_response})
            speak_text(assistant_response, language)

        except sr.UnknownValueError:
            print("Didn't catch that.")
            play_audio("error.mp3")
        except sr.RequestError as e:
            print(f"Request error: {e}")
            speak_text("There was an issue with the microphone.", language)
        finally:
            print("Going back to wake word detection...")

def listen_for_wake_word():
    with sr.Microphone() as source:
        print("Listening for 'Teddy'...")

        while True:
            try:
                audio = r.listen(source)
                text = r.recognize_google(audio, language="en")  # Try English first
                if "teddy" in text.lower():
                    print("Wake word 'Teddy' detected.")
                    greet = np.random.choice(greetings)
                    speak_text(greet, language)
                    time.sleep(1)
                    handle_conversation(language)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Microphone error: {e}")
                continue

def detect_language(text):
    try:
        detected_language = detect(text)  # Detect the language of the speech
        print(f"Detected language: {detected_language}")
        if detected_language == 'tl':  # Filipino
            return 'tl-TL'
        else:  # Default to English
            return 'en-EN'
    except Exception as e:
        print(f"Error in language detection: {e}")
        return 'en-EN'  # Default to English if detection fails

# Main loop
while True:
    listen_for_wake_word()  # Starts listening for the wake word "Teddy"
