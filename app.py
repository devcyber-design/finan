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
    """Carrega os dados do arquivo CSV ou cria um DataFrame vazio."""
    if os.path.exists(FILE_PATH):
        try:
            df = pd.read_csv(FILE_PATH)
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            df = pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Valor", "Descrição"])
    else:
        df = pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Valor", "Descrição"])
        
    # Garante que a coluna Data é do tipo datetime, tratando erros
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df

def save_data(df):
    """Salva o DataFrame no arquivo CSV."""
    df.to_csv(FILE_PATH, index=False)

def add_transaction(df, date, type, category, value, description, parcelas=1):
    """Adiciona uma transação, com suporte a parcelamento."""
    new_rows = []
    # Cria uma linha para cada parcela
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
    df.sort_values(by="Data", inplace=True) 
    save_data(df)
    return df

def delete_transaction(df, index):
    """Exclui uma transação pelo índice."""
    df = df.drop(index).reset_index(drop=True)
    save_data(df)
    return df

def get_categories(transaction_type):
    """Retorna as categorias baseadas no tipo de transação."""
    income_categories = ["Salário", "Investimento", "Freelance", "Presente", "Vendas", "Outros"]
    expense_categories = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Contas", "Compras", "Outros"]
    
    if transaction_type == "Receita":
        return income_categories
    else:
        return expense_categories

# --- Layout ---
st.set_page_config(page_title="Dash Money", page_icon="💰", layout="wide")

# --- Inicialização do State ---
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

# Criar quatro colunas para os botões
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
            # Mapeamento manual de meses para evitar problemas de locale e compatibilidade de versão do pandas.
            month_names_pt_br = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            df["Mês"] = df["Data"].dt.month.map(month_names_pt_br)
            monthly_balance = df.groupby(["Ano", "Mês", "Tipo"])["Valor"].sum().reset_index()
            
            # Ordenação manual dos meses para o Plotly não depender de locale
            month_order = [
                'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
            ]
            
            fig = px.bar(
                monthly_balance,
                x="Mês",
                y="Valor",
                color="Tipo",
                barmode="group",
                facet_col="Ano",
                title="📈 Evolução Mensal de Receitas e Despesas",
                color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                category_orders={"Mês": month_order} # Aplica a ordem correta
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
            # Mapeamento manual de meses para evitar problemas de locale e compatibilidade de versão do pandas.
            month_names_pt_br = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            df["Mês"] = df["Data"].dt.month.map(month_names_pt_br)
            
            monthly_summary = (
                df.groupby(["Ano", "Mês", "Tipo"])["Valor"]
                .sum()
                .reset_index()
            )
            
            # Ordenação manual dos meses
            month_order = [
                'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
            ]
            
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
                    category_orders={"Mês": month_order} # Aplica a ordem correta
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
        # Usar o índice do DataFrame original (df) para a exclusão
        df_display.reset_index(inplace=True) 
        df_display.rename(columns={"index": "ID"}, inplace=True)
        
        # Filtro para garantir que apenas IDs válidos sejam exibidos no selectbox
        valid_ids = df_display["ID"].tolist()
        
        st.dataframe(df_display[["ID", "Data", "Tipo", "Categoria", "Valor", "Descrição"]].sort_values(by="Data", ascending=False), 
                    use_container_width=True, 
                    height=400)

        st.divider()
        
        st.subheader("🗑️ Excluir Transação")
        
        # Apenas mostrar o selectbox se houver transações
        if valid_ids:
            # Garante que o selectbox tem um valor padrão válido
            default_id = valid_ids[0] if valid_ids else None
            
            selected_id = st.selectbox("Selecione o ID da transação:", valid_ids, index=valid_ids.index(default_id) if default_id in valid_ids else 0)
            
            selected_row = df_display.loc[df_display["ID"] == selected_id]
            st.write("**Transação selecionada:**")
            st.dataframe(selected_row, use_container_width=True)

            if st.button("Excluir Transação", type="secondary"):
                # Passar o ID (que é o índice do DataFrame original) para a função
                st.session_state.df = delete_transaction(st.session_state.df, selected_id)
                st.success("Transação excluída com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma transação disponível para exclusão.")


# --- Página: NOVO LANÇAMENTO (CORRIGIDA) ---
elif st.session_state.page == "lancamento":
    st.subheader("➕ Novo Lançamento")

    # FIX: MOVER A SELEÇÃO DO TIPO DE TRANSAÇÃO PARA FORA DO FORM
    # Isso garante que o Streamlit irá re-renderizar a página imediatamente quando o valor mudar,
    # carregando as categorias e opções de recorrência corretamente.
    transaction_type = st.radio(
        "Tipo de Transação", 
        ["Receita", "Despesa"], 
        horizontal=True,
        index=0 if st.session_state.transaction_type == "Receita" else 1,
        key="transaction_type_radio"
    )
    st.session_state.transaction_type = transaction_type # Atualiza o state
    st.divider()

    with st.form("novo_lancamento"):
        
        col_date, col_value = st.columns(2)
        with col_date:
             date = st.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")
        with col_value:
             value = st.number_input("Valor", min_value=0.01, format="%.2f", key="value_input")
             
        description = st.text_input("Descrição (Opcional)", key="description_input")

        # Carregar categorias baseadas no tipo selecionado (agora pega o valor ATUAL)
        categories = get_categories(transaction_type)
        category = st.selectbox("Categoria", categories, key="category_select")

        # Apenas mostrar opção de parcelamento/recorrência para despesas
        parcelas = 1
        recurring = False # Inicializa como False
        
        if transaction_type == "Despesa":
            st.subheader("Opções Adicionais")
            # Este bloco aparece corretamente quando transaction_type for "Despesa"
            recurring = st.checkbox("Despesa Parcelada / Recorrente", key="recurring_checkbox")
            
            if recurring:
                # O usuário pode usar "recorrente" para indicar despesas contínuas ou parceladas.
                # Se for recorrente, o número de parcelas indica quantos meses será repetido.
                parcelas = st.number_input(
                    "Número de parcelas (meses)", 
                    min_value=2, 
                    max_value=36, 
                    value=2, 
                    step=1,
                    key="parcelas_input"
                )
        
        submitted = st.form_submit_button("Salvar Lançamento", type="primary")
        
        if submitted:
            final_date = date
            
            if value > 0:
                st.session_state.df = add_transaction(
                    st.session_state.df, final_date, transaction_type, category, value, description, parcelas
                )
                
                if parcelas > 1:
                     st.success(f"Lançamento de R$ {value:.2f} registrado e parcelado em {parcelas} meses!")
                else:
                     st.success(f"Lançamento de R$ {value:.2f} registrado com sucesso!")

                # Redireciona para a visão geral após o sucesso
                st.session_state.page = "visao_geral"
                st.rerun()
            else:
                st.error("O valor deve ser maior que zero.")

