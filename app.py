import streamlit as st

import os

from google import genai

from google.genai import types



# --- CONFIGURAÇÕES DE SEGURANÇA ---

try:

    API_KEY = st.secrets["GEMINI_API_KEY"]

except FileNotFoundError:

    st.error("Arquivo .streamlit/secrets.toml não encontrado.")

    st.stop()

except KeyError:

    st.error("Chave 'GEMINI_API_KEY' não encontrada no secrets.toml.")

    st.stop()



# --- ESCOLHA DO MODELO ---

# Usando o nome EXATO que apareceu na sua lista (Turno 15)

MODELO_ESCOLHIDO = "gemini-flash-latest"



# Configuração da página

st.set_page_config(page_title="Auditor Jurídico AI", page_icon="⚖️", layout="wide")



st.title("⚖️ Auditor Jurídico - Análise de Processos")

st.markdown(f"Status: Conectado ao modelo **{MODELO_ESCOLHIDO}**")



# --- Instruções do Sistema ---

SYSTEM_INSTRUCTION = """ATUAÇÃO:

Você é um Auditor Jurídico Sênior. Seu objetivo é analisar relatórios processuais em PDF e gerar indicadores de gestão claros para tomada de decisão.



REGRAS DE CLASSIFICAÇÃO:



1. TEMPORALIDADE (Novos vs. Antigos):

   - "Novos": Processos distribuídos nos últimos 30 dias (baseado na data mais recente encontrada no documento ou na data atual).

   - "Antigos": Processos anteriores a esse período.



2. STATUS PADRONIZADO (Classifique APENAS nestas 4 categorias):

   - "Em Andamento": Processos ativos, aguardando audiência, perícia ou sentença.

   - "Finalizados": Processos arquivados, extintos ou com trânsito em julgado (sem mérito de ganho/perda explícito).

   - "Ganhos": Processos julgados improcedentes (empresa venceu) ou extintos sem custo.

   - "Perdidos": Processos julgados procedentes ou parcialmente procedentes (empresa condenada) ou acordos pagos.



3. DATAS:

   - Extraia a "Data Início" (Distribuição).

   - Extraia a "Data Fim" (Sentença/Trânsito em Julgado/Arquivamento) se houver. Se não houver, deixe em branco.



4. PASSIVOS:

   - Identifique a razão principal (ex: Horas Extras, Dano Moral).



FORMATO DE SAÍDA (Obrigatório seguir esta ordem):



PARTE 1: RESUMO EXECUTIVO (Bullet Points)

- Quantidade de Processos NOVOS (últimos 30 dias): [N]

- Quantidade de Processos JÁ EXISTENTES: [N]

- Contagem por Status: [N] Em Andamento, [N] Finalizados, [N] Ganhos, [N] Perdidos.

- Principais Ofensores (Top 3 motivos de passivos):



PARTE 2: TABELA VISUAL (Markdown)

Crie uma tabela com as colunas:

| N. Processo | Status | Data Início | Data Fim | Motivo Passivo | Valor |



PARTE 3: DADOS PARA EXCEL (CSV)

- Bloco de código para copiar e colar.

- Separador: PONTO E VÍRGULA (;)

- Formato de data: DD/MM/AAAA

- Colunas: Numero_Processo;Status_Padronizado;Novo_ou_Antigo;Data_Inicio;Data_Fim;Motivo_Passivo;Valor_Causa"""



# --- Área Principal ---



uploaded_file = st.file_uploader("Faça upload do relatório processual (PDF)", type=["pdf"])



if uploaded_file and st.button("Analisar Documento"):

    try:

        client = genai.Client(api_key=API_KEY)

        pdf_data = uploaded_file.read()



        contents = [

            types.Content(

                role="user",

                parts=[

                    types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"),

                    types.Part.from_text(text="Analise este arquivo PDF conforme suas instruções de sistema."),

                ],

            ),

        ]



        generate_content_config = types.GenerateContentConfig(

            temperature=0.2,

            system_instruction=[

                types.Part.from_text(text=SYSTEM_INSTRUCTION),

            ],

        )

        

        st.divider()

        st.subheader("Relatório de Auditoria")

        

        def stream_parser():

            stream = client.models.generate_content_stream(

                model=MODELO_ESCOLHIDO,

                contents=contents,

                config=generate_content_config,

            )

            for chunk in stream:

                if chunk.text:

                    yield chunk.text



        st.write_stream(stream_parser)



    except Exception as e:

        st.error(f"Ocorreu um erro: {e}")
