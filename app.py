import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração da página para Mobile
st.set_page_config(page_title="Finanças Família", page_icon="💰")

# Função para conectar ao Google Sheets usando as Secrets do Streamlit
def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Monta o dicionário de credenciais a partir dos Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    
    # Abre a planilha pelo ID fornecido
    return client.open_by_key(st.secrets["spreadsheet_id"]).sheet1

# Interface do Usuário
st.title("💰 Controle Financeiro")
st.subheader("Lançamento de Gastos")

with st.form("form_gastos", clear_on_submit=True):
    data = st.date_input("Data", datetime.now())
    
    # --- NOVO CAMPO: USUÁRIO ---
    usuario = st.selectbox("Quem está lançando?", ["Rafael", "Pamela", "Veronica", "Silvio"])
    
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoria", [
        "Mercado", 
        "Combustível/Transporte", 
        "Lazer/Lanche", 
        "Saúde", 
        "Educação", 
        "Moradia", 
        "Outros"
    ])
    descricao = st.text_input("Descrição (Ex: Almoço, Posto, etc.)")
    
    submit = st.form_submit_button("Salvar na Planilha")

if submit:
    if valor > 0:
        try:
            sheet = conectar_planilha()
            # Prepara a linha para inserir (Data, Usuário, Categoria, Valor, Descrição)
            nova_linha = [data.strftime("%d/%m/%Y"), usuario, categoria, valor, descricao]
            sheet.append_row(nova_linha)
            st.success(f"✅ Lançamento de {usuario} salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
    else:
        st.warning("Por favor, insira um valor maior que zero.")

st.info("Os dados são salvos diretamente na planilha privada da família.")
