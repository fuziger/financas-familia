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
# Categorias atualizadas para bater com as metas
categorias_gastos = ["Mercado", "Combustível", "Lanches", "Emergências", "Saúde", "Educação", "Moradia", "Lazer", "Outros"]

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
            categoria = st.selectbox("Categoria", categorias_gastos)
        
        descricao = st.text_input("Descrição")
        if st.form_submit_button("Salvar Gasto"):
            if valor > 0:
                aba = conectar_planilha("Gastos")
                aba.append_row([data.strftime("%d/%m/%Y"), usuario, categoria, valor, descricao])
                st.success("Gasto registrado com sucesso!")
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
            if valor_res > 0:
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
        df_gastos = pd.DataFrame(conectar_planilha("Gastos").get_all_records())
        df_receitas = pd.DataFrame(conectar_planilha("Receitas").get_all_records())
        df_reserva = pd.DataFrame(conectar_planilha("Reserva de Emergência").get_all_records())
        
        # Leitura da nova aba de Metas
        try:
            df_metas = pd.DataFrame(conectar_planilha("Metas Semanais").get_all_records())
        except:
            df_metas = pd.DataFrame() # Caso a aba ainda não exista

        # --- RESUMO GERAL ---
        total_gastos = df_gastos['Valor'].sum() if not df_gastos.empty else 0.0
        total_receitas = df_receitas['Valor'].sum() if not df_receitas.empty else 0.0
        
        deposito_reserva = df_reserva['Valor Entrada'].sum() if not df_reserva.empty else 0.0
        resgate_reserva = df_reserva['Valor Saída'].sum() if not df_reserva.empty else 0.0
        
        saldo_atual = (total_receitas + resgate_reserva) - (total_gastos + deposito_reserva)
        total_acumulado_reserva = df_reserva['Total Acumulado'].iloc[-1] if not df_reserva.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Receitas Totais", f"R$ {total_receitas:,.2f}")
        c2.metric("Gastos Totais", f"R$ {total_gastos:,.2f}")
        c3.metric("Reserva Atual", f"R$ {total_acumulado_reserva:,.2f}")
        c4.metric("Saldo Disponível", f"R$ {saldo_atual:,.2f}")

        st.divider()

        # --- METAS SEMANAIS ---
        st.subheader("🎯 Acompanhamento de Metas Semanais (Mês Atual)")
        
        if not df_gastos.empty and not df_metas.empty:
            # Converte as datas para o formato do pandas para filtrar por mês e semana
            df_gastos['Data_Obj'] = pd.to_datetime(df_gastos['Data'], format='%d/%m/%Y', errors='coerce')
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            # Filtra os gastos apenas do mês corrente
            df_mes = df_gastos[(df_gastos['Data_Obj'].dt.month == mes_atual) & (df_gastos['Data_Obj'].dt.year == ano_atual)].copy()
            
            if not df_mes.empty:
                # Descobre a qual semana do ano cada gasto pertence
                df_mes['Semana'] = df_mes['Data_Obj'].dt.isocalendar().week
                
                # Coleta as metas definidas na planilha
                metas_dict = {
                    "Combustível": float(df_metas['Combustível'].iloc[0]) if 'Combustível' in df_metas else 0.0,
                    "Mercado": float(df_metas['Mercado'].iloc[0]) if 'Mercado' in df_metas else 0.0,
                    "Lanches": float(df_metas['Lanches'].iloc[0]) if 'Lanches' in df_metas else 0.0,
                    "Emergências": float(df_metas['Emergências'].iloc[0]) if 'Emergências' in df_metas else 0.0
                }
                
                # Agrupa a soma de gastos por semana e categoria
                gastos_semana = df_mes.groupby(['Semana', 'Categoria'])['Valor'].sum().unstack(fill_value=0)
                
                # Cria um painel sanfonado (expander) para cada semana encontrada no mês
                for semana in sorted(gastos_semana.index, reverse=True): # Da semana mais recente para a mais antiga
                    with st.expander(f"📅 Histórico - Semana {semana} do Ano", expanded=(semana == gastos_semana.index.max())):
                        cols_meta = st.columns(4)
                        categorias_alvo = ["Combustível", "Mercado", "Lanches", "Emergências"]
                        
                        for i, cat in enumerate(categorias_alvo):
                            gasto_real = gastos_semana.at[semana, cat] if cat in gastos_semana.columns else 0.0
                            meta_definida = metas_dict.get(cat, 0.0)
                            
                            # Calcula se sobrou ou faltou
                            saldo_meta = meta_definida - gasto_real
                            
                            # Se saldo for positivo (sobrou), fica verde/normal. Se negativo (estourou), fica vermelho/inverso.
                            if saldo_meta >= 0:
                                label_delta = f"+ R$ {saldo_meta:,.2f} (Sobrou)"
                                cor_delta = "normal"
                            else:
                                label_delta = f"R$ {saldo_meta:,.2f} (Déficit)"
                                cor_delta = "inverse"
                                
                            cols_meta[i].metric(label=f"Gasto c/ {cat}", value=f"R$ {gasto_real:,.2f}", delta=label_delta, delta_color=cor_delta)
            else:
                st.info("Nenhum gasto registrado no mês atual para comparar com as metas.")
        else:
            st.warning("⚠️ Para ver o histórico, certifique-se de que a aba 'Metas Semanais' está preenchida corretamente e que existem gastos lançados.")

        st.divider()

        # Gráfico simples de Gastos por Categoria
        if not df_gastos.empty:
            st.subheader("Distribuição Geral de Gastos")
            gastos_cat = df_gastos.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
            st.bar_chart(gastos_cat)

    except Exception as e:
        st.error(f"Erro ao carregar os dados. Verifique a estrutura da planilha. Detalhes: {e}")
