import streamlit as st
import fitz  # PyMuPDF
import re
import io

def marcar_inicio_nome(text):
    """Marca o início dos nomes com '@nome' após numeração (ex: '1. ')"""
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
    """Marca o fim dos nomes após padrões como '. Palavra' ou '. 2020'"""
    end_pattern = re.compile(r'\.\s([A-Z][a-zA-Z]{2,}|\d{4})')
    start_idx = 0
    result = []

    while True:
        start_match = re.search(r'@nome', text[start_idx:])
        if not start_match:
            break

        start_pos = start_idx + start_match.start()
        match = end_pattern.search(text[start_pos:])
        if not match:
            break

        pattern_start_global = start_pos + match.start()
        pattern_end_global = start_pos + match.end()

        result.append(text[start_idx:start_pos])
        result.append(text[start_pos:pattern_start_global])
        result.append('@fim_nome')
        result.append(text[pattern_start_global:pattern_end_global])
        start_idx = pattern_end_global

    result.append(text[start_idx:])
    return ''.join(result)

def formatar_quebras_paragrafo(text):
    """Substitui marcadores por quebras de parágrafo"""
    substituicoes = [
        (r'@nome', '\n'),                    # Quebra antes do nome
        (r'@fim_nome', '\n'),                # Quebra após o nome
        (r'Integrantes:', '\nIntegrantes:\n'),  # Seção com quebra dupla
        (r'\bIntegrante\b', '\n• '),         # Itens de lista com marcador
        (r'\bCoordenador\b', '\nCoordenador:\n'),
        (r'\s/\s', '\n'),                    # Barra como separador
        (r';', '\n'),                        # Ponto-e-vírgula
        (r'In:', '\nPublicado em:\n'),       # Título descritivo
        (r'\.\s*\(Org\.\)', '\n(Organizador)\n'),
        (r'\(Org\.\)', '\n(Organizador)\n')
    ]
    
    for padrao, substituicao in substituicoes:
        text = re.sub(padrao, substituicao, text)
    
    # Pós-processamento
    text = re.sub(r' +', ' ', text)          # Remove espaços múltiplos
    text = re.sub(r'\n ', '\n', text)        # Remove espaços após quebras
    text = re.sub(r'\n{3,}', '\n\n', text)   # Limita a 2 quebras consecutivas
    
    return text.strip()

# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto formatado")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando PDF...")
    
    try:
        # Extração do texto
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = "".join(page.get_text() + "\n" for page in doc)
        cleaned_text = re.sub(r'\s+', ' ', raw_text)  # Normaliza espaços

        # Processamento em 3 etapas
        texto_marcado = marcar_inicio_nome(cleaned_text)
        texto_marcado = marcar_fim_nome_apos_inicio(texto_marcado)
        texto_final = formatar_quebras_paragrafo(texto_marcado)

        # Download
        txt_buffer = io.BytesIO(texto_final.encode('utf-8'))
        st.success("Pronto para download!")
        st.download_button(
            label="⬇️ Baixar texto formatado",
            data=txt_buffer,
            file_name="texto_formatado.txt",
            mime="text/plain"
        )

        # Visualização
        with st.expander("🔍 Pré-visualização (primeiras 2000 caracteres)"):
            st.text(texto_final[:2000] + ("..." if len(texto_final) > 2000 else ""))

    except Exception as e:
        st.error(f"Erro: {str(e)}")
else:
    st.warning("Por favor, carregue um arquivo PDF.")
