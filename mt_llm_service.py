import time
import json
from pathlib import Path
from typing import Optional

import logging
logging.basicConfig(level = logging.INFO)

import torch
from transformers import MarianMTModel, MarianTokenizer

MODEL_NAME = "Helsinki-NLP/opus-mt-ru-en"


class TensorRTLLMEngine:
    def __init__(self):
        self.model_name = MODEL_NAME
        self.target_language = 'en'
        self.last_prompt = None

    def load_translation_model(self):
        """Load the translation model and tokenizer."""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logging.info(f"Loading translation model on device: {self.device}")

            self.translation_model = MarianMTModel.from_pretrained(
                self.model_name
            ).to(self.device)
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)

            self.model_loaded = True
            logging.info(f"Translation model loaded successfully. Target language: {self.target_language}")
        except Exception as e:
            logging.error(f"Failed to load translation model: {e}")
            self.translation_model = None
            self.tokenizer = None
            self.model_loaded = False

    def translate_text(self, text: str) -> str:
        """
        Translate a single text segment.

        Args:
            text (str): Text to translate

        Returns:
            str: Translated text or original text if translation fails
        """
        if not self.model_loaded or not text.strip():
            return text

        try:
            # Encode input and move to device
            encoded_input = self.tokenizer(text, return_tensors="pt").to(self.device)

            # Generate translation
            with torch.no_grad():
                generated_tokens = self.translation_model.generate(**encoded_input)

            # Decode output
            output = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            return output if output else text

        except Exception as e:
            logging.error(f"Translation failed for text '{text}': {e}")
            return text


    def run(
        self,
        model_path,
        tokenizer_path,
        phi_model_type=None,
        transcription_queue=None,
        llm_queue=None,
        audio_queue=None,
        input_text=None, 
        max_output_len=100, 
        max_attention_window_size=4096, 
        num_beams=1, 
        streaming=False,
        streaming_interval=4,
        debug=False,
    ):  
        self.load_translation_model()
        
        logging.info("[LLM INFO:] Loaded LLM TensorRT Engine.")

        conversation_history = {}

        while True:

            # Get the last transcription output from the queue
            transcription_output = transcription_queue.get()
            if transcription_queue.qsize() != 0:
                continue
            
            if transcription_output["uid"] not in conversation_history:
                conversation_history[transcription_output["uid"]] = []

            prompt = transcription_output['prompt'].strip()
                                
            # if prompt is same but EOS is True, we need that to send outputs to websockets
            '''
            if self.last_prompt == prompt:
                if self.last_output is not None and transcription_output["eos"]:
                    self.eos = transcription_output["eos"]
                    llm_queue.put({
                        "uid": transcription_output["uid"],
                        "llm_output": self.last_output,
                        "eos": self.eos,
                        "latency": self.infer_time
                    })
                    audio_queue.put({"llm_output": self.last_output, "eos": self.eos})
                    conversation_history[transcription_output["uid"]].append(
                        (transcription_output['prompt'].strip(), self.last_output[0].strip())
                    )
                    continue
            '''

            input_text = prompt
            self.eos = transcription_output["eos"]

            logging.info(f"[LLM INFO:] Running LLM Inference with WhisperLive prompt: {prompt}, eos: {self.eos}")
            start = time.time()
            with torch.no_grad():
                output = self.translate_text(input_text)
                #torch.cuda.synchronize()

            self.infer_time = time.time() - start
            
            # if self.eos:
            if output is not None:
                self.last_output = output
                self.last_prompt = prompt
                llm_queue.put({
                    "uid": transcription_output["uid"],
                    "llm_output": output,
                    "eos": self.eos,
                    "latency": self.infer_time
                })
                audio_queue.put({"llm_output": output, "eos": self.eos})
                logging.info(f"[LLM INFO:] Output: {output[0]}\nLLM inference done in {self.infer_time} ms\n\n")
            
            if self.eos:
                conversation_history[transcription_output["uid"]].append(
                    (transcription_output['prompt'].strip(), output[0].strip())
                )
                self.last_prompt = None
                self.last_output = None
