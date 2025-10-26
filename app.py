import streamlit as st
import plotly.express as px
import pandas as pd
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Configurações ---
FILE_PATH = "finances.csv"

# --- Funções de Dados ---
def load_data():
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
    else:
        df = pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Valor", "Descrição"])
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df

def save_data(df):
    df.to_csv(FILE_PATH, index=False)

def add_transaction(df, date, type, category, value, description, parcelas=1):
    new_rows = []
    for i in range(parcelas):
        parcela_date = date + relativedelta(months=i)
        desc = description
        if parcelas > 1:
            desc += f" ({i+1}/{parcelas})"
        new_rows.append({
            "Data": parcela_date,
            "Tipo": type,
            "Categoria": category,
            "Valor": value,
            "Descrição": desc
        })
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    save_data(df)
    return df

def delete_transaction(df, index):
    df = df.drop(index).reset_index(drop=True)
    save_data(df)
    return df

# --- Layout ---
st.set_page_config(page_title="Dashboard Financeiro", page_icon="💰", layout="centered")
st.title("💰 Dashboard Financeiro Completo")

# --- Dados ---
if "df" not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df.copy()
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# --- Navegação na Barra Lateral ---
selected_page = st.sidebar.radio(
    "Selecione a Página",
    ["📈 Visão Geral", "📊 Análises", "📅 Histórico", "➕ Novo Lançamento"],
    index=0,
)

# =======================
# 📈 VISÃO GERAL
# =======================
if selected_page == "📈 Visão Geral":
    st.subheader("💰 Visão Geral")
    if df.empty:
        st.info("Nenhuma transação registrada ainda.")
    else:
        df["Sinal"] = df["Tipo"].apply(lambda x: 1 if x == "Receita" else -1)
        df["Valor Ajustado"] = df["Valor"] * df["Sinal"]
        total_balance = df["Valor Ajustado"].sum()
        total_income = df[df["Tipo"] == "Receita"]["Valor"].sum()
        total_expense = df[df["Tipo"] == "Despesa"]["Valor"].sum()

        col1, col2, col3 = st.columns(3)
        col1.markdown(
            f"<div style='background:#2E8B57;padding:20px;border-radius:10px;text-align:center;color:white'>"
            f"<h4>💰 Saldo Total</h4><h2>R$ {total_balance:,.2f}</h2></div>",
            unsafe_allow_html=True,
        )
        col2.markdown(
            f"<div style='background:#1E90FF;padding:20px;border-radius:10px;text-align:center;color:white'>"
            f"<h4>⬆️ Receitas</h4><h2>R$ {total_income:,.2f}</h2></div>",
            unsafe_allow_html=True,
        )
        col3.markdown(
            f"<div style='background:#DC143C;padding:20px;border-radius:10px;text-align:center;color:white'>"
            f"<h4>⬇️ Despesas</h4><h2>R$ {total_expense:,.2f}</h2></div>",
            unsafe_allow_html=True,
        )

        # --- Gráfico mensal ---
        df["Ano"] = df["Data"].dt.year
        df["Mês"] = df["Data"].dt.month_name(locale="pt_BR")
        monthly_balance = df.groupby(["Ano", "Mês", "Tipo"])["Valor"].sum().reset_index()
        fig = px.bar(
            monthly_balance,
            x="Mês",
            y="Valor",
            color="Tipo",
            barmode="group",
            facet_col="Ano",
            title="📊 Evolução Mensal de Receitas e Despesas",
            color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
        )
        st.plotly_chart(fig, use_container_width=True)

