import streamlit as st
from PyPDF2 import PdfReader
import io
import re

def corrigir_palavras_quebradas(text):
    # 1. Trata palavras cortadas com hífen e espaço (ex: "epiph-\n yte" → "epiphyte")
    text = re.sub(r'(\w+)-\s*\n?(\w+)', r'\1\2', text)

    # 2. Corrige palavras partidas sem hífen, ex: "Neotr opical" → "Neotropical"
    text = re.sub(r'(\b[A-Za-z]{1,2})\s+([a-z]{3,})', r'\1\2', text)

    return text


st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

# Upload do PDF
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando o arquivo...")

    # Ler o PDF
    reader = PdfReader(uploaded_file)
    raw_text = ""

    # Extrair texto de todas as páginas
    for page in reader.pages:
        text = page.extract_text()
        if text:
            raw_text += text + "\n"

    # Aplicar correções nas palavras quebradas
    cleaned_text = corrigir_palavras_quebradas(raw_text)

    # Garantir codificação UTF-8
    text_bytes = cleaned_text.encode('utf-8')

    # Criar buffer para download
    txt_buffer = io.BytesIO(text_bytes)

    # Botão para download
    st.success("Texto extraído e corrigido com sucesso!")
    st.download_button(
        label="📥 Baixar texto como .txt",
        data=txt_buffer,
        file_name="texto_extraido_corrigido.txt",
        mime="text/plain"
    )

    # Mostrar preview do texto
    with st.expander("👁️ Visualizar início do texto"):
        st.text(cleaned_text[:2000] + "..." if len(cleaned_text) > 2000 else cleaned_text)

else:
    st.warning("Por favor, envie um arquivo PDF.")
