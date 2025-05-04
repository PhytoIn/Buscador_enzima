import streamlit as st
import fitz  # PyMuPDF
import re
import io

def marcar_inicio_nome(text):
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
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
    # Lista de padrões para substituição com prioridade
    padroes = [
        (r'@nome', '\n'),                    # Início do nome
        (r'@fim_nome', '\n'),                # Fim do nome
        (r'Integrantes:\s*', '\n'),          # Seção de integrantes
        (r'Integrante\b\s*', '\n'),          # Itens de lista
        (r'Coordenador\b\s*', '\n'),         # Cargo
        (r'\s\/\s', '\n'),                   # Separador com espaços
        (r';\s*', '\n'),                     # Ponto-e-vírgula
        (r'In:\s*', '\n'),                   # Indicador de publicação
        (r'\.\s*\(Org\.\)\s*', '\n'),        # Organizador com ponto
        (r'\(Org\.\)\s*', '\n')              # Organizador sem ponto
    ]
    
    # Aplicar substituições em ordem
    for padrao, substituicao in padroes:
        text = re.sub(padrao, substituicao, text)
    
    # Limpar espaços e quebras múltiplas
    text = re.sub(r'\s+', ' ', text)          # Remove espaços extras
    text = re.sub(r'\n\s*', '\n', text)       # Remove espaços após quebras
    text = re.sub(r'\n{3,}', '\n\n', text)    # Limita para 2 quebras consecutivas
    
    return text.strip()

# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")
st.subheader("Faça upload de um PDF e baixe o texto extraído em formato .txt")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("Processando com PyMuPDF...")

    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = "".join([page.get_text() + "\n" for page in doc])
        cleaned_text = raw_text.replace('\n', ' ')

        # Processamento em 3 etapas
        texto_marcado = marcar_fim_nome_apos_inicio(marcar_inicio_nome(cleaned_text))
        texto_formatado = formatar_quebras_paragrafo(texto_marcado)

        # Preparar para download
        txt_buffer = io.BytesIO(texto_formatado.encode("utf-8"))
        
        st.success("Texto processado com sucesso!")
        st.download_button(
            label="📥 Baixar texto formatado",
            data=txt_buffer,
            file_name="curriculo_formatado.txt",
            mime="text/plain"
        )

        with st.expander("🔍 Visualizar texto formatado"):
            st.text(texto_formatado[:2000] + ("..." if len(texto_formatado) > 2000 else ""))

    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")

else:
    st.warning("Por favor, carregue um arquivo PDF.")