# =======================
# 📊 ANÁLISES
# =======================
elif selected_page == "📊 Análises":
    st.subheader("📊 Análises de Transações")

    if df.empty:
        st.info("Nenhuma transação registrada.")
    else:
        analysis_type = st.radio(
            "Selecione o Tipo de Análise",
            ["🧾 Análise por Categoria", "📅 Comparativo Mensal", "📆 Comparativo Anual"],
            horizontal=True
        )

        # 1️⃣ Despesas e Receitas Lado a Lado
        if analysis_type == "🧾 Análise por Categoria":
            col_exp, col_inc = st.columns(2)

            # Despesas
            with col_exp:
                expenses_df = df[df["Tipo"] == "Despesa"]
                if not expenses_df.empty:
                    summary = expenses_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        title="Distribuição de Despesas por Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.qualitative.Set1
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhuma despesa registrada.")

            # Receitas
            with col_inc:
                income_df = df[df["Tipo"] == "Receita"]
                if not income_df.empty:
                    summary = income_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        title="Distribuição de Receitas por Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.qualitative.Pastel1
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhuma receita registrada.")

        # 3️⃣ Comparativo Mensal
        elif analysis_type == "📅 Comparativo Mensal":
            df["Ano"] = df["Data"].dt.year
            df["Mês"] = df["Data"].dt.month_name(locale="pt_BR")
            monthly_summary = df.groupby(["Ano", "Mês", "Tipo"])["Valor"].sum().reset_index()
            if not monthly_summary.empty:
                fig = px.bar(
                    monthly_summary,
                    x="Mês",
                    y="Valor",
                    color="Tipo",
                    barmode="group",
                    facet_col="Ano",
                    title="Comparativo Mensal por Ano",
                    color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados mensais para exibir.")

        # 4️⃣ Comparativo Anual
        elif analysis_type == "📆 Comparativo Anual":
            df["Ano"] = df["Data"].dt.year
            yearly_summary = df.groupby(["Ano", "Tipo"])["Valor"].sum().reset_index()
            if not yearly_summary.empty:
                fig = px.bar(
                    yearly_summary,
                    x="Ano",
                    y="Valor",
                    color="Tipo",
                    barmode="group",
                    title="Comparativo Anual de Receitas e Despesas",
                    color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados anuais para exibir.")

# =======================
# 📅 HISTÓRICO
# =======================
elif selected_page == "📅 Histórico":
    st.subheader("📅 Histórico de Transações")
    if df.empty:
        st.info("Nenhuma transação registrada.")
    else:
        df_display = df.copy()
        df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y")
        df_display.reset_index(inplace=True)
        df_display.rename(columns={"index": "ID"}, inplace=True)
        st.dataframe(df_display.sort_values(by="Data", ascending=False), use_container_width=True)

        st.subheader("🗑️ Excluir Transação")
        selected_id = st.selectbox("Selecione o ID da transação:", df_display["ID"])
        selected_row = df_display.loc[df_display["ID"] == selected_id]
        st.write("**Transação selecionada:**")
        st.dataframe(selected_row, use_container_width=True)

        if st.button("Excluir Transação", type="secondary"):
            st.session_state.df = delete_transaction(st.session_state.df, selected_id)
            st.success("Transação excluída com sucesso!")
            st.rerun()

# =======================
# ➕ NOVO LANÇAMENTO
# =======================
elif selected_page == "➕ Novo Lançamento":
    st.subheader("➕ Novo Lançamento")
    transaction_type = st.radio("Tipo de Transação", ["Receita", "Despesa"], horizontal=True)
    date = st.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")
    value = st.number_input("Valor", min_value=0.01, format="%.2f")
    description = st.text_input("Descrição (Opcional)")

    income_categories = ["Salário", "Investimento", "Freelance", "Outros"]
    expense_categories = ["Alimentação", "Transporte", "Moradia", "Lazer", "Contas", "Outros"]
    categories = income_categories if transaction_type == "Receita" else expense_categories
    category = st.selectbox("Categoria", categories)

    recurring = st.checkbox("Despesa Parcelada / Recorrente")
    parcelas = 1
    if recurring:
        parcelas = st.number_input("Número de parcelas (meses)", min_value=2, max_value=36, value=2, step=1)

    if st.button("Salvar Lançamento", type="primary"):
        if value > 0:
            st.session_state.df = add_transaction(
                st.session_state.df, date, transaction_type, category, value, description, parcelas
            )
            st.success(f"Lançamento de R$ {value:.2f} registrado com sucesso!")
            st.rerun()
        else:
            st.error("O valor deve ser maior que zero.")
