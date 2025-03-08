import streamlit as st
import os
import openai
import requests
# from utils_openai import retorna_resposta_modelo
from pages.utils_files import *
from dotenv import load_dotenv
from fake_useragent import UserAgent
from langchain_community.document_loaders import (
    YoutubeLoader, CSVLoader, PyPDFLoader, TextLoader)
from fake_useragent import UserAgent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from time import sleep
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Carrega arquivo .env
load_dotenv('.env')
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# print('hello', os.getenv('OPENAI_API_KEY'))

# Obtém o diretório onde os arquivos estão salvos
DIRETORIO_ARQUIVOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "arquivos")

# Nome do arquivo onde as URLs serão salvas
ARQUIVO_URLS = os.path.join(DIRETORIO_ARQUIVOS, "urls.txt")

# Define o tamanho dos chunks de texto
CHUNK_SIZE = 2000  # Aproximadamente 2000 caracteres por trecho
CHUNK_OVERLAP = 200  # Sobreposição para manter contexto entre partes

# =================================================================
# INICIALIZAÇÃO
# =================================================================


def inicializacao():
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    if 'conversa_atual' not in st.session_state:
        st.session_state.conversa_atual = ''
    if 'conteudo_arquivos' not in st.session_state or not st.session_state['conteudo_arquivos']:
        # Carrega arquivos apenas uma vez e evita armazenar None
        conteudo = atualizar_agente()
        if conteudo:  # Garante que algo foi retornado antes de armazenar
            st.session_state.conteudo_arquivos = conteudo
        else:
            st.session_state.conteudo_arquivos = "Nenhum conteúdo relevante foi carregado."

# =================================================================
# SIDEBAR
# =================================================================


def sidebar():
    st.sidebar.button('➕ Nova conversa',
                      on_click=seleciona_conversa,
                      args=('', ),
                      use_container_width=True)
    st.sidebar.markdown('')

    # Lista as conversas anteriores já realizadas
    conversas = listar_conversas()
    for nome_arquivo in conversas:
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        st.sidebar.button(nome_mensagem,
                          on_click=seleciona_conversa,
                          args=(nome_arquivo, ),
                          disabled=nome_arquivo == st.session_state['conversa_atual'],
                          use_container_width=True)
    st.sidebar.markdown("Desenvolvido por [Repp]")


def seleciona_conversa(nome_arquivo):
    if nome_arquivo == '':
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo)
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo

# =================================================================
# CHAT
# =================================================================


def pagina_principal():
    # Definição do prompt do sistema para guiar as respostas da IA
    mensagem_sistema = {'role': 'system',
                        'content': 'Você é um assistente amigável e informativo chamado ReppChat. '
                        'Responda de forma clara, objetiva e profissional. '
                        'Sempre seja educado e incentive a interação do usuário.'}

    # Usa o conteúdo já armazenado na sessão
    conteudo_arquivos = st.session_state['conteudo_arquivos']

    # Verifica se o conteúdo foi carregado corretamente (para debug)
    # st.write("🔍 Debug: Conteúdo carregado dos arquivos:",
    #          conteudo_arquivos[:500])  # Exibe os primeiros 500 caracteres

    # Carrega mensagens e remove mensagens inválidas (com content = None)
    mensagens = [msg for msg in ler_mensagens(
        st.session_state['mensagens']) if msg.get('content')]

    # Adiciona a mensagem do sistema apenas se ainda não existir
    if not mensagens or mensagens[0]['role'] != 'system':
        mensagens.insert(0, mensagem_sistema)

    # Garante que as informações dos arquivos sejam sempre incluídas nas mensagens enviadas ao modelo
    # Evita estouro de tokens, mantendo apenas as últimas 10 interações
    mensagens = mensagens[:10]
    if conteudo_arquivos:
        mensagens.append({
            'role': 'system',
            # Limite para evitar tokens excessivos
            'content': f"Contexto adicional carregado dos arquivos:\n\n{conteudo_arquivos}"
        })

    st.header('🤖 Bem-vindo ao ReppChat 🤖', divider=True)

    # Exibe mensagens antigas (exceto a mensagem do sistema)
    for mensagem in mensagens:
        if mensagem['role'] != 'system':  # Não exibir a mensagem do sistema no chat
            chat = st.chat_message(mensagem['role'])
            chat.markdown(mensagem['content'])

    # Captura entrada do usuário
    prompt = st.chat_input('Fale com o chat')

    if prompt and prompt.strip():
        nova_mensagem = {'role': 'user', 'content': prompt.strip()}
        mensagens.append(nova_mensagem)

        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])

        # Cria mensagem do assistente
        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown("▌")

        # Obtem resposta do modelo
        resposta_completa = ''
        try:
            # Verifica exatamente o que está sendo enviado ao modelo
            # st.write("🔍 Debug: Mensagens enviadas ao modelo:", mensagens)
            respostas = retorna_resposta_modelo(mensagens,
                                                modelo='gpt-3.5-turbo',
                                                temperatura=0,
                                                stream=True)

            for resposta in respostas:
                if hasattr(resposta.choices[0].delta, "content") and resposta.choices[0].delta.content:
                    resposta_completa += resposta.choices[0].delta.content
                    placeholder.markdown(resposta_completa + "▌")

            # Exibe resposta final
            placeholder.markdown(resposta_completa)
            nova_mensagem = {'role': 'assistant',
                             'content': resposta_completa}
            mensagens.append(nova_mensagem)

        except Exception as err:
            st.error(f'Erro ao obter resposta: {str(err)}')

        # Salva mensagens na sessão e no armazenamento
        st.session_state['mensagens'] = mensagens
        salvar_mensagens(mensagens)

