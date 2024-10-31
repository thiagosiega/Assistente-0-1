import os
import tkinter as tk
from tkinter import scrolledtext, ttk
import google.generativeai as genai
import logging
import sys

# Configuração do Log
logging.basicConfig(
    filename='assistente.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class IA:
    """Classe para interagir com a API Gemini."""
    
    def __init__(self, model='models/gemini-1.5-flash'):
        self.FILE_API = "Assistente/api_key.txt"
        self.api_key = self._get_api_key()
        self.model = model
        genai.configure(api_key=self.api_key)

    def _get_api_key(self):
        try:
            with open(self.FILE_API, "r") as file:
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

class AssistenteGUI:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title('Assistente')
        self.janela.geometry('1000x600')  # Ajuste para acomodar a barra lateral

        self.modelos_disponiveis = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro']
        self.modelo_selecionado = tk.StringVar(value=self.modelos_disponiveis[0])

        self.ia = IA(model=self.modelo_selecionado.get())  # Instancia a classe IA com o modelo inicial

        # Diretório e arquivo de histórico
        self.historico_dir = "historico_conversas"
        os.makedirs(self.historico_dir, exist_ok=True)
        self.historico_path = os.path.join(self.historico_dir, "conversa.txt")

        # Lista para manter o histórico completo na memória
        self.historico_completo = []

        # Frame para o histórico de conversas (barra lateral)
        self.frame_historico = tk.Frame(self.janela, width=200, bg="lightgray")
        self.frame_historico.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_historico.pack_propagate(False)

        # Título do histórico de conversas
        self.label_historico = tk.Label(self.frame_historico, text="Históricos Salvos", font=('Helvetica', 14), bg="lightgray")
        self.label_historico.pack(pady=10)

        # Área de rolagem para botões de históricos de conversa
        self.scroll_area = scrolledtext.ScrolledText(self.frame_historico, wrap=tk.WORD, width=25, height=25, font=('Helvetica', 10))
        self.scroll_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.scroll_area.config(state=tk.DISABLED)  # Impede edição direta

        # Carregar botões para os arquivos de conversa
        self.carregar_botoes_historico()

        # Frame para o título
        self.frame_titulo = tk.Frame(self.janela)
        self.frame_titulo.pack(pady=10)

        # Título principal da aplicação
        self.label = tk.Label(self.frame_titulo, text='Assistente', font=('Helvetica', 16))
        self.label.pack()

        # Menu de seleção do modelo
        self.frame_modelo = tk.Frame(self.janela)
        self.frame_modelo.pack(pady=5)
        self.label_modelo = tk.Label(self.frame_modelo, text="Escolha o modelo:", font=('Helvetica', 12))
        self.label_modelo.pack(side=tk.LEFT, padx=5)
        self.menu_modelo = ttk.OptionMenu(self.frame_modelo, self.modelo_selecionado, *self.modelos_disponiveis, command=self.atualizar_modelo)
        self.menu_modelo.pack(side=tk.LEFT)

        # Área de texto para exibir as respostas do assistente
        self.texto_exibicao = scrolledtext.ScrolledText(self.janela, wrap=tk.WORD, width=85, height=25, font=('Helvetica', 12))
        self.texto_exibicao.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Frame na parte inferior para entrada de texto e botões
        self.frame_inferior = tk.Frame(self.janela)
        self.frame_inferior.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Entrada de texto para enviar perguntas/comandos
        self.entry = tk.Entry(self.frame_inferior, width=50)
        self.entry.pack(side=tk.LEFT, padx=10)

        # Botão Enviar
        self.botao_enviar = tk.Button(self.frame_inferior, text="Enviar", command=self.enviar)
        self.botao_enviar.pack(side=tk.LEFT, padx=5)

        # Botões adicionais
        self.botao_salvar = tk.Button(self.frame_inferior, text="Salvar Conversa", command=self.salvar_conversa)
        self.botao_salvar.pack(side=tk.RIGHT, padx=10)

        self.botao_limpar = tk.Button(self.frame_inferior, text="Limpar Histórico", command=self.limpar_historico)
        self.botao_limpar.pack(side=tk.RIGHT, padx=10)

        self.botao_nova_conversa = tk.Button(self.frame_inferior, text="Nova Conversa", command=self.nova_conversa)
        self.botao_nova_conversa.pack(side=tk.RIGHT, padx=10)

    def nova_conversa(self):
        self.historico_completo = []
        self.texto_exibicao.delete(1.0, tk.END)
        self.historico_path = os.path.join(self.historico_dir, f"conversa_{len(os.listdir(self.historico_dir)) + 1}.txt")
        self.salvar_conversa("Nova conversa iniciada.\n")

    def limpar_historico(self):
        self.historico_completo = []
        self.texto_exibicao.delete(1.0, tk.END)
        
    def carregar_botoes_historico(self):
        # Limpa os botões anteriores na área de rolagem e insere novos botões
        self.scroll_area.config(state=tk.NORMAL)
        self.scroll_area.delete(1.0, tk.END)

        arquivos = os.listdir(self.historico_dir)
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(self.historico_dir, arquivo)
            botao = tk.Button(self.scroll_area, text=arquivo, command=lambda p=caminho_arquivo: self.carregar_conversa(p))
            self.scroll_area.window_create("end", window=botao)
            self.scroll_area.insert("end", "\n")
        
        self.scroll_area.config(state=tk.DISABLED)  # Desativa edição

    def carregar_conversa(self, caminho_arquivo):
        self.texto_exibicao.delete(1.0, tk.END)
        with open(caminho_arquivo, 'r', encoding="utf-8") as file:
            conteudo = file.read()
            self.texto_exibicao.insert(tk.END, conteudo)

    def atualizar_modelo(self, modelo):
        self.ia.model = modelo

    def enviar(self):
        texto = self.entry.get()
        if texto.strip():
            self.historico_completo.append(f"Você: {texto}")
            contexto = "\n".join(self.historico_completo) + f"\nAssistente:"
            resposta = self.ia.generate_response(contexto)
            self.historico_completo.append(f"Assistente: {resposta}")

            self.exibir_resposta(f"Você disse: {texto}\n", "green")
            self.exibir_resposta(f"Assistente: {resposta}\n", "purple")
            
            self.carregar_botoes_historico()
            self.salvar_conversa(f"Você: {texto}\nAssistente: {resposta}\n")
            self.entry.delete(0, tk.END)
        else:
            self.exibir_resposta("Nenhuma entrada fornecida.\n", "red")

    def exibir_resposta(self, resposta, cor="black"):
        self.texto_exibicao.insert(tk.END, resposta, cor)
        self.texto_exibicao.insert(tk.END, "\n")
        self.texto_exibicao.see(tk.END)
        self.texto_exibicao.tag_configure(cor, foreground=cor)

    def salvar_conversa(self, texto):
        with open(self.historico_path, "a", encoding="utf-8") as file:
            file.write(texto)
            file.write("\n")

if __name__ == '__main__':
    janela = tk.Tk()
    AssistenteGUI(janela)
    janela.mainloop()
