import streamlit as st
import fitz  # PyMuPDF
import re
import unicodedata
import itertools
from difflib import SequenceMatcher

def marcar_inicio_nome(text):
    """Marca o início dos nomes com '@nome' após numeração (ex: '1. ')"""
    return re.sub(r'\b\d+\.\s*', '@nome', text)

def marcar_fim_nome_apos_inicio(text):
    """Marca o fim dos nomes após padrões como '. Palavra' ou '. 2020'"""
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

def normalizar_nomes(text):
    """Padroniza nomes removendo acentos e caracteres especiais"""
    linhas_normalizadas = []
    
    for linha in text.split('\n'):
        linha = unicodedata.normalize('NFKD', linha)
        linha = linha.encode('ASCII', 'ignore').decode('ASCII')
        linha = re.sub(r"[,.'\-]", ' ', linha)
        linha = re.sub(r'\s+', ' ', linha).strip().upper()
        linhas_normalizadas.append(linha)
    
    return '\n'.join(linhas_normalizadas)

def remover_particulas(text):
    """Remove partículas de ligação de nomes com mais de 2 palavras"""
    particulas = {"DA", "DE", "DO", "DAS", "DOS", "VAN", "JR", "JUNIOR"}
    linhas_limpas = []
    
    for linha in text.split('\n'):
        palavras = linha.split()
        if len(palavras) > 2:
            palavras = [p for p in palavras if p not in particulas]
        linhas_limpas.append(' '.join(palavras))
    
    return '\n'.join(linhas_limpas)

def processar_nome(nome):
    """Processa um nome para comparação"""
    nome = unicodedata.normalize('NFKD', nome)
    nome = nome.encode('ASCII', 'ignore').decode('ASCII').upper()
    nome = re.sub(r"[,.'\-]", ' ', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    
    partes = nome.split()
    particulas = {"DA", "DE", "DO", "DAS", "DOS", "VAN", "JR", "JUNIOR"}
    if len(partes) > 2:
        partes = [p for p in partes if p not in particulas]
    return ' '.join(partes)

def gerar_combinacoes_nomes(partes):
    """Gera variações possíveis para os nomes"""
    combinacoes = []
    n = len(partes)
    
    # Combinações não abreviadas
    if n >= 2:
        combinacoes.append(' '.join(partes))
        combinacoes.append(f"{partes[-1]} {' '.join(partes[:-1])}")
        
        if n >= 3:
            combinacoes.append(f"{' '.join(partes[-2:])} {' '.join(partes[:-2])}")

    # Abreviações progressivas
    if n >= 3:
        if n == 3:
            combinacoes.append(f"{partes[0]} {partes[1][0]} {partes[2]}")
        else:
            for qtd in range(1, n-1):
                for inicio in range(1, (n-1) - qtd + 1):
                    temp = partes.copy()
                    for i in range(inicio, inicio + qtd):
                        temp[i] = temp[i][0]
                    combinacoes.append(' '.join(temp))

    # Último nome primeiro com abreviações
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

    # Dois últimos primeiro com abreviações
    if n >= 3:
        dois_ultimos = partes[-2:]
        demais = partes[:-2]
        
        if demais:
            if n == 3:
                combinacoes.append(f"{' '.join(dois_ultimos)} {demais[0][0]}")
                combinacoes.append(f"{' '.join(dois_ultimos)} {demais[0]}")
            else:
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
st.set_page_config(page_title="Comparador de Nomes em PDF", layout="centered")
st.title("🔍 Comparador de Nomes em PDF")

# Seção de entrada de dados
st.subheader("Dados para Comparação")
candidates_input = st.text_area(
    "Insira os nomes completos dos candidatos (separados por vírgula):",
    placeholder="Ex: Maria Silva Oliveira, José Carlos Pereira",
    height=100
)

precision = st.slider(
    "Nível de precisão na comparação:",
    min_value=50,
    max_value=100,
    value=100,
    help="100% exige correspondência exata entre os nomes"
)

uploaded_file = st.file_uploader("Carregue o PDF para análise:", type="pdf")

if uploaded_file is not None and candidates_input:
    try:
        # Processar nomes dos candidatos
        nomes_candidatos = [nome.strip() for nome in candidates_input.split(',') if nome.strip()]
        candidatos = []
        
        for nome in nomes_candidatos:
            processado = processar_nome(nome)
            partes = processado.split()
            combinacoes = gerar_combinacoes_nomes(partes)
            candidatos.append({
                'original': nome,
                'combinations': combinacoes
            })

        # Processar PDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        raw_text = "".join(page.get_text() + "\n" for page in doc)
        cleaned_text = re.sub(r'\s+', ' ', raw_text)

        texto_marcado = marcar_inicio_nome(cleaned_text)
        texto_marcado = marcar_fim_nome_apos_inicio(texto_marcado)
        texto_formatado = formatar_quebras_paragrafo(texto_marcado)
        texto_limpo = limpar_texto(texto_formatado)
        texto_normalizado = normalizar_nomes(texto_limpo)
        texto_sem_particulas = remover_particulas(texto_normalizado)
        texto_final = texto_sem_particulas

        # Extrair nomes do PDF
        nomes_pdf = [linha.strip() for linha in texto_final.split('\n') if linha.strip()]

        # Realizar comparações
        threshold = precision / 100.0
        resultados = []
        
        for candidato in candidatos:
            encontrados = []
            
            for combinacao in candidato['combinations']:
                for nome_pdf in nomes_pdf:
                    similaridade = SequenceMatcher(None, combinacao, nome_pdf).ratio()
                    if similaridade >= threshold:
                        encontrados.append(nome_pdf)
            
            # Remover duplicatas mantendo a ordem
            vistos = set()
            unicos = []
            for nome in encontrados:
                if nome not in vistos:
                    vistos.add(nome)
                    unicos.append(nome)
            
            if unicos:
                resultados.append({
                    'buscado': candidato['original'],
                    'encontrados': unicos
                })

        # Exibir resultados
        st.subheader("Resultados da Busca")
        
        if resultados:
            for resultado in resultados:
                st.write(f"**Nome buscado:** {resultado['buscado']}")
                st.write("**Nome(s) encontrado(s):**")
                for encontrado in resultado['encontrados']:
                    st.write(encontrado)
                st.write("---")
        else:
            st.write("**Nenhum nome encontrado**")

    except Exception as e:
        st.error(f"Erro durante o processamento: {str(e)}")
elif uploaded_file and not candidates_input:
    st.warning("Por favor, insira os nomes dos candidatos para comparação.")