# Resume o texto para diminuir o numero de tokens


def retorna_resposta_modelo(mensagens, modelo='gpt-3.5-turbo', temperatura=0, stream=False):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model=modelo,
        messages=mensagens,
        temperature=temperatura,
        stream=stream
    )
    return response


def resumir_texto(texto):
    prompt_resumo = f"Resuma o seguinte conteúdo de forma clara e objetiva:\n\n{texto}"

    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt_resumo}],
        temperature=0.5,
        max_tokens=500  # Limita o tamanho do resumo
    )

    return resposta.choices[0].message.content if resposta.choices else "Erro ao gerar resumo."

# Atualiza o agente com as informações externas carregadas


def atualizar_agente():
    """Lê todos os arquivos PDF da pasta e extrai o conteúdo."""
    conteudo_extraido = []

    # Percorre todos os arquivos na pasta
    for nome_arquivo in os.listdir(DIRETORIO_ARQUIVOS):

        # Verifica se é um PDF
        if nome_arquivo.lower().endswith('.pdf'):
            conteudo_pdf = carrega_pdf(nome_arquivo)
            conteudo_extraido.append(
                f"### {nome_arquivo} ###\n{conteudo_pdf}")

        # Verifica se é um CSV
        elif nome_arquivo.lower().endswith('.csv'):
            conteudo_csv = carrega_csv(nome_arquivo)
            conteudo_extraido.append(
                f"### {nome_arquivo} ###\n{conteudo_csv}")

        # Se for TXT
        elif nome_arquivo.lower().endswith('.txt'):
            conteudo_txt = carrega_txt(nome_arquivo)
            conteudo_extraido.append(
                f"### {nome_arquivo} ###\n{conteudo_txt}")

    # Processar URLs (sites e YouTube)
    if os.path.exists(ARQUIVO_URLS):
        with open(ARQUIVO_URLS, "r", encoding="utf-8") as f:
            urls = f.readlines()

        for linha in urls:
            tipo, url = linha.strip().split(": ", 1)

            if tipo == "Site":
                conteudo_site = carrega_site(url)
                conteudo_extraido.append(
                    f"### Conteúdo do site {url} ###\n{conteudo_site}")

            elif tipo == "Youtube":
                conteudo_video = carrega_youtube(url)
                conteudo_extraido.append(
                    f"### Transcrição do vídeo {url} ###\n{conteudo_video}")

    return "\n\n".join(conteudo_extraido) if conteudo_extraido else "Nenhum documento carregado."

# =================================================================
# LOADERS
# =================================================================


