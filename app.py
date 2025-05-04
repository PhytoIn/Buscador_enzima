import streamlit as st
import fitz  # PyMuPDF
import re
import io


def marcar_inicio_nome(text):
    # Marca início dos nomes com '@nome'
    text = re.sub(r' \d{1,3}\. ', ' @nome', text)
    text = re.sub(r' \d{1,3}\.\n', ' @nome\n', text)
    text = re.sub(r'\n\d{1,3}\. ', '\n@nome', text)
    return text


def marcar_fim_nome_apos_inicio(text):
    # Encontra todos os pontos com duas letras maiúsculas: ". SP", ". II", ". BR"
    pattern = re.compile(r'(\.[\s][A-Z][A-Z])')

    # Procura todos os "@nome" e seus posições
    nome_positions = [m.start() for m in re.finditer('@nome', text)]

    # Lista para armazenar os novos cortes
    new_text_parts = []
    last_pos = 0

    for start_pos in nome_positions:
        # Pegar parte do texto após esse '@nome'
        subtext = text[start_pos:]

        # Encontrar o primeiro '. $$' nessa parte
        match = pattern.search(subtext)

        if match:
            end_pos_in_sub = match.end()
            end_pos_global = start_pos + end_pos_in_sub

            # Adicionar parte antes do '. $$' + '@fim_nome'
            new_text_parts.append(text[last_pos:start_pos])
            new_text_parts.append('@nome')
            new_text_parts.append(text[start_pos + 5:end_pos_global - 1])  # pega nome até antes do ponto
            new_text_parts.append(' @fim_nome')

            last_pos = end_pos_global
        else:
            # Se não encontrar '. $$', apenas continua
            continue

    # Adiciona o restante do texto
    new_text_parts.append(text[last_pos:])
    return ''.join(new_text_parts)


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

        # Passo 2: Marcar fim dos nomes baseado no primeiro '. $$' após '@nome'
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
            st.text(marked_text[:2000] + "..." if len(marked_text) > 2000 else marked_text)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
