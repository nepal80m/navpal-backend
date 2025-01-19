import os
import sys
import pyaudio
import wave
import logging
import collections
import webrtcvad
import numpy as np
from google.cloud import speech
from google.cloud import translate_v2 as translate
from six.moves import queue

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all log levels
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Audio recording parameters
RATE = 16000          # Sample rate
CHUNK_DURATION_MS = 30  # Duration of a chunk in ms
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)  # Number of samples per chunk
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1          # Single channel for microphone
WAVE_OUTPUT_FILENAME = "output.wav"  # Output audio file

# VAD parameters
VAD_AGGRESSIVENESS = 2  # VAD aggressiveness (0-3). 3 is the most aggressive
SILENCE_DURATION_MS = 5000  # Duration of silence to consider as end of speech

class AudioFrame(object):
    """Represents a single frame of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk_duration_ms):
        self._rate = rate
        self._chunk_duration_ms = chunk_duration_ms
        self._chunk_size = int(rate * chunk_duration_ms / 1000)
        self._buffer = collections.deque()
        self.closed = True

    def __enter__(self):
        try:
            logging.debug("Initializing PyAudio.")
            self._audio_interface = pyaudio.PyAudio()
            logging.debug("Opening microphone stream.")
            self._audio_stream = self._audio_interface.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=self._rate,
                input=True,
                frames_per_buffer=self._chunk_size,
                stream_callback=self._fill_buffer,
            )
            self.closed = False
            logging.debug("Microphone stream opened successfully.")
            return self
        except Exception as e:
            logging.critical(f"Failed to open microphone stream: {e}")
            sys.exit(1)

    def __exit__(self, type, value, traceback):
        try:
            logging.debug("Closing microphone stream.")
            self._audio_stream.stop_stream()
            self._audio_stream.close()
            self.closed = True
            self._buffer.append(None)
            self._audio_interface.terminate()
            logging.debug("Microphone stream closed.")
        except Exception as e:
            logging.error(f"Error while closing microphone stream: {e}")

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buffer.append(AudioFrame(
            bytes=in_data,
            timestamp=time_info['current_time'],
            duration=self._chunk_duration_ms / 1000.0
        ))
        return None, pyaudio.paContinue

    def generator(self):
        logging.debug("Starting audio generator.")
        while not self.closed:
            if len(self._buffer) == 0:
                continue
            frame = self._buffer.popleft()
            if frame is None:
                logging.debug("Audio generator received termination signal.")
                return
            yield frame.bytes

def write_wave(path, audio_frames):
    """Writes the recorded audio frames to a WAV file."""
    wf = wave.open(path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(audio_frames))
    wf.close()
    logging.info(f"Audio recorded and saved to {path}")

def transcribe_audio(audio_file_path):
    """Transcribes speech from an audio file using Google Speech-to-Text API."""
    logging.info("Initializing Google Speech-to-Text client.")
    try:
        client = speech.SpeechClient()
        logging.debug("Google Speech-to-Text client initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize Google Speech-to-Text client: {e}")
        sys.exit(1)

    # Read the audio file
    try:
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
            logging.debug(f"Read audio file: {audio_file_path}")
    except Exception as e:
        logging.error(f"Failed to read audio file: {e}")
        sys.exit(1)

    # Configure recognition settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ne-NP",  # Nepali language code
    )
    audio = speech.RecognitionAudio(content=content)

    # Perform transcription
    logging.info("Sending audio data to Speech-to-Text API for transcription.")
    try:
        response = client.recognize(config=config, audio=audio)
        logging.debug("Received response from Speech-to-Text API.")
    except Exception as e:
        logging.error(f"An error occurred during transcription: {e}")
        sys.exit(1)

    # Extract transcription
    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript

    if transcription:
        logging.info(f"Transcription (Nepali): {transcription}")
        return transcription
    else:
        logging.warning("No transcription received.")
        return None

def translate_text(text, target_language='en'):
    """Translates text from Nepali to English using Google Translate API."""
    logging.info("Initializing Google Translate client.")
    try:
        translator = translate.Client()
        logging.debug("Google Translate client initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize Google Translate client: {e}")
        sys.exit(1)

    logging.info("Translating transcription to English.")
    try:
        translation = translator.translate(text, target_language=target_language)
        translated_text = translation.get('translatedText', '')
        if translated_text:
            logging.info(f"Translation (English): {translated_text}")
            return translated_text
        else:
            logging.warning("No translation received.")
            return None
    except Exception as e:
        logging.error(f"An error occurred during translation: {e}")
        return None

def main():
    # Initialize VAD
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    logging.debug(f"Initialized VAD with aggressiveness={VAD_AGGRESSIVENESS}")

    # Buffer to hold audio frames
    audio_frames = []
    triggered = False
    silence_ms = 0

    # Calculate number of consecutive silent frames needed to consider as end of speech
    num_silent_chunks = int(SILENCE_DURATION_MS / CHUNK_DURATION_MS)

    logging.info("Starting live speech capture. Speak into the microphone...")

    with MicrophoneStream(RATE, CHUNK_DURATION_MS) as stream:
        for frame in stream.generator():
            if frame is None:
                break
            # Convert byte data to PCM samples
            pcm_samples = np.frombuffer(frame, dtype=np.int16)
            is_speech = vad.is_speech(frame, RATE)

            logging.debug(f"VAD detected speech: {is_speech}")

            if not triggered:
                if is_speech:
                    logging.info("Speech started.")
                    triggered = True
                    audio_frames.append(frame)
                    silence_ms = 0
            else:
                audio_frames.append(frame)
                if not is_speech:
                    silence_ms += CHUNK_DURATION_MS
                    logging.debug(f"Silence detected: {silence_ms}ms")
                    if silence_ms > SILENCE_DURATION_MS:
                        logging.info("Speech ended.")
                        break
                else:
                    silence_ms = 0

    # Save the recorded audio
    write_wave(WAVE_OUTPUT_FILENAME, audio_frames)

    # Transcribe the audio
    transcription = transcribe_audio(WAVE_OUTPUT_FILENAME)
    if not transcription:
        logging.error("Transcription failed. Exiting.")
        sys.exit(1)

    # Translate the transcription
    translation = translate_text(transcription)
    if not translation:
        logging.error("Translation failed. Exiting.")
        sys.exit(1)

    logging.info("Process completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Exiting...")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")
        sys.exit(1)