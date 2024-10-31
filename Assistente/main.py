import os
import tkinter as tk
from tkinter import messagebox
import win32gui
import win32console

# Ocultar o console do Windows
win32gui.ShowWindow(win32console.GetConsoleWindow(), 0)

FILE_DEPENDENCIAS = "Assistente/requirements.txt"
FILE_API = "Assistente/api_key.txt"
API_LINK = "https://aistudio.google.com/app/apikey"

# Ler a chave da API a partir de um arquivo de texto
def get_api_key():
    try:
        with open(FILE_API, "r") as file:
            if (api_key := file.read().strip()) == "SUA-API-GOOGLE":
                mostrar_erro_api()
                return None
            return api_key
    except FileNotFoundError:
        mostrar_erro_api()
        return None

# Função para exibir uma mensagem de erro com um botão "Copiar"
def mostrar_erro_api():
    # Função para copiar o link e fechar a janela
    def copiar_link():
        root.clipboard_clear()
        root.clipboard_append(API_LINK)
        root.update()  # Necessário para garantir que a área de transferência seja atualizada

    # Função para abrir o arquivo api_key.txt para edição
    def abrir_txt():
        os.system("notepad Assistente/api_key.txt")

    # Função para verificar novamente o arquivo api_key.txt
    def verificar_arquivo():
        root.destroy()
        main()

    # Configurar a janela de erro com o botão de cópia
    root = tk.Tk()
    root.title("Erro")
    root.geometry("300x150")
    root.resizable(False, False)

    # Mensagem e botões de ação
    label = tk.Label(root, text="Por favor, insira a chave da API no arquivo api_key.txt.")
    label.pack(pady=5)
    
    btn_copiar = tk.Button(root, text="Copiar link", command=copiar_link)
    btn_copiar.pack(pady=5)

    btn_abrir = tk.Button(root, text="Abrir arquivo", command=abrir_txt)
    btn_abrir.pack(pady=5)

    btn_atualizado = tk.Button(root, text="Já atualizei", command=verificar_arquivo)
    btn_atualizado.pack(pady=5)
    
    root.mainloop()

# Função para instalar as dependências do Assistente
def instalar_dependencias():
    File = "Assistente/Sistema.txt"
    if os.path.exists(File):
        return "Bibliotecas já instaladas"
    try:
        os.system(f"pip install -r {FILE_DEPENDENCIAS}")
        with open(File, "w") as file:
            file.write("Bibliotecas instaladas")
        return "Dependências instaladas com sucesso."
    except FileNotFoundError:
        return "Arquivo de dependências não encontrado."
    except Exception as e:
        return f"Ocorreu um erro ao instalar as dependências: {e}"

# Função para executar o Assistente
def executar_assistente():
    respostra = messagebox.askyesno("Assistente", "Modo sem janela?")
    if respostra:
        try:
            os.system("python Assistente/Assistente.pyw")
        except Exception as e:
            return f"Ocorreu um erro ao executar o Assistente: {e}"
        return
    else:
        try:
            os.system("python Assistente/Assistente_GUI.py")
        except Exception as e:
            return f"Ocorreu um erro ao executar o Assistente: {e}"
        return

# Função principal
def main():
    api_key = get_api_key()
    if api_key is None or api_key == "SUA-API-GOOGLE":
        return
    print("Instalando dependências...")
    print(instalar_dependencias())
    print("Executando Assistente...")
    executar_assistente()

if __name__ == "__main__":
    main()
