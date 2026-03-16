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
pagina = st.sidebar.radio("Ir para:", ["Dashboard de Análise", "Lançar Gastos", "Lançar Receitas", "Reserva de Emergência"])

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
            categoria = st.selectbox("Categoria", ["Mercado", "Combustível", "Lazer", "Saúde", "Educação", "Moradia", "Outros"])
        
        descricao = st.text_input("Descrição")
        if st.form_submit_button("Salvar Gasto"):
            if valor > 0:
                aba = conectar_planilha("Página1")
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
                aba = conectar_planilha("Receitas")
                aba.append_row([data.strftime("%d/%m/%Y"), usuario, valor, descricao])
                st.success("Receita registrada!")

# --- PÁGINA: RESERVA DE EMERGÊNCIA ---
elif pagina == "Reserva de Emergência":
    st.header("🛡️ Reserva de Emergência")
    
    aba_reserva = conectar_planilha("Reserva de Emergência")
    df_reserva = pd.DataFrame(aba_reserva.get_all_records())
    
    total_reserva = df_reserva['Total Acumulado'].iloc[-1] if not df_reserva.empty else 0.0
    st.metric("Total Acumulado na Reserva", f"R$ {total_reserva:,.2f}")

    with st.form("form_reserva", clear_on_submit=True):
        tipo = st.selectbox("Tipo de Movimentação", ["Depósito (Entrada)", "Resgate (Saída)"])
        valor_res = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        if st.form_submit_button("Confirmar Movimentação"):
            entrada = valor_res if "Depósito" in tipo else 0.0
            saida = valor_res if "Resgate" in tipo else 0.0
            novo_total = total_reserva + entrada - saida
            
            aba_reserva.append_row([datetime.now().strftime("%d/%m/%Y"), entrada, saida, novo_total])
            st.success("Movimentação na reserva registrada!")
            st.rerun()

# --- PÁGINA: DASHBOARD ---
else:
    st.header("📊 Análise de Saldo Familiar")
    
    try:
        df_gastos = pd.DataFrame(conectar_planilha("Página1").get_all_records())
        df_receitas = pd.DataFrame(conectar_planilha("Receitas").get_all_records())
        df_reserva = pd.DataFrame(conectar_planilha("Reserva de Emergência").get_all_records())

        total_gastos = df_gastos['Valor'].sum() if not df_gastos.empty else 0.0
        total_receitas = df_receitas['Valor'].sum() if not df_receitas.empty else 0.0
        
        # Lógica solicitada: 
        # Dinheiro que entrou na reserva SAIU do saldo disponível (débito)
        # Dinheiro que saiu da reserva ENTROU no saldo disponível (crédito)
        deposito_reserva = df_reserva['Valor Entrada'].sum() if not df_reserva.empty else 0.0
        resgate_reserva = df_reserva['Valor Saída'].sum() if not df_reserva.empty else 0.0
        
        saldo_atual = (total_receitas + resgate_reserva) - (total_gastos + deposito_reserva)
        total_acumulado_reserva = df_reserva['Total Acumulado'].iloc[-1] if not df_reserva.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Receitas Totais", f"R$ {total_receitas:,.2f}")
        c2.metric("Gastos Totais", f"R$ {total_gastos:,.2f}")
        c3.metric("Reserva Atual", f"R$ {total_acumulado_reserva:,.2f}")
        c4.metric("Saldo Disponível", f"R$ {saldo_atual:,.2f}")

        if not df_gastos.empty:
            st.subheader("Gastos por Categoria")
            st.bar_chart(df_gastos.groupby('Categoria')['Valor'].sum())

    except Exception as e:
        st.error(f"Erro ao carregar dados. Verifique os nomes das abas na planilha. {e}")
