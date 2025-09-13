import json
import os
import queue
import pyaudio
import requests
import yaml
from google.cloud import speech
from google.oauth2 import service_account

from Eng2Cn import translate_text

# Global
q = queue.Queue()
credentials = None
PROJECT_ID = ''
audio_source_language = ''
source_language = ''
target_language = ''
push_url = ''

def callback(in_data, frame_count, time_info, status_flags):
    q.put(in_data)
    return None, pyaudio.paContinue


def listen_print_loop(responses):
    """Iterates through server responses and prints them."""
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript.strip()
        if result.is_final:
            # [Main Integration Here!!]

            if transcript:
                try:
                    # Output what the speaker said
                    print(f"Speakr: {transcript}")
                    # Output the translation
                    translated_text = translate_text(transcript, source_language= source_language, target_language = target_language, credentials=credentials, PROJECT_ID=PROJECT_ID)
                    print(f"Translated: {translated_text}")

                    # Push to url
                    try:
                        requests.post(push_url, json={"text": transcript+' '+translated_text}, headers={'Content-Type': 'application/json'})
                    except Exception as e:
                        print("Push Server Error:", str(e)[:30])

                except Exception as e:
                    print(f"Error: {e}")


def main():
    # Initial Configuration
    ConfigureFile = "./config.yaml"
    with open(ConfigureFile, 'r', encoding='utf-8') as f:
        yaml_conf: dict = yaml.safe_load(f)
        f.close()
    credentials_json_file = yaml_conf['credentials_json_file']
    # Speech-to-Text language source & target
    global audio_source_language
    audio_source_language = yaml_conf['audio_source_language']
    # Text-Translation language source & target
    global source_language
    global target_language
    source_language = yaml_conf['source_language']
    target_language = yaml_conf['target_language']

    # Load credentials
    global credentials
    credentials = service_account.Credentials.from_service_account_file(credentials_json_file)
    # Create client for speech (audio)
    client = speech.SpeechClient(credentials=credentials)

    # Load PROJECT_ID for Eng2CN component
    global PROJECT_ID
    with open(credentials_json_file, "r", encoding="utf-8") as f:
        key_data = json.load(f)
    PROJECT_ID = key_data["project_id"]

    # Audio recording parameters
    RATE = int(yaml_conf['rate'])
    CHUNK = int(yaml_conf['chunk'])

    # push_url
    global push_url
    push_url = yaml_conf['push_url']


    # For more plausible usage to avoid abuse in once, here canceled while true structure.
    # while True:
    for while_true_number in range(0, 10):
        try:

            # Setup audio stream: Although the variable `audio_stream` seems not be called, but it matters in silence
            # Capture the mic
            audio_interface = pyaudio.PyAudio()
            audio_stream = audio_interface.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback,
            )


            print("🎤 Speak into your microphone... (Ctrl+C to stop)")

            # Configure recognition
            streaming_config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=RATE,
                    language_code=audio_source_language,  # You’re speaking English
                ),
                interim_results=True,
                single_utterance=False, # Keep Long Connection, to avoid 12 seconds silent waitting time
            )

            # Generator: audio chunks
            def requests():
                while True:
                    data = q.get()
                    if data is None:
                        break
                    yield speech.StreamingRecognizeRequest(audio_content=data)

            # Start streaming recognition
            responses = client.streaming_recognize(config=streaming_config, requests=requests())

            listen_print_loop(responses)
        except Exception as e:
            print("Re-connecting ...", e)
            while not q.empty():
                q.get()
            continue


if __name__ == "__main__":
    main()
