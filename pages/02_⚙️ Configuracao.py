import streamlit as st
import os
from loaders import *
import pandas as pd
from langchain.document_loaders import PyPDFLoader


TIPOS_ARQUIVOS_VALIDOS = ['Site', 'Youtube', 'PDF', 'CSV', 'TXT']

# Obtém o diretório onde os arquivos estão salvos
DIRETORIO_ARQUIVOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "arquivos")

# Cria a pasta 'arquivos' caso não exista
os.makedirs(DIRETORIO_ARQUIVOS, exist_ok=True)

# Nome do arquivo onde as URLs serão salvas
ARQUIVO_URLS = os.path.join(DIRETORIO_ARQUIVOS, "urls.txt")

# Lista para armazenar os conteúdos dos arquivos e das URLs
conteudos = []


def sidebar():
    # Apenas leitura do valor do selectbox, sem tentar modificar `st.session_state` diretamente.
    tipo_arquivo = st.selectbox(
        'Selecione o tipo de arquivo', TIPOS_ARQUIVOS_VALIDOS, key='tipo_arquivo')

    # Ajustando o input conforme o tipo de arquivo selecionado
    if tipo_arquivo in ['Site']:
        st.text_input(f'Digite a URL do {tipo_arquivo}', key='arquivo')
    elif tipo_arquivo in ['Youtube']:
        st.text_input(f'Digite a ID do {tipo_arquivo}', key='arquivo')
    else:
        st.file_uploader('Faça aqui o upload do arquivo', type=[
                         tipo_arquivo.lower()], key='arquivo')

    st.button('Carregar arquivo', on_click=carrega_arquivo)
    st.button('Listar arquivos', on_click=listar_arquivos)
    st.markdown("Desenvolvido por [Repp]")


def carrega_arquivo():
    tipo_arquivo = st.session_state.get('tipo_arquivo')
    arquivo = st.session_state.get('arquivo')

    if not tipo_arquivo:
        st.error("Por favor, selecione um tipo de arquivo.")
        return

    if tipo_arquivo in ['Site']:
        if not arquivo:
            st.error("Por favor, insira a URL.")
            return
            # Salva a URL em um arquivo TXT
        with open(ARQUIVO_URLS, "a", encoding="utf-8") as f:
            f.write(f"{tipo_arquivo}: {arquivo}\n")
        st.success(f"{tipo_arquivo} salvo com sucesso!")

    if tipo_arquivo in ['Youtube']:
        if not arquivo:
            st.error("Por favor, insira a ID do vídeo.")
            return
        # Salva a URL em um arquivo TXT
        with open(ARQUIVO_URLS, "a", encoding="utf-8") as f:
            f.write(f"{tipo_arquivo}: {arquivo}\n")
        st.success(f"{tipo_arquivo} salvo com sucesso!")

    elif tipo_arquivo in ['PDF', 'CSV', 'TXT']:
        if arquivo is None:
            st.error("Por favor, faça o upload de um arquivo.")
            return

        # Obtém o nome original do arquivo
        nome_arquivo_original = arquivo.name
        # Define o caminho para salvar o arquivo
        caminho_arquivo = os.path.join(
            DIRETORIO_ARQUIVOS, nome_arquivo_original)

        # Salva o arquivo na raiz do projeto
        with open(caminho_arquivo, "wb") as f:
            f.write(arquivo.read())

        st.success(f"Arquivo {tipo_arquivo} salvo em {caminho_arquivo}!")


def listar_arquivos():
    # Lista os arquivos na pasta
    arquivos = os.listdir(DIRETORIO_ARQUIVOS)

    # Exclui o arquivo urls.txt da lista
    arquivos_filtrados = [f for f in arquivos if f != "urls.txt" and f.endswith(tuple(
        [t.lower() for t in TIPOS_ARQUIVOS_VALIDOS if t not in ['Site', 'Youtube']]))]

    # Lista para armazenar os dados
    dados_arquivos = []

    # Adiciona arquivos físicos ao DataFrame
    for arquivo in arquivos_filtrados:
        caminho = os.path.join(DIRETORIO_ARQUIVOS, arquivo)
        tamanho_kb = os.path.getsize(caminho) / 1024  # Converte para KB
        dados_arquivos.append(
            {"Nome": arquivo, "Tamanho (KB)": round(tamanho_kb, 2), "Tipo": "Arquivo"})

    # Adiciona as URLs salvas no arquivo de texto
    if os.path.exists(ARQUIVO_URLS):
        with open(ARQUIVO_URLS, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        for linha in linhas:
            if linha.strip():
                tipo, url = linha.split(": ", 1)
                dados_arquivos.append(
                    {"Nome": url.strip(), "Tamanho (KB)": "-", "Tipo": tipo})

    # Cria um DataFrame e exibe
    return pd.DataFrame(dados_arquivos)


def excluir_arquivos(selecionados):
    arquivos = os.listdir(DIRETORIO_ARQUIVOS)
    if os.path.exists(ARQUIVO_URLS):
        with open(ARQUIVO_URLS, "r", encoding="utf-8") as f:
            linhas = f.readlines()

    novas_linhas = []

    for item in selecionados:
        caminho = os.path.join(DIRETORIO_ARQUIVOS, item)
        if item in arquivos:
            os.remove(caminho)
        else:
            novas_linhas = [linha for linha in linhas if item not in linha]

    with open(ARQUIVO_URLS, "w", encoding="utf-8") as f:
        f.writelines(novas_linhas)

    st.success("Arquivos/URLs excluídos com sucesso!")


st.title("Gerenciador de Arquivos e URLs")
df = listar_arquivos()

if not df.empty:
    selecionados = st.multiselect(
        "Selecione os arquivos/URLs para excluir:", df["Nome"].tolist())
    if st.button("Excluir Selecionados"):
        excluir_arquivos(selecionados)
        st.rerun()

st.dataframe(df)


def main():
    with st.sidebar:
        sidebar()


if __name__ == '__main__':
    main()
