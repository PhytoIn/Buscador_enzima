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

def gerar_combinacoes_nomes(partes):
    """Função corrigida para evitar combinação extra em nomes com 3 palavras"""
    combinacoes = []
    n = len(partes)
    
    # Grupo 1: Combinações não abreviadas
    if n >= 2:
        combinacoes.append(' '.join(partes))  # Ordem original
        combinacoes.append(f"{partes[-1]} {' '.join(partes[:-1])}")  # Último primeiro
        
        if n >= 3:
            combinacoes.append(f"{' '.join(partes[-2:])} {' '.join(partes[:-2])}")  # Dois últimos primeiro

    # Grupo 2: Abreviações progressivas do meio
    if n >= 3:
        if n == 3:
            # Apenas a combinação NOME1 N2 NOME3
            combinacoes.append(f"{partes[0]} {partes[1][0]} {partes[2]}")
        
        else:  # Para 4+ palavras
            for qtd in range(1, n-1):
                for inicio in range(1, (n-1) - qtd + 1):
                    temp = partes.copy()
                    for i in range(inicio, inicio + qtd):
                        temp[i] = temp[i][0]
                    combinacoes.append(' '.join(temp))

    # Grupo 3: Último nome primeiro com abreviações
    if n >= 2:
        ultimo = [partes[-1]]
        demais = partes[:-1]
        
        for qtd in range(1, len(demais)+1):
            for inicio in range(len(demais) - qtd + 1):
                temp = []
                for i, p in enumerate(demais):
                    if inicio <= i < inicio + qtd:
                        temp.append(p[0])
                    else:
                        temp.append(p)
                combinacoes.append(f"{' '.join(ultimo)} {' '.join(temp)}")

    # Grupo 4: Dois últimos primeiro com abreviações (corrigido)
    if n >= 3:
        dois_ultimos = partes[-2:]
        demais = partes[:-2]
        
        if demais:
            # Para 3 palavras: só há 1 nome para abreviar
            if n == 3:
                combinacoes.append(f"{' '.join(dois_ultimos)} {demais[0][0]}")  # Apenas abreviação
                combinacoes.append(f"{' '.join(dois_ultimos)} {demais[0]}")     # Sem abreviação
            
            else:  # 4+ palavras
                for qtd in range(1, len(demais)+1):
                    for inicio in range(len(demais) - qtd + 1):
                        temp = []
                        for i, p in enumerate(demais):
                            if inicio <= i < inicio + qtd:
                                temp.append(p[0])
                            else:
                                temp.append(p)
                        combinacoes.append(f"{' '.join(dois_ultimos)} {' '.join(temp)}")

    return list(set(combinacoes))

# Interface Streamlit
st.set_page_config(page_title="Extrair Texto de PDF", layout="centered")
st.title("📄 Extrair Texto de Arquivo PDF")

# --- NOVA SEÇÃO ADICIONADA AQUI ---
st.subheader("Processamento de Nomes de Candidatos")
candidates_input = st.text_area(
    "Cole os nomes completos dos candidatos (separados por vírgulas):",
    placeholder="Ex: João Silva Pereira, Maria Oliveira, Carlos Alberto Motta Jr.",
    height=100
)

if candidates_input:
    st.subheader("Combinações Geradas")
    names = [name.strip() for name in candidates_input.split(',') if name.strip()]
    
    for name in names:
        # Processar cada nome
        processed_name = unicodedata.normalize('NFKD', name)
        processed_name = processed_name.encode('ASCII', 'ignore').decode('ASCII').upper()
        processed_name = re.sub(r"[,.'\-]", ' ', processed_name)
        processed_name = re.sub(r'\s+', ' ', processed_name).strip()
        
        # Remover partículas
        particles = {"DA", "DE", "DO", "DAS", "DOS", "VAN", "JR", "JUNIOR"}
        parts = [p for p in processed_name.split() if p not in particles]
        processed_name = ' '.join(parts)
        
        if not parts:
            continue
            
        st.write(f"**Nome original:** {name}")
        st.write(f"**Nome processado:** {processed_name}")
        
        # Gerar combinações
        combinations = gerar_combinacoes_nomes(parts)  # parts já é a lista processada
        
        # Mostrar combinações
        st.write("**Combinações:**")
        for combo in sorted(combinations):
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