def carrega_pdf(nome_arquivo):
    """Extrai arquivos PDF"""
    try:
        caminho_arquivo = os.path.join(DIRETORIO_ARQUIVOS, nome_arquivo)
        loader = PyPDFLoader(caminho_arquivo)
        lista_documentos = loader.load()
        documento = '\n\n'.join(
            [doc.page_content for doc in lista_documentos])

        # Divide o texto em partes menores
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = splitter.split_text(documento)

        # Resume cada chunk separadamente e limita para não sobrecarregar a API
        resumos = [resumir_texto(chunk) for chunk in chunks[:5]]
        texto_resumido = "\n\n".join(resumos)

        return texto_resumido

    except Exception as e:
        print(f"Erro ao carregar {nome_arquivo}: {e}")


def carrega_csv(nome_arquivo):
    try:
        caminho_arquivo = os.path.join(
            DIRETORIO_ARQUIVOS, nome_arquivo)  # Caminho completo
        loader = CSVLoader(caminho_arquivo)  # Passa o caminho correto
        lista_documentos = loader.load()
        documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
        return documento
    except Exception as e:
        print(f"Erro ao carregar {nome_arquivo}: {e}")


def carrega_txt(nome_arquivo):
    try:
        caminho_arquivo = os.path.join(
            DIRETORIO_ARQUIVOS, nome_arquivo)  # Caminho completo
        loader = TextLoader(caminho_arquivo)  # Passa o caminho correto
        lista_documentos = loader.load()
        documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
        return documento
    except Exception as e:
        print(f"Erro ao carregar {nome_arquivo}: {e}")


def carrega_youtube(video_id):
    """Extrai transcrição de vídeos do YouTube."""
    try:
        loader = YoutubeLoader(video_id, add_video_info=False, language=['pt'])
        lista_documentos = loader.load()
        return '\n\n'.join([doc.page_content for doc in lista_documentos])
    except Exception as e:
        return f"Erro ao carregar vídeo {video_id}: {str(e)}"


def carrega_site(url):
    """Realiza scrap de conteúdo de sites, incluindo suporte para Sitemap XML."""
    documento = ""

    # Verifica se é um Sitemap XML
    if url.endswith(".xml"):
        return carrega_site_com_sitemap(url)

    # Scrap normal de uma única página
    for i in range(3):  # Tenta até 3 vezes
        try:
            os.environ['USER_AGENT'] = UserAgent().random
            headers = {"User-Agent": os.environ['USER_AGENT']}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            documento = soup.get_text()
            break  # Sai do loop se o carregamento for bem-sucedido

        except Exception as e:
            print(f'Erro ao carregar o site {url} ({i+1}/3): {e}')
            sleep(3)  # Espera antes de tentar novamente

    return documento if documento else f"Erro ao carregar site: {url}"


def carrega_site_com_sitemap(url_sitemap, limite_paginas=10):
    """Lê um Sitemap XML e faz scrap das páginas listadas nele."""
    urls = obter_urls_sitemap(url_sitemap)
    if not urls:
        return f"Erro: Nenhuma URL encontrada no Sitemap {url_sitemap}."

    conteudo_total = []

    for i, url in enumerate(urls[:limite_paginas]):  # Limita o número de páginas
        print(f"Carregando página {i+1}/{limite_paginas}: {url}")
        conteudo_pagina = carrega_site(url)
        conteudo_total.append(
            f"### Conteúdo da página {url} ###\n{conteudo_pagina}")

    return "\n\n".join(conteudo_total) if conteudo_total else "Nenhum conteúdo extraído."


def obter_urls_sitemap(url_sitemap):
    """Obtém todas as URLs listadas no Sitemap XML."""
    headers = {"User-Agent": UserAgent().random}
    try:
        response = requests.get(url_sitemap, headers=headers, timeout=10)
        response.raise_for_status()

        # Analisa o XML e extrai as URLs
        root = ET.fromstring(response.content)
        urls = [elem.text for elem in root.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        return urls

    except Exception as e:
        print(f"Erro ao carregar o Sitemap {url_sitemap}: {e}")
        return []


# =================================================================
# MAIN
# =================================================================
def main():
    inicializacao()
    sidebar()
    pagina_principal()


if __name__ == '__main__':
    main()
