import streamlit as st
import os
import re  
from google import genai
from google.genai import types

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("Arquivo .streamlit/secrets.toml não encontrado.")
    st.stop()
except KeyError:
    st.error("Chave 'GEMINI_API_KEY' não encontrada no secrets.toml.")
    st.stop()

MODELO_ESCOLHIDO = "gemini-flash-latest"

st.set_page_config(page_title="Auditor Jurídico AI", page_icon="⚖️", layout="wide")

st.title("⚖️ Auditor Jurídico - Análise de Processos")
st.markdown(f"Status: Conectado ao modelo **{MODELO_ESCOLHIDO}**")

SYSTEM_INSTRUCTION = """ATUAÇÃO:
Você é um Auditor Jurídico Sênior com foco em "Data Mining" (Mineração de Dados). Sua prioridade absoluta é a granularidade e especificidade dos dados.

REGRA DE OURO (ANTI-PREGUIÇA):
É ESTRITAMENTE PROIBIDO usar termos genéricos como "Verbas Rescisórias", "Direitos Trabalhistas", "Obrigações de Fazer" ou "Indenizações". Você DEVE "explodir" esses termos nos itens reais da petição.

PROTOCOLO DE EXTRAÇÃO DE PASSIVOS:
1. NÃO RESUMA. Liste os itens.
2. Se o texto diz "Verbas Rescisórias", você deve procurar quais são e listar: "Aviso Prévio / Férias Proporcionais / Multa 40% FGTS / Multa Art. 477".
3. Se o texto diz "Horas Extras", especifique: "Horas Extras 50% / Intervalo Intrajornada / Adicional Noturno".
4. Se o texto diz "Insalubridade/Periculosidade", especifique o grau ou motivo: "Adicional Insalubridade (Ruído) / Periculosidade (Eletricidade)".
5. Se houver mais de 3 itens, liste os 3 financeiramente mais impactantes ou os primeiros citados.

REGRAS GERAIS:

1. TEMPORALIDADE:
   - "Novos": Últimos 30 dias.
   - "Antigos": Anteriores a 30 dias.

2. STATUS (Apenas 4 tipos):
   - "Em Andamento"
   - "Finalizados"
   - "Ganhos"
   - "Perdidos"

3. DATAS:
   - Formato DD/MM/AAAA. Se não houver dia, use 01/MM/AAAA.

FORMATO DE SAÍDA (Obrigatório seguir esta ordem):

PARTE 1: RESUMO EXECUTIVO (Bullet Points)
- Quantidade de Processos NOVOS (últimos 30 dias): [N]
- Quantidade de Processos JÁ EXISTENTES: [N]
- Contagem por Status: [N] Em Andamento, [N] Finalizados, [N] Ganhos, [N] Perdidos.
- TOP 5 OFENSORES ESPECÍFICOS (Não use termos genéricos):
  1. [Item Específico, ex: Falta de Registro na CTPS] - [Qtd] recorrências
  2. [Item Específico, ex: Multa do Art. 477] - [Qtd] recorrências
  3. ...

PARTE 2: TABELA VISUAL (Markdown)
Crie uma tabela com as colunas:
| N. Processo | Status | Data Início | Data Fim | Causa Raiz (Itens Específicos separados por barra / ) | Valor |

PARTE 3: DADOS PARA EXCEL (CSV)
- Bloco de código CSV.
- Separador: PONTO E VÍRGULA (;)
- Colunas: Numero_Processo;Status;Novo_ou_Antigo;Data_Inicio;Data_Fim;Itens_Especificos_Passivo;Valor_Causa
"""
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

        response_text = st.write_stream(stream_parser)

        match = re.search(r"```(?:csv)?\n(.*?)```", response_text, re.DOTALL)

        if match:
            csv_data = match.group(1).strip()
            
            st.markdown("---")
            st.success("Análise finalizada. Baixe os dados para Excel abaixo:")
            
            st.download_button(
                label="Baixar Planilha (.csv)",
                data=csv_data,
                file_name="auditoria_juridica.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ O relatório foi gerado, mas o sistema não encontrou o bloco de dados CSV para download automático.")

    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")


