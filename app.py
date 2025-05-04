import streamlit as st
import fitz  # PyMuPDF
import io

def marcar_nomes_em_duas_etapas(text):
    # Passo 1: Marca início dos nomes com '@nome'
    text = re.sub(r' \d{1,3}\. ', ' @nome ', text)
    text = re.sub(r' \d{1,3}\.\n', ' @nome\n', text)
    text = re.sub(r'\n\d{1,3}\. ', '\n@nome ', text)

    # Passo 2: Para cada '@nome', substitui o primeiro '. [A-Z]' por '@fim_nome'
    def marcar_fim(match_block):
        bloco = match_block.group(0)
        # Substitui apenas o primeiro '. [A-Z]'
        bloco_modificado = re.sub(r'\.\s([A-Z])', ' @fim_nome \\1', bloco, count=1)
        return bloco_modificado

    # Procura blocos começando com '@nome' até o primeiro '. [A-Z]'
    text = re.sub(r'(@nome[^\n]*?)(?=\.\s[A-Z])', marcar_fim, text, flags=re.DOTALL)

    return text


st.set_page_config(page_title="Extrair Texto de Arquivo PDF", layout="centered")
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

        # Marcar nomes conforme os padrões definidos
        marked_text = marcar_nomes_em_duas_etapas(cleaned_text)

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

        # Mostrar preview do texto (limitado a 2000 caracteres)
        with st.expander("👁️ Visualizar início do texto"):
            st.text(marked_text[:2000] + "..." if len(marked_text) > 2000 else marked_text)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
