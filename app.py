import streamlit as st
import fitz  # PyMuPDF
import re
import io


def marcar_inicio_nome(text):
    # Marca início dos nomes com '@nome' após numeração como "1. ", "2. ", etc.
    return re.sub(r'\b\d+\.\s*', '@nome', text)


def marcar_fim_nome_apos_inicio(text):
    # Padrão combinado: ". XX" onde X pode ser maiúscula ou minúscula, ou ". ####"
    end_pattern = re.compile(r'\.\s([A-Za-z][A-Za-z]|\d{4})')

    start_idx = 0
    result = []

    while True:
        # Encontra próximo '@nome'
        start_match = re.search('@nome', text[start_idx:])
        if not start_match:
            break

        start_pos = start_idx + start_match.start()

        # Procura o fim do nome após @nome
        end_match = end_pattern.search(text[start_pos:])
        if end_match:
            end_pos = start_pos + end_match.end()

            # Adicionar partes do texto até o '@fim_nome'
            result.append(text[start_idx:start_pos])          # Texto antes do @nome
            result.append('@nome')                            # Inserção explícita
            result.append(text[start_pos + 5:end_pos - 1])    # Nome sem o . XX ou . ####
            result.append(' @fim_nome')                      # Fim da marcação

            start_idx = end_pos  # Atualiza índice
        else:
            # Se não encontrar, adicionar até o final
            result.append(text[start_idx:start_pos])
            result.append('@nome')
            start_idx = len(text)

    # Adiciona o restante do texto
    result.append(text[start_idx:])
    return ''.join(result)


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

        # Passo 2: Marcar fim dos nomes baseado no primeiro '. $$' ou '. ####'
        marked_text = marcar_fim_nome_apos_inicio(marked_start_text)

        # Garantir codificação UTF-8
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
