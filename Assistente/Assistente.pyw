import os
import sys
import pyaudio
import wave
import keyboard
import google.generativeai as genai
import win32console, win32gui
import time
import logging
from threading import Thread, Lock
import speech_recognition as sr
from gtts import gTTS
import pygame

# Constantes de Configuração
FILE_API = "Assistente/api_key.txt"
AUDIO_DIR = "Assistente/Audio/"
AUDIO_FILENAME = "audio.wav"
RESPONSE_AUDIO_FILENAME = "resposta.mp3"
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
CHUNK = 1024  # Tamanho do buffer para a gravação
DEBOUNCE_INTERVAL = 2  # Intervalo de debounce para o atalho em segundos

# Configuração do Log
logging.basicConfig(
    filename='assistente.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Corrige os problemas de codificação no log
)

# Ocultar o console do Windows
win32gui.ShowWindow(win32console.GetConsoleWindow(), 0)

class IA:
    """Classe para interagir com a API Gemini."""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.model = 'models/gemini-1.5-flash'
        genai.configure(api_key=self.api_key)

    def _get_api_key(self):
        try:
            with open(FILE_API, "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            logging.error("Erro: Arquivo de chave API não encontrado.")
            sys.exit("Erro: Arquivo de chave API não encontrado.")

    def generate_response(self, text):
        if not text.strip():
            logging.error("Erro: O conteúdo para geração de resposta está vazio.")
            return "Nenhuma entrada de áudio foi capturada."
        
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(text)
            return response.text.replace('*', '')
        except Exception as e:
            logging.error(f"Erro na geração de resposta: {e}")
            return "Ocorreu um erro ao gerar a resposta."

class Assistente:
    """Classe principal para o assistente virtual."""
    
    def __init__(self):
        self.ia = IA()
        self.audio_em_texto = AudioEmTexto()
        self.texto_em_audio = TextoEmAudio()
        
        # Inicializar o mixer uma vez no início do Assistente
        pygame.mixer.init()
        
        # Criar diretório de áudio, se não existir
        os.makedirs(AUDIO_DIR, exist_ok=True)
    
    def iniciar(self):
        logging.info("Assistente virtual iniciado.")
        while True:
            # Iniciar gravação quando o atalho é pressionado
            if keyboard.is_pressed("ctrl+alt+a"):
                Thread(target=self.processo_assistente).start()
                
            # Esperar um curto período antes de verificar o atalho novamente
            time.sleep(0.1)

    def processo_assistente(self):
        # Inicia a gravação e aguarda o áudio capturado
        if self.audio_em_texto.record_audio():
            text = self.audio_em_texto.audio_to_text()
            logging.info(f"Entrada de áudio capturada: {text}")
            response = self.ia.generate_response(text)
            logging.info(f"Resposta gerada: {response}")
            self.texto_em_audio.text_to_audio(response)

class TextoEmAudio:
    """Classe para converter texto em áudio."""
    
    def __init__(self):
        self.lock = Lock()

    def text_to_audio(self, text):
        with self.lock:
            tts = gTTS(text=text, lang='pt')
            response_path = os.path.join(AUDIO_DIR, RESPONSE_AUDIO_FILENAME)
            
            try:
                if os.path.exists(response_path):
                    os.remove(response_path)
            except PermissionError:
                logging.error("Erro: O arquivo de áudio está em uso e não pode ser removido.")
                return
            
            tts.save(response_path)

            # Reproduz o áudio e aguarda até que termine
            pygame.mixer.music.load(response_path)
            pygame.mixer.music.play()

            # Aguarda até que o áudio termine de tocar
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.stop()  # Parar a música ao final

class AudioEmTexto:
    """Classe para converter áudio em texto e gravar enquanto o atalho estiver pressionado."""
    
    def __init__(self):
        self.lock = Lock()
        self.is_recording = False

    def record_audio(self):
        with self.lock:
            self.is_recording = True
            audio_frames = []
            p = pyaudio.PyAudio()
            stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK)

            print("Gravando...")

            while keyboard.is_pressed("ctrl+alt+a"):
                data = stream.read(CHUNK)
                audio_frames.append(data)

            # Encerrar a gravação quando o atalho for liberado
            print("Gravação finalizada.")
            stream.stop_stream()
            stream.close()
            p.terminate()

            audio_path = os.path.join(AUDIO_DIR, AUDIO_FILENAME)
            
            # Salvar o áudio gravado no arquivo
            wf = wave.open(audio_path, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(AUDIO_FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(audio_frames))
            wf.close()

            return True
    
    def audio_to_text(self):
        with self.lock:
            recognizer = sr.Recognizer()
            audio_path = os.path.join(AUDIO_DIR, AUDIO_FILENAME)
            
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio, language="pt-BR")
            except sr.UnknownValueError:
                text = ""
            
            return text

def main():
    assistente = Assistente()
    assistente.iniciar()

if __name__ == "__main__":
    main()
