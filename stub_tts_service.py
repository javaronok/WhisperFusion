import functools
import logging
logging.basicConfig(level = logging.INFO)

from websockets.sync.server import serve

SAMPLE_RATE = 24000  # у Kokoro именно 24 кГц

class WhisperSpeechTTS:

    def initialize_model(self):
        pass

    def run(self, host, port, audio_queue=None, should_send_server_ready=None):
        self.initialize_model()
        logging.info("[WhisperSpeech INFO:] Warmed up Whisper Speech torch compile model. Connect to the WebGUI now.")
        should_send_server_ready.value = True

        with serve(
            functools.partial(self.start_whisperspeech_tts, audio_queue=audio_queue), 
            host, port
            ) as server:
            server.serve_forever()

    def start_whisperspeech_tts(self, websocket, audio_queue=None):
        while True:
            llm_response = audio_queue.get()
            if audio_queue.qsize() != 0:
                continue

            # check if this websocket exists
            try:
                websocket.ping()
            except Exception as e:
                del websocket
                audio_queue.put(llm_response)
                break
            
