import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página para mobile
st.set_page_config(page_title="Finanças da Família", layout="centered")

st.title("💰 Painel Financeiro Familiar")
st.subheader("Lançamento de Gastos e Receitas")

# Lista de categorias que você definiu
categorias = [
    "Mercado", "Combustível", "Água", "Energia Elétrica", 
    "Gás", "Lazer", "Lanches", "Assinaturas", 
    "Dívidas", "Reserva de Emergência", "Salários (Receita)"
]

# Formulário de entrada
with st.form("novo_lancamento", clear_on_submit=True):
    data = st.date_input("Data", date.today())
    categoria = st.selectbox("Selecione a Categoria", categorias)
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    descricao = st.text_input("Descrição (Ex: Compra do mês, Cinema...)")
    
    submit = st.form_submit_button("Registrar no Painel")

if submit:
    if valor > 0:
        st.success(f"Registrado: R$ {valor:.2f} em '{categoria}'!")
        # Aqui no futuro conectaremos a função de salvar na planilha
    else:
        st.warning("Por favor, insira um valor maior que zero.")

st.divider()
st.info("Dica: Adicione este link à tela inicial do seu celular para abrir como um app!")
