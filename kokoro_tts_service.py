import functools
import time
import logging
logging.basicConfig(level = logging.INFO)

from websockets.sync.server import serve

from kokoro import KPipeline

SAMPLE_RATE = 24000  # у Kokoro именно 24 кГц

class WhisperSpeechTTS:

    def initialize_model(self):
        self.pipeline = KPipeline(lang_code='a')
        self.last_llm_response = None

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
        self.eos = False
        self.output_audio = None

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
            
            llm_output = llm_response["llm_output"][0]
            self.eos = llm_response["eos"]

            def should_abort():
                if not audio_queue.empty(): raise TimeoutError()

            # only process if the output updated
            if self.last_llm_response != llm_output.strip():
                try:
                    start = time.time()
                    generator = self.pipeline(llm_output, voice="af_heart")
                    inference_time = time.time() - start
                    logging.info(f"[WhisperSpeech INFO:] TTS inference done in {inference_time} ms.\n\n")

                    for result in generator:
                        logging.debug(result.phonemes)
                        if result.audio is None:
                            continue
                        output_audio = result.audio.cpu().numpy()

                        if output_audio is not None:
                            try:
                                websocket.send(output_audio.tobytes())
                            except Exception as e:
                                logging.error(f"[WhisperSpeech ERROR:] Audio error: {e}")

                    self.last_llm_response = llm_output.strip()
                except TimeoutError as te:
                    logging.error(f"[WhisperSpeech timeout ERROR:] error: {te}")
                    pass
