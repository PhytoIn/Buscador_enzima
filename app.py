import streamlit as st
import fitz  # PyMuPDF
import re
import io

# === Funções de Processamento ===

def marcar_inicio_nome(text):
    # Marca início dos nomes com '@nome' após numeração como "1. ", "2. ", etc.
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
    # Padrão refinado: ". [A-Z][a-z]+" (palavra com inicial maiúscula e pelo menos 3 letras) ou ". ####"
    end_pattern = re.compile(r'\.\s([A-Z][a-zA-Z]{2,}|\d{4})')

    start_idx = 0
    result = []
    text_length = len(text)

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

            result.append(text[start_idx:start_pos])
            result.append('@nome')
            result.append(text[start_pos + 5:pattern_start_global])
            result.append('@fim_nome')
            start_idx = pattern_end_global
        else:
            result.append(text[start_idx:start_pos])
            result.append('@nome')
            start_idx = text_length
            break

    result.append(text[start_idx:])
    return ''.join(result)

def inserir_quebras_de_paragrafo(text):
    # Padrão para identificar os marcadores e substituir por quebra de parágrafo
    padrao = re.compile(r"""
        Integrantes:\s*|           # Marcador: Integrantes:
        Integrante\s*|             # Marcador: Integrante
        Coordenador\s*|           # Marcador: Coordenador
        /\s*|                      # Marcador: barra
         \. \s*|                   # Marcador: espaço + ponto + espaço
        ;\s*|                      # Marcador: ponto e vírgula
        In:\s*|                    # Marcador: In:
        \. $Org\.$\s*|            # Marcador: . (Org.)
        $Org\.$\s*                # Marcador: (Org.)
    """, re.VERBOSE)

    # Substitui todos os marcadores por duas quebras de linha
    return padrao.sub('\n\n', text)

# === Interface Streamlit ===

st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

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

        # Passo 3: Inserir quebras de parágrafo com base nos marcadores
        text_com_quebras = inserir_quebras_de_paragrafo(marked_text)

        # Reduz múltiplas quebras de linha a uma única
        text_limpo = re.sub(r'\n{3,}', '\n\n', text_com_quebras)

        # Garantir codificação UTF-8 para download
        text_bytes = text_limpo.encode("utf-8")
        txt_buffer = io.BytesIO(text_bytes)

        # Botão para download
        st.success("Texto extraído e formatado com sucesso!")
        st.download_button(
            label="📥 Baixar texto como .txt",
            data=txt_buffer,
            file_name="texto_formatado.txt",
            mime="text/plain"
        )

        # Mostrar preview do texto
        with st.expander("👁️ Visualizar início do texto"):
            st.text_area("", value=text_limpo[:2000] + ("..." if len(text_limpo) > 2000 else ""), height=300)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
