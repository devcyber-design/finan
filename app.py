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

def get_categories(transaction_type):
    """Retorna as categorias baseadas no tipo de transação"""
    income_categories = ["Salário", "Investimento", "Freelance", "Presente", "Vendas", "Outros"]
    expense_categories = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Contas", "Compras", "Outros"]
    
    if transaction_type == "Receita":
        return income_categories
    else:
        return expense_categories

# --- Layout ---
st.set_page_config(page_title="Dashboard Financeiro", page_icon="💰", layout="wide")

# --- Inicialização ---
if "df" not in st.session_state:
    st.session_state.df = load_data()
if "page" not in st.session_state:
    st.session_state.page = "visao_geral"
if "analise_tipo" not in st.session_state:
    st.session_state.analise_tipo = "despesas"
if "transaction_type" not in st.session_state:
    st.session_state.transaction_type = "Receita"

# --- Dados ---
df = st.session_state.df.copy()
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# --- HEADER COM BOTÕES DE NAVEGAÇÃO ---
st.title("💰 Dashboard Financeiro")

# Criar quatro colunas para os botões (agora com Visão Geral)
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Visão Geral", use_container_width=True):
        st.session_state.page = "visao_geral"

with col2:
    if st.button("➕ Lançamentos", use_container_width=True):
        st.session_state.page = "lancamento"

with col3:
    if st.button("📊 Análise", use_container_width=True):
        st.session_state.page = "analise"

with col4:
    if st.button("📅 Histórico", use_container_width=True):
        st.session_state.page = "historico"

st.divider()

# --- BLOCO DE MÉTRICAS FIXAS (sempre visível quando há dados) ---
if not df.empty:
    df["Sinal"] = df["Tipo"].apply(lambda x: 1 if x == "Receita" else -1)
    df["Valor Ajustado"] = df["Valor"] * df["Sinal"]
    total_balance = df["Valor Ajustado"].sum()
    total_income = df[df["Tipo"] == "Receita"]["Valor"].sum()
    total_expense = df[df["Tipo"] == "Despesa"]["Valor"].sum()

    # Métricas principais - altura reduzida
    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f"<div style='background:#2E8B57;padding:10px;border-radius:10px;text-align:center;color:white'>"
        f"<h4 style='margin:0;font-size:14px;'>💰 Saldo Total</h4><h3 style='margin:0;font-size:18px;'>R$ {total_balance:,.2f}</h3></div>",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"<div style='background:#1E90FF;padding:10px;border-radius:10px;text-align:center;color:white'>"
        f"<h4 style='margin:0;font-size:14px;'>⬆️ Total de Receitas</h4><h3 style='margin:0;font-size:18px;'>R$ {total_income:,.2f}</h3></div>",
        unsafe_allow_html=True,
    )
    col3.markdown(
        f"<div style='background:#DC143C;padding:10px;border-radius:10px;text-align:center;color:white'>"
        f"<h4 style='margin:0;font-size:14px;'>⬇️ Total de Despesas</h4><h3 style='margin:0;font-size:18px;'>R$ {total_expense:,.2f}</h3></div>",
        unsafe_allow_html=True,
    )
    
    st.divider()

# --- Página: VISÃO GERAL (Dashboard Principal) ---
if st.session_state.page == "visao_geral":
    st.subheader("🏠 Visão Geral")

    if df.empty:
        st.info("Nenhuma transação registrada ainda. Use o botão 'Lançamentos' para adicionar sua primeira transação.")
    else:
        # Gráficos principais
        col1, col2 = st.columns(2)

        with col1:
            # --- Gráfico de evolução mensal ---
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
                title="📈 Evolução Mensal de Receitas e Despesas",
                color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # --- Gráficos de pizza para receitas e despesas ---
            tab1, tab2 = st.tabs(["Receitas", "Despesas"])
            
            with tab1:
                income_df = df[df["Tipo"] == "Receita"]
                if not income_df.empty:
                    summary = income_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        title="Distribuição de Receitas por Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Blues
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhuma receita registrada.")

            with tab2:
                expenses_df = df[df["Tipo"] == "Despesa"]
                if not expenses_df.empty:
                    summary = expenses_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        title="Distribuição de Despesas por Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Reds
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhuma despesa registrada.")

