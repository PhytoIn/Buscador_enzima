import streamlit as st
from PyPDF2 import PdfReader
import io

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

    # Garantir codificação UTF-8
    text_bytes = raw_text.encode('utf-8')

    # Criar buffer para download
    txt_buffer = io.BytesIO(text_bytes)

    # Botão para download
    st.success("Texto extraído com sucesso!")
    st.download_button(
        label="📥 Baixar texto como .txt",
        data=txt_buffer,
        file_name="texto_extraido.txt",
        mime="text/plain"
    )

    # Mostrar preview do texto
    with st.expander("👁️ Visualizar início do texto"):
        st.text(raw_text[:2000] + "..." if len(raw_text) > 2000 else raw_text)

else:
    st.warning("Por favor, envie um arquivo PDF.")
