import os
import sys
import wave
import ctypes
import pyaudio
import keyboard
import speech_recognition as sr
import google.generativeai as genai
from PIL import Image
import pystray
from pystray import MenuItem as item
import win32console, win32gui
from gtts import gTTS
import playsound

# Constantes
FILE_API = "Assistente/api_key.txt"
FILDE_AUDIO = "Assistente/Audio/"
NOME_ARQUIVO = "audio.wav"
FORMATO = pyaudio.paInt16
CANAIS = 1
TAXA_AMOSTRAGEM = 44100
DURACAO = 5
NOME_ARQUIVO_RESPOSTA = "resposta.mp3"

# Ocultar o console do Windows
win32gui.ShowWindow(win32console.GetConsoleWindow(), 0)

# Função para ler a chave da API a partir de um arquivo de texto
def get_api_key():
    try:
        with open(FILE_API, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        sys.exit("Erro: Arquivo de chave API não encontrado.")

# Classe IA para interagir com a API Gemini
class IA:
    def __init__(self):
        self.api_key = get_api_key()
        genai.configure(api_key=self.api_key)
        self.modelo = 'models/gemini-1.5-flash'

    def gerar_texto(self, texto):
        try:
            modelo = genai.GenerativeModel(self.modelo)
            resposta = modelo.generate_content(texto)
            return resposta.text.replace('*', '')
        except Exception as e:
            return f"Ocorreu um erro: {e}"

# Função para criar ícone na bandeja do sistema
def quit_program(icon, item):
    icon.stop()
    sys.exit()

def setup_tray_icon():
    icon_image = Image.new('RGB', (64, 64), color=(255, 0, 0))
    menu = (item('Sair', quit_program),)
    tray_icon = pystray.Icon("AudioRecorder", icon_image, menu=menu)
    tray_icon.run_detached()

# Função para gravar áudio
def gravar_audio():
    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(format=FORMATO, channels=CANAIS, rate=TAXA_AMOSTRAGEM, input=True, frames_per_buffer=1024)
    except Exception as e:
        sys.exit(f"Erro ao acessar o microfone: {e}")
    
    print("Gravando áudio...")
    frames = [stream.read(1024) for _ in range(0, int(TAXA_AMOSTRAGEM / 1024 * DURACAO))]
    print("Áudio gravado com sucesso!")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    if not os.path.exists(FILDE_AUDIO):
        os.makedirs(FILDE_AUDIO)

    arquivo_path = os.path.join(FILDE_AUDIO, NOME_ARQUIVO)
    with wave.open(arquivo_path, 'wb') as arquivo:
        arquivo.setnchannels(CANAIS)
        arquivo.setsampwidth(audio.get_sample_size(FORMATO))
        arquivo.setframerate(TAXA_AMOSTRAGEM)
        arquivo.writeframes(b''.join(frames))

# Função para converter áudio para texto
def converter_audio():
    arquivo_path = os.path.join(FILDE_AUDIO, NOME_ARQUIVO)
    if not os.path.exists(arquivo_path):
        print("Arquivo de áudio não encontrado!")
        return ""
    
    reconhecedor = sr.Recognizer()
    with sr.AudioFile(arquivo_path) as source:
        audio = reconhecedor.record(source)
    
    try:
        return reconhecedor.recognize_google(audio, language='pt-BR')
    except sr.UnknownValueError:
        return "Não entendi o que você disse"
    except sr.RequestError as e:
        return f"Erro ao solicitar reconhecimento de áudio: {e}"

# Função para converter texto usando a IA
def converter_texto(texto):
    ia = IA()
    return ia.gerar_texto(texto)

# Função para converter texto em áudio e reproduzir
def texto_para_audio(texto):
    try:
        tts = gTTS(texto, lang='pt')
        resposta_path = os.path.join(FILDE_AUDIO, NOME_ARQUIVO_RESPOSTA)
        # Remove o arquivo mp3 se ele já existir para evitar erro de permissão
        if os.path.exists(resposta_path):
            os.remove(resposta_path)
        tts.save(resposta_path)
        playsound.playsound(resposta_path)
    except Exception as e:
        print(f"Erro ao converter texto em áudio: {e}")

# Função principal
def main():
    setup_tray_icon()
    while True:
        if keyboard.is_pressed('ctrl+shift+g'):
            gravar_audio()
            texto_convertido = converter_audio()
            print(f"Texto convertido: {texto_convertido}")
            if texto_convertido:
                resposta_ia = converter_texto(texto_convertido)
                print(f"IA: {resposta_ia}")
                texto_para_audio(resposta_ia)
            while keyboard.is_pressed('ctrl+shift+g'):
                pass

if __name__ == "__main__":
    main()
