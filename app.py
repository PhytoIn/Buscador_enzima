import streamlit as st
import fitz  # PyMuPDF
import re
import io


def marcar_nomes_em_duas_etapas(text):
    # --- Passo 1: Marca início dos nomes com '@nome' ---
    text = re.sub(r' \d{1,3}\. ', ' @nome ', text)
    text = re.sub(r' \d{1,3}\.\n', ' @nome\n', text)
    text = re.sub(r'\n\d{1,3}\. ', '\n@nome ', text)

    # --- Passo 2: Para cada '@nome', substitui o primeiro '. [A-Z]' por '@fim_nome' ---
    def marcar_fim(match_block):
        bloco = match_block.group(0)
        # Substitui apenas o primeiro '. [A-Z]' por '@fim_nome'
        bloco_modificado = re.sub(r'\.\s([A-Z])', ' @fim_nome \\1', bloco, count=1)
        return bloco_modificado

    # Procura blocos começando com '@nome' até o primeiro '. [A-Z]' (sem pular para outros blocos)
    text = re.sub(r'(@nome[^\n]*?)(?=\.\s[A-Z])', marcar_fim, text, flags=re.DOTALL)

    return text


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

    # Substituir quebras de linha por espaço
    cleaned_text = raw_text.replace('\n', ' ')

    # Marcar nomes conforme os padrões definidos
    marked_text = marcar_nomes_em_duas_etapas(cleaned_text)

    # Garantir codificação UTF-8
