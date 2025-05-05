import streamlit as st
import fitz  # PyMuPDF
import re
import io

def marcar_inicio_nome(text):
    """Marca o início dos nomes com '@nome' após numeração (ex: '1. ')"""
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
    """Marca o fim dos nomes após padrões como '. Palavra' (incluindo acentos) ou '. 2020'"""
    end_pattern = re.compile(r'\.\s([A-ZÀ-Ú][a-zA-ZÀ-ú]{2,}|\d{4})')
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
        (r'@nome', '\n'),                   
        (r'@fim_nome', '\n'),              
        (r'Integrantes:', '\nIntegrantes:\n'),
        (r'\bIntegrante\b', '\n• '),       
        (r'\bCoordenador\b', '\nCoordenador:\n'),
        (r'\s/\s', '\n'),                  
        (r';', '\n'),                      
        (r'In:', '\nPublicado em:\n'),     
        (r'\.\s*\(Org\.\)', '\n(Organizador)\n'),
        (r'\(Org\.\)', '\n(Organizador)\n')
    ]
    
    for padrao, substituicao in substituicoes:
        text = re.sub(padrao, substituicao, text)
    
    text = re.sub(r' +', ' ', text)         
    text = re.sub(r'\n ', '\n', text)       
    text = re.sub(r'\n{3,}', '\n\n', text)  
    
    return text.strip()

def limpar_texto(text):
    """Aplica todas as regras de limpeza especificadas"""
    linhas_limpas = []
    
    for linha in text.split('\n'):
        original = linha  # Guarda a versão original para verificação de comprimento
        linha = linha.strip()
        
        # Regra 0: Remove parágrafos com 60+ caracteres (antes do strip)
        if len(original) >= 60:
            continue
            
        # Regra 1: Remove parágrafos com números
        if re.search(r'\d', linha):
            continue
            
        # Regra 2: Remove parágrafos com pontuação
        if re.search(r'[:?!]', linha):
            continue
            
        # Regra 3: Remove parágrafos com parênteses/colchetes
        if re.search(r'[\(\)\{\}\[\]]', linha):
            continue
            
        # Regra 4: Remove parágrafos com uma única palavra
        if len(linha.split()) == 1:
            continue
            
        # Regra 5: Remove espaços/hífens no final
        linha = re.sub(r'[-\s]+$', '', linha)
            
        linhas_limpas.append(linha)
    
    return '\n'.join(linhas_limpas)

def remover_linhas_repetidas(text):
    """Remove linhas duplicadas mantendo a primeira ocorrência"""
    linhas_vistas = set()
    linhas_unicas = []
    
    for linha in text.split('\n'):
        linha_limpa = linha.strip()
        if linha_limpa and linha_limpa not in linhas_vistas:
            linhas_vistas.add(linha_limpa)
            linhas_unicas.append(linha)
    
    return '\n'.join(linhas_unicas)

def ordenar_linhas_alfabeticamente(text):
    """Ordena as linhas em ordem alfabética, ignorando maiúsculas/minúsculas"""
    linhas = [linha.strip() for linha in text.split('\n') if linha.strip()]
    linhas_ordenadas = sorted(linhas, key=lambda x: x.lower())
    return '\n'.join(linhas_ordenadas)

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

        # Processamento em 6 etapas
        texto_marcado = marcar_inicio_nome(cleaned_text)
        texto_marcado = marcar_fim_nome_apos_inicio(texto_marcado)
        texto_formatado = formatar_quebras_paragrafo(texto_marcado)
        texto_limpo = limpar_texto(texto_formatado)
        texto_sem_repeticao = remover_linhas_repetidas(texto_limpo)
        texto_final = ordenar_linhas_alfabeticamente(texto_sem_repeticao)

        # Download
        txt_buffer = io.BytesIO(texto_final.encode('utf-8'))
        st.success("Pronto para download!")
        st.download_button(
            label="⬇️ Baixar texto formatado",
            data=txt_buffer,
            file_name="nomes_ordenados.txt",  # Nome mais descritivo
            mime="text/plain"
        )

        # Visualização
        with st.expander("🔍 Visualizar lista de nomes (ordenada alfabeticamente)"):
            st.text(texto_final[:2000] + ("..." if len(texto_final) > 2000 else ""))

        # Estatísticas
        num_nomes = len(texto_final.split('\n'))
        st.info(f"✅ Processamento concluído! Total de nomes únicos: {num_nomes}")

    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
else:
    st.warning("Por favor, carregue um arquivo PDF.")
