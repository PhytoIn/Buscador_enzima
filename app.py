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

def adicionar_quebras_paragrafo(text):
    # Lista de padrões para substituir por quebras de parágrafo (ordem é importante)
    padroes = [
        r'@nome',              # Marcador de início de nome
        r'@fim_nome',          # Marcador de fim de nome
        r'Integrantes:\s*',    # Título de seção
        r'Integrante\b\s*',    # Item de lista
        r'Coordenador\b\s*',   # Cargo
        r'\s\/\s',             # Barra com espaços
        r'\s\.\s',             # Espaço + ponto + espaço
        r';\s*',               # Ponto e vírgula
        r'In:\s*',             # Indicador de publicação
        r'\.\s*\(Org\.\)\s*', # Organizador com ponto
        r'\(Org\.\)\s*'       # Organizador sem ponto
    ]
    
    # Substituir cada padrão por uma quebra de linha
    for padrao in padroes:
        text = re.sub(padrao, '\n', text)
    
    # Remover múltiplas quebras de linha consecutivas e espaços extras
    text = re.sub(r'\n\s+', '\n', text)  # Remove espaços após quebras
    text = re.sub(r'\n+', '\n\n', text)  # Garante no máximo 2 quebras consecutivas
    
    return text.strip()

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

        # Passo 1: Marcar nomes
        marked_start_text = marcar_inicio_nome(cleaned_text)
        marked_text = marcar_fim_nome_apos_inicio(marked_start_text)

        # Passo 2: Adicionar quebras de parágrafo
        final_text = adicionar_quebras_paragrafo(marked_text)

        # Preparar para download
        text_bytes = final_text.encode("utf-8")
        txt_buffer = io.BytesIO(text_bytes)

        st.success("Texto extraído e formatado com sucesso!")
        st.download_button(
            label="📥 Baixar texto como .txt",
            data=txt_buffer,
            file_name="texto_formatado.txt",
            mime="text/plain"
        )

        with st.expander("👁️ Visualizar início do texto"):
            st.text_area("", value=final_text[:2000] + ("..." if len(final_text) > 2000 else ""), height=300)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {str(e)}")

else:
    st.warning("Por favor, envie um arquivo PDF.")
