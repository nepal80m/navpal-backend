# from openai import OpenAI
# client = OpenAI()

audio_file= open("/Users/anishd/Documents/QuackUO/navpal/output_final.wav", "rb")
# transcription = client.audio.transcriptions.create(
#     model="whisper-1", 
#     file=audio_file
# )

# print(transcription.text)

# from google.cloud import translate_v2 as translate

# def test_translation(text):
#     translator = translate.Client()
#     target = 'en'
#     translation = translator.translate(text, target_language=target)
#     print(f"Original: {text}")
#     print(f"Translated: {translation['translatedText']}")

# test_translation(transcription.text)

from openai import OpenAI
client = OpenAI()

# audio_file = open("/path/to/file/german.mp3", "rb")
transcription = client.audio.translations.create(
    model="whisper-1", 
    file=audio_file,
)

print(transcription.text)

