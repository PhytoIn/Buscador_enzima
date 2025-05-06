import streamlit as st
import fitz  # PyMuPDF
import re
import io
import unicodedata
import itertools

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
        original = linha
        linha = linha.strip()
        
        if len(original) >= 60:
            continue
            
        if re.search(r'\d', linha):
            continue
            
        if re.search(r'[:?!]', linha):
            continue
            
        if re.search(r'[\(\)\{\}\[\]]', linha):
            continue
            
        if len(linha.split()) == 1:
            continue
            
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

def normalizar_nomes(text):
    """Padroniza nomes removendo acentos, caracteres especiais e espaços extras"""
    linhas_normalizadas = []
    
    for linha in text.split('\n'):
        linha = unicodedata.normalize('NFKD', linha)
        linha = linha.encode('ASCII', 'ignore').decode('ASCII')
        linha = re.sub(r"[,.'\-]", ' ', linha)
        linha = re.sub(r'\s+', ' ', linha).strip().upper()
        linhas_normalizadas.append(linha)
    
    return '\n'.join(linhas_normalizadas)

def remover_particulas(text):
    """Remove partículas de ligação e sufixos em nomes com mais de 2 palavras"""
    particulas = {"DA", "DE", "DO", "DAS", "DOS", "VAN", "JR", "JUNIOR"}
    linhas_limpas = []
    
    for linha in text.split('\n'):
        palavras = linha.split()
        if len(palavras) > 2:
            palavras = [p for p in palavras if p not in particulas]
        linhas_limpas.append(' '.join(palavras))
    
    return '\n'.join(linhas_limpas)

def processar_nome(nome):
    """Processa um único nome: normaliza e remove partículas"""
    nome = unicodedata.normalize('NFKD', nome)
    nome = nome.encode('ASCII', 'ignore').decode('ASCII').upper()
    nome = re.sub(r"[,.'\-]", ' ', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    
    partes = nome.split()
    if len(partes) > 2:
        particulas = {"DA", "DE", "DO", "DAS", "DOS", "VAN", "JR", "JUNIOR"}
        partes = [p for p in partes if p not in particulas]
    return ' '.join(partes)

def gerar_combinacoes_grupo1(partes):
    """Gera combinações do primeiro grupo de padrões"""
    combinacoes = []
    n = len(partes)
    
    if n >= 4:
        for i in range(1, n-2):
            nova_parte = [partes[0]]
            for j in range(1, n-1):
                if j == i:
                    nova_parte.append(partes[j][0])
                else:
                    nova_parte.append(partes[j])
            nova_parte.append(partes[-1])
            combinacoes.append(' '.join(nova_parte))
    
    if n >= 3:
        abreviados_meio = [p[0] for p in partes[1:-1]]
        combinacoes.append(f"{partes[0]} {' '.join(abreviados_meio)} {partes[-1]}")
    
    return combinacoes

def gerar_combinacoes_grupo2(partes):
    """Gera combinações do segundo grupo de padrões"""
    combinacoes = []
    n = len(partes)
    
    if n >= 2:
        ultimo_nome = partes[-1]
        outros_nomes = partes[:-1]
        
        for r in range(1, len(outros_nomes)+1):
            for combinacao in itertools.permutations(outros_nomes, r):
                for mask in itertools.product([True, False], repeat=r):
                    partes_abreviadas = []
                    for i, parte in enumerate(combinacao):
                        if mask[i]:
                            partes_abreviadas.append(parte[0])
                        else:
                            partes_abreviadas.append(parte)
                    combinacoes.append(f"{ultimo_nome} {' '.join(partes_abreviadas)}")
    
    return combinacoes

# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")

# Seção para processamento de nomes de candidatos
st.subheader("Processamento de Nomes de Candidatos")
nomes_candidatos = st.text_area(
    "Cole os nomes dos candidatos (separados por vírgulas):",
    help="Exemplo: João Silva Pereira, Maria Costa Jr, Antônio D'Ávila"
)

if nomes_candidatos:
    st.subheader("Resultado do Processamento de Nomes")
    nomes = [nome.strip() for nome in nomes_candidatos.split(',')]
    
    for nome_original in nomes:
        nome_processado = processar_nome(nome_original)
        partes = nome_processado.split()
        
        if not partes:
            continue
        
        st.write(f"**Nome original:** {nome_original}")
        st.write(f"**Nome processado:** {nome_processado}")
        
        # Gerar combinações
        grupo1 = gerar_combinacoes_grupo1(partes)
        grupo2 = gerar_combinacoes_grupo2(partes)
        
        st.write("**Combinações Geradas:**")
        for combo in grupo1 + grupo2:
            st.write(f"- {combo}")
        
        st.write("---")

# Seção original de processamento de PDF
st.subheader("Processamento de Arquivos PDF")
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    # Processamento do PDF existente...
    # ... (mantido igual ao código original)

    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = "".join(page.get_text() + "\n" for page in doc)
        cleaned_text = re.sub(r'\s+', ' ', raw_text)

        texto_marcado = marcar_inicio_nome(cleaned_text)
        texto_marcado = marcar_fim_nome_apos_inicio(texto_marcado)
        texto_formatado = formatar_quebras_paragrafo(texto_marcado)
        texto_limpo = limpar_texto(texto_formatado)
        texto_normalizado = normalizar_nomes(texto_limpo)
        texto_sem_particulas = remover_particulas(texto_normalizado)
        texto_sem_repeticao = remover_linhas_repetidas(texto_sem_particulas)
        texto_final = ordenar_linhas_alfabeticamente(texto_sem_repeticao)

        txt_buffer = io.BytesIO(texto_final.encode('utf-8'))
        st.success("Pronto para download!")
        st.download_button(
            label="⬇️ Baixar texto formatado",
            data=txt_buffer,
            file_name="nomes_ordenados.txt",
            mime="text/plain"
        )

        with st.expander("🔍 Visualizar lista de nomes"):
            st.text(texto_final[:2000] + ("..." if len(texto_final) > 2000 else ""))

        num_nomes = len(texto_final.split('\n'))
        st.info(f"✅ Processamento concluído! Total de nomes únicos: {num_nomes}")

    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
else:
    st.warning("Por favor, carregue um arquivo PDF.")
