import openai
from dotenv import load_dotenv, find_dotenv
import os

# Carrega arquivo .env
load_dotenv('.env')

# # Valida se API foi carregada
# print('hello', os.getenv('OPENAI_API_KEY'))
client = openai.Client()
# API OPENAI ================================================


def retorna_resposta_modelo(mensagens, modelo='gpt-3.5-turbo', temperatura=0, stream=False):
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model=modelo,
        messages=mensagens,
        temperature=temperatura,
        stream=stream
    )
    return response
