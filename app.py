import streamlit as st
import fitz  # PyMuPDF
import re
import io


def marcar_inicio_nome(text):
    # Marca início dos nomes com '@nome' após numeração como "1. ", "2. ", etc.
    return re.sub(r'\b\d+\.\s*', '@nome', text)


def marcar_fim_nome_apos_inicio(text):
    # Padrão refinado: ". Palavra" ou ". 2020"
    # Apenas palavras com inicial maiúscula ou anos com 4 dígitos
    end_pattern = re.compile(r'\.\s([A-Z][a-zA-Z]{1,}|\d{4})')

    start_idx = 0
    result = []

    while True:
        # Encontrar próximo '@nome'
        start_match = re.search('@nome', text[start_idx:])
        if not start_match:
            break

        start_pos = start_idx + start_match.start()

        # Buscar o primeiro padrão '. Palavra' ou '. 2020' após '@nome'
        match = end_pattern.search(text[start_pos:])
        if match:
            pattern_start_global = start_pos + match.start()
            pattern_end_global = start_pos + match.end()

            # Adicionar texto até '@nome'
            result.append(text[start_idx:start_pos])

            # Adicionar '@nome...@fim_nome'
            result.append('@nome')
            result.append(text[start_pos + 5:pattern_start_global])  # Conteúdo entre '@nome' e padrão
            result.append('@fim_nome')

            # Continuar processando depois do padrão encontrado
            start_idx = pattern_end_global
        else:
            # Se não encontrar mais padrões, adicionar até o final
            result.append(text[start_idx:start_pos])
            result.append('@nome')
            start_idx = len(text)

    # Adicionar o restante do texto
    result.append(text[start_idx:])
    return ''.join(result)


# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

# Upload do PDF
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando com PyMuPDF...")

    try:
        # Ler PDF com PyMuPDF diretamente do upload
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = ""

        # Extrair texto de todas as páginas
        for page in doc:
            raw_text += page.get_text() + "\n"

        # Substituir quebras de linha por espaço
        cleaned_text = raw_text.replace('\n', ' ')

        # Passo 1: Marcar início dos nomes
        marked_start_text = marcar_inicio_nome(cleaned_text)

        # Passo 2: Marcar fim dos nomes com base no novo padrão refinado
        marked_text = marcar_fim_nome_apos_inicio(marked_start_text)

        # Garantir codificação UTF-8 para download
        text_bytes = marked_text.encode("utf-8")

        # Criar buffer para download
        txt_buffer = io.BytesIO(text_bytes)

        # Botão para download
        st.success("Texto extraído e marcado com sucesso!")
        st.download_button(
            label="📥 Baixar texto como .txt",
            data=txt_buffer,
            file_name="texto_marcado.txt",
            mime="text/plain"
        )

        # Mostrar preview do texto
        with st.expander("👁️ Visualizar início do texto"):
            st.text_area("", value=marked_text[:2000] + ("..." if len(marked_text) > 2000 else ""), height=300)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
