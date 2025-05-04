import streamlit as st
import fitz  # PyMuPDF
import re
import io

def marcar_inicio_nome(text):
    # Marca início dos nomes com '@nome' após numeração como "1. ", "2. ", etc.
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
    # Padrão refinado: ". Palavra" (pelo menos 3 letras) ou ". 2020"
    end_pattern = re.compile(r'\.\s([A-Z][a-zA-Z]{2,}|\d{4})')

    start_idx = 0
    result = []

    while True:
        # Encontrar próximo '@nome'
        start_match = re.search(r'@nome', text[start_idx:])
        if not start_match:
            break

        start_pos = start_idx + start_match.start()

        # Buscar o primeiro padrão '. Palavra' ou '. 2020' após '@nome'
        match = end_pattern.search(text[start_pos:])
        if not match:
            break

        pattern_start_global = start_pos + match.start()
        pattern_end_global = start_pos + match.end()

        # Adicionar texto desde o último índice até o início do '@nome'
        result.append(text[start_idx:start_pos])

        # Adicionar conteúdo do '@nome' até o início do padrão e incluir '@fim_nome'
        result.append(text[start_pos:pattern_start_global])
        result.append('@fim_nome')

        # Adicionar o padrão encontrado (ex: ". Polimorfismo" ou ". 2020")
        result.append(text[pattern_start_global:pattern_end_global])

        # Atualizar o índice para continuar após o padrão
        start_idx = pattern_end_global

    # Adicionar o restante do texto
    result.append(text[start_idx:])
    return ''.join(result)

# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando com PyMuPDF...")

    try:
        # Ler PDF com PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = ""

        for page in doc:
            raw_text += page.get_text() + "\n"

        cleaned_text = raw_text.replace('\n', ' ')

        marked_start_text = marcar_inicio_nome(cleaned_text)
        marked_text = marcar_fim_nome_apos_inicio(marked_start_text)

        text_bytes = marked_text.encode("utf-8")
        txt_buffer = io.BytesIO(text_bytes)

        st.success("Texto extraído e marcado com sucesso!")
        st.download_button(
            label="📥 Baixar texto como .txt",
            data=txt_buffer,
            file_name="texto_marcado.txt",
            mime="text/plain"
        )

        with st.expander("👁️ Visualizar início do texto"):
            st.text_area("", value=marked_text[:2000] + ("..." if len(marked_text) > 2000 else ""), height=300)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
