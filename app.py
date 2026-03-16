import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Finanças Família", page_icon="📊", layout="wide")

# Função de conexão
def conectar_planilha(aba_nome):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(aba_nome)

# --- Navegação Lateral ---
st.sidebar.title("Menu Principal")
pagina = st.sidebar.radio("Ir para:", ["Dashboard de Análise", "Lançar Gastos", "Lançar Receitas"])

usuarios = ["Rafael", "Pamela", "Veronica", "Silvio"]

# --- PÁGINA: LANÇAR GASTOS ---
if pagina == "Lançar Gastos":
    st.header("💸 Lançar Novo Gasto")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", datetime.now())
            usuario = st.selectbox("Quem gastou?", usuarios)
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            categoria = st.selectbox("Categoria", ["Mercado", "Combustível", "Lazer", "Saúde", "Educação", "Outros"])
        
        descricao = st.text_input("Descrição")
        if st.form_submit_button("Salvar Gasto"):
            if valor > 0:
                aba = conectar_planilha("Página1") # Verifique se o nome da aba de gastos é este
                aba.append_row([data.strftime("%d/%m/%Y"), usuario, categoria, valor, descricao])
                st.success("Gasto registrado!")
            else:
                st.warning("Insira um valor válido.")

# --- PÁGINA: LANÇAR RECEITAS ---
elif pagina == "Lançar Receitas":
    st.header("💰 Registrar Receita (Entrada)")
    with st.form("form_receitas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", datetime.now())
            usuario = st.selectbox("Recebido por:", usuarios)
        with col2:
            valor = st.number_input("Valor da Entrada (R$)", min_value=0.0, step=0.01)
            descricao = st.text_input("Origem (Salário, Extra, etc.)")
            
        if st.form_submit_button("Salvar Receita"):
            if valor > 0:
                aba = conectar_planilha("Receitas") # Nome da nova aba criada no Google Sheets
                aba.append_row([data.strftime("%d/%m/%Y"), usuario, valor, descricao])
                st.success("Receita registrada!")

# --- PÁGINA: DASHBOARD ---
else:
    st.header("📊 Análise de Saldo Familiar")
    
    try:
        # Busca dados das duas abas
        df_gastos = pd.DataFrame(conectar_planilha("Página1").get_all_records())
        df_receitas = pd.DataFrame(conectar_planilha("Receitas").get_all_records())

        # Cálculos
        total_gastos = df_gastos['Valor'].sum() if not df_gastos.empty else 0.0
        total_receitas = df_receitas['Valor'].sum() if not df_receitas.empty else 0.0
        saldo_atual = total_receitas - total_gastos

        # Exibição de Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Receitas", f"R$ {total_receitas:,.2f}")
        c2.metric("Total de Gastos", f"R$ {total_gastos:,.2f}", delta_color="inverse")
        c3.metric("Saldo Disponível", f"R$ {saldo_atual:,.2f}", delta=f"{saldo_atual:,.2f}")

        # Gráfico simples de Gastos por Categoria
        if not df_gastos.empty:
            st.subheader("Gastos por Categoria")
            gastos_cat = df_gastos.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
            st.bar_chart(gastos_cat)
            
            st.subheader("Últimos Lançamentos")
            st.dataframe(df_gastos.tail(10), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar dados. Verifique se as abas 'Página1' e 'Receitas' existem. Detalhe: {e}")
