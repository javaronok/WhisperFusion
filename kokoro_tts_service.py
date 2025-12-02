import time
import json
import base64
import logging
logging.basicConfig(level=logging.INFO)

import threading
from websockets.sync.server import serve

from kokoro import KPipeline

SAMPLE_RATE = 24000  # у Kokoro именно 24 кГц

class WhisperSpeechTTS:

    def initialize_model(self):
        self.pipeline = KPipeline(lang_code='a')
        self.last_llm_response = None

        # Хранилище всех активных websocket-соединений
        self.connected_clients = set()
        self.lock = threading.Lock()  # Для безопасного доступа к списку клиентов

    def run(self, host, port, audio_queue=None, should_send_server_ready=None):
        self.initialize_model()

        # Запускаем поток, который будет читать очередь и генерировать аудио
        # daemon=True гарантирует, что поток закроется при остановке основного приложения
        process_thread = threading.Thread(
            target=self.broadcast_audio_loop,
            args=(audio_queue,),
            daemon=True
        )
        process_thread.start()

        logging.info("[WhisperSpeech INFO:] Warmed up Whisper Speech torch compile model. Connect to the WebGUI now.")
        should_send_server_ready.value = True

        # Запускаем сервер, который теперь только управляет подключениями
        with serve(
            self.handle_client_connection,
            host, port
            ) as server:
            server.serve_forever()

    def handle_client_connection(self, websocket):
        """
        Этот метод вызывается для каждого нового подключения.
        Его задача — зарегистрировать клиента и держать соединение открытым.
        """
        with self.lock:
            self.connected_clients.add(websocket)

        logging.info(f"[WhisperSpeech INFO:] New client connected. Total clients: {len(self.connected_clients)}")

        try:
            # Держим соединение открытым.
            # Читаем входящие сообщения (даже если они нам не нужны), чтобы ловить дисконнект.
            for message in websocket:
                pass  # Игнорируем входящие сообщения от клиента, нам нужно только отправлять
        except Exception:
            pass
        finally:
            with self.lock:
                self.connected_clients.remove(websocket)
            logging.info(f"[WhisperSpeech INFO:] Client disconnected. Total clients: {len(self.connected_clients)}")

    def broadcast_audio_loop(self, audio_queue):
        """
        Фоновый процесс: читает LLM ответ -> генерирует аудио -> рассылает ВСЕМ.
        """
        self.eos = False

        while True:
            # 1. Получаем данные из очереди (блокирующая операция)
            llm_response = audio_queue.get()

            # Оптимизация очереди (как в оригинале)
            if audio_queue.qsize() != 0:
                continue

            llm_output = llm_response["llm_output"][0]
            self.eos = llm_response["eos"]

            # Если нет клиентов, мы все равно генерируем или пропускаем?
            # Лучше пропустить отправку, но логику генерации можно оставить, если нужно греть кеш,
            # но для экономии ресурсов можно проверить:
            # if not self.connected_clients: continue

            # only process if the output updated
            if self.last_llm_response != llm_output.strip():
                try:
                    start = time.time()
                    # ГЕНЕРАЦИЯ АУДИО (Тяжелая операция выполняется 1 раз)
                    generator = self.pipeline(llm_output, voice="af_heart")
                    inference_time = time.time() - start
                    logging.info(f"[WhisperSpeech INFO:] TTS inference done in {inference_time} ms.\n\n")

                    for result in generator:
                        logging.debug(result.phonemes)
                        if result.audio is None:
                            continue

                        output_audio = result.audio.cpu().numpy()

                        if output_audio is not None:
                            audio_bytes = output_audio.tobytes()

                            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                            message = {
                                "type": "tts",
                                "content": llm_output,
                                "audio": audio_base64
                            }

                            # рассылка всем подключённым клиентам
                            with self.lock:
                                # Копируем список, чтобы не сломать итерацию при удалении клиента
                                active_clients = list(self.connected_clients)

                            for client in active_clients:
                                try:
                                    client.send(json.dumps(message))
                                except Exception as e:
                                    logging.error(f"[WhisperSpeech ERROR:] Send error: {e}")
                                    # Удаление клиента произойдет в handle_client_connection автоматически при разрыве

                    self.last_llm_response = llm_output.strip()

                except TimeoutError as te:
                    logging.error(f"[WhisperSpeech timeout ERROR:] error: {te}")
                    pass
                except Exception as e:
                    logging.error(f"[WhisperSpeech General ERROR:] {e}")