# --- Página: ANÁLISE ---
elif st.session_state.page == "analise":
    st.subheader("📊 Análise de Transações")

    if df.empty:
        st.info("Nenhuma transação registrada ainda. Use o botão 'Lançamentos' para adicionar sua primeira transação.")
    else:
        # Submenu para tipos de análise
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🧾 Despesas", use_container_width=True):
                st.session_state.analise_tipo = "despesas"
        with col2:
            if st.button("💵 Receitas", use_container_width=True):
                st.session_state.analise_tipo = "receitas"
        with col3:
            if st.button("📅 Mensal", use_container_width=True):
                st.session_state.analise_tipo = "mensal"
        with col4:
            if st.button("📆 Anual", use_container_width=True):
                st.session_state.analise_tipo = "anual"

        st.divider()

        tipo = st.session_state.analise_tipo

        # 1️⃣ DESPESAS
        if tipo == "despesas":
            st.subheader("🧾 Despesas por Categoria")
            expenses_df = df[df["Tipo"] == "Despesa"]
            if not expenses_df.empty:
                summary = expenses_df.groupby("Categoria")["Valor"].sum().reset_index()
                fig = px.pie(
                    summary,
                    values="Valor",
                    names="Categoria",
                    title="Distribuição de Despesas por Categoria",
                    hole=0.3,
                    color_discrete_sequence=px.colors.sequential.Reds
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de detalhes
                st.subheader("📋 Detalhes das Despesas")
                st.dataframe(expenses_df[["Data", "Categoria", "Valor", "Descrição"]].sort_values("Data", ascending=False), use_container_width=True)
            else:
                st.info("Nenhuma despesa registrada.")

        # 2️⃣ RECEITAS
        elif tipo == "receitas":
            st.subheader("💵 Receitas por Categoria")
            income_df = df[df["Tipo"] == "Receita"]
            if not income_df.empty:
                summary = income_df.groupby("Categoria")["Valor"].sum().reset_index()
                fig = px.pie(
                    summary,
                    values="Valor",
                    names="Categoria",
                    title="Distribuição de Receitas por Categoria",
                    hole=0.3,
                    color_discrete_sequence=px.colors.sequential.Blues
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de detalhes
                st.subheader("📋 Detalhes das Receitas")
                st.dataframe(income_df[["Data", "Categoria", "Valor", "Descrição"]].sort_values("Data", ascending=False), use_container_width=True)
            else:
                st.info("Nenhuma receita registrada.")

        # 3️⃣ COMPARATIVO MENSAL
        elif tipo == "mensal":
            st.subheader("📅 Comparativo Mensal (Receita x Despesa)")
            df["Ano"] = df["Data"].dt.year
            df["Mês"] = df["Data"].dt.month_name(locale="pt_BR")
            monthly_summary = (
                df.groupby(["Ano", "Mês", "Tipo"])["Valor"]
                .sum()
                .reset_index()
                .sort_values(by=["Ano"])
            )
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

        # 4️⃣ COMPARATIVO ANUAL
        elif tipo == "anual":
            st.subheader("📆 Comparativo Anual (Receita x Despesa)")
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

# --- Página: HISTÓRICO ---
elif st.session_state.page == "historico":
    st.subheader("📅 Histórico de Transações")

    if df.empty:
        st.info("Nenhuma transação registrada. Use o botão 'Lançamentos' para adicionar sua primeira transação.")
    else:
        df_display = df.copy()
        df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y")
        df_display.reset_index(inplace=True)
        df_display.rename(columns={"index": "ID"}, inplace=True)
        
        st.dataframe(df_display[["ID", "Data", "Tipo", "Categoria", "Valor", "Descrição"]].sort_values(by="Data", ascending=False), 
                    use_container_width=True, 
                    height=400)

        st.divider()
        
        st.subheader("🗑️ Excluir Transação")
        selected_id = st.selectbox("Selecione o ID da transação:", df_display["ID"])
        selected_row = df_display.loc[df_display["ID"] == selected_id]
        st.write("**Transação selecionada:**")
        st.dataframe(selected_row, use_container_width=True)

        if st.button("Excluir Transação", type="secondary"):
            st.session_state.df = delete_transaction(st.session_state.df, selected_id)
            st.success("Transação excluída com sucesso!")
            st.rerun()

# --- Página: NOVO LANÇAMENTO ---
elif st.session_state.page == "lancamento":
    st.subheader("➕ Novo Lançamento")

    with st.form("novo_lancamento"):
        # Usar o valor atual do session_state como padrão
        transaction_type = st.radio(
            "Tipo de Transação", 
            ["Receita", "Despesa"], 
            horizontal=True,
            index=0 if st.session_state.transaction_type == "Receita" else 1
        )
        
        # Atualizar o session_state quando o usuário mudar a seleção
        st.session_state.transaction_type = transaction_type
        
        date = st.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")
        value = st.number_input("Valor", min_value=0.01, format="%.2f")
        description = st.text_input("Descrição (Opcional)")

        # Carregar categorias baseadas no tipo selecionado
        categories = get_categories(transaction_type)
        category = st.selectbox("Categoria", categories)

        # Apenas mostrar opção de parcelamento para despesas
        if transaction_type == "Despesa":
            recurring = st.checkbox("Despesa Parcelada / Recorrente")
            parcelas = 1
            if recurring:
                parcelas = st.number_input("Número de parcelas (meses)", min_value=2, max_value=36, value=2, step=1)
        else:
            recurring = False
            parcelas = 1

        submitted = st.form_submit_button("Salvar Lançamento", type="primary")
        
        if submitted:
            if value > 0:
                st.session_state.df = add_transaction(
                    st.session_state.df, date, transaction_type, category, value, description, parcelas
                )
                st.success(f"Lançamento de R$ {value:.2f} registrado com sucesso!")
                st.session_state.page = "visao_geral"
                st.rerun()
            else:
                st.error("O valor deve ser maior que zero.")