import streamlit as st
import webbrowser
import time

st.set_page_config(
    page_title='Inicio',
    page_icon='🏡',
    layout='wide'
)

st.title('🤖 ReppChat - Seu propagandista virtual 🧑‍⚕‍')

btn = st.button("Acesse nosso site")
if btn:
    webbrowser.open_new_tab("https://www.reppmobile.com")

st.markdown('''
            Feito por :rainbow[quem entende de propaganda médica e gestão].
            Somos especialistas há mais de 15 anos em estruturar e otimizar a propaganda médica, conectando-se diariamente a médicos.
            Além disso, nosso time acumula mais de 10 anos atuando em empresas de tecnologia de ponta 🤔, o que nos torna mais do que uma empresa de software – compreendemos seu negócio e suas necessidades de vendas junto aos consultórios.
            Nosso propósito é claro: ajudar as empresas alavancarem as vendas através de uma propaganda médica eficiente e inteligente.
    ''')

como_funciona = ''' Vá em configurações e insira todos os dados que você gostaria que o assistente soubesse.
                Os arquivos aceitos são: PDF, CSV, TXT, sites ou videos do Youtube.
                Você pode conferir os arquivos que foram carregados no botao **Listar arquivos**
                Após isso vá para Chat e converse com o assistente'''


def stream_como_funciona():
    for word in como_funciona.split(" "):
        yield word + " "
        time.sleep(0.02)


if st.button("Como funciona?"):
    st.write_stream(stream_como_funciona)

st.sidebar.markdown("Desenvolvido por [Repp]")
