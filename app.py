import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

# Upload do PDF
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando com PyMuPDF...")

    # Ler PDF com PyMuPDF diretamente do upload
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    raw_text = ""

    # Extrair texto de todas as páginas
    for page in doc:
        raw_text += page.get_text() + "\n"

    # Substituir quebras de linha por espaço (substitui múltiplas quebras também)
    cleaned_text = raw_text.replace('\n', ' ')

    # Garantir codificação UTF-8
    text_bytes = cleaned_text.encode("utf-8")

    # Criar buffer para download
    txt_buffer = io.BytesIO(text_bytes)

    # Botão para download
    st.success("Texto extraído e limpo com sucesso!")
    st.download_button(
        label="📥 Baixar texto como .txt",
        data=txt_buffer,
        file_name="texto_extraido_limpo.txt",
        mime="text/plain"
    )

    # Mostrar preview do texto
    with st.expander("👁️ Visualizar início do texto"):
        st.text(cleaned_text[:2000] + "..." if len(cleaned_text) > 2000 else cleaned_text)

else:
    st.warning("Por favor, envie um arquivo PDF.")
