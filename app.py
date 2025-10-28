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
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
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
st.set_page_config(page_title="Gestor Financeiro", page_icon="💰", layout="wide")

# --- CSS Personalizado para diminuir o espaço superior e otimizar espaço ---
st.markdown("""
<style>
/* 1. Máxima Redução de Margem Superior */
/* Altera o padding-top do bloco de conteúdo principal */
.css-1y4p8ic {
    padding-top: 0rem; 
}
/* Diminui padding no topo e nas laterais do conteúdo principal (para wide layout) */
section.main {
    padding-top: 0rem; 
    padding-right: 1rem;
    padding-left: 1rem;
    padding-bottom: 0rem; 
}
/* Remove a margem superior do título (h1) que costuma empurrar o conteúdo */
h1 {
    margin-top: 0rem !important; 
    padding-top: 0rem !important;
}
/* Remove a margem superior dos subtítulos (h2) para subir o conteúdo da página atual */
h2 {
    margin-top: 0rem !important;
    padding-top: 0rem !important;
}
/* Diminui o espaçamento dos elementos (para caber em uma página) */
.stButton, .stRadio, .stSelectbox, .stTextInput, .stNumberInput {
    margin-bottom: -5px;
}
.stForm {
    padding-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)


# --- Inicialização do State ---
if "df" not in st.session_state:
    st.session_state.df = load_data()
if "page" not in st.session_state:
    st.session_state.page = "lancamento" # Inicia em Lançamentos
if "analise_tipo" not in st.session_state:
    st.session_state.analise_tipo = "despesas"
if "transaction_type" not in st.session_state:
    st.session_state.transaction_type = "Receita"

# --- Dados ---
df = st.session_state.df.copy()
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# ----------------------------------------------------------------------------------
# --- NAVEGAÇÃO NA SIDEBAR (Barra Lateral) ---
# ----------------------------------------------------------------------------------

st.sidebar.title("Gestor Financeiro")

# Mapeamento para os botões
pages = {
    "➕ Lançamento": "lancamento",
    "🏠 Visão Geral": "visao_geral",
    "📊 Análise": "analise",
    "📅 Histórico": "historico"
}

# Cria os botões de navegação no sidebar
for label, key in pages.items():
    # Define o botão ativo como 'primary'
    button_type = "primary" if st.session_state.page == key else "secondary"
    
    # Se o botão for clicado, atualiza o estado e força o rerun
    if st.sidebar.button(label, use_container_width=True, type=button_type):
        st.session_state.page = key
        
        # SOLUÇÃO JAVASCRIPT: Força o recolhimento da sidebar em modo móvel
        st.markdown("""
        <script>
            function collapseSidebar() {
                // Tenta encontrar e clicar no botão de fechar (menu hamburger)
                const closeButton = document.querySelector('button[aria-label="Close sidebar"]') ||
                                    document.querySelector('button[aria-label="Fechar Menu"]');
                if (closeButton) {
                    closeButton.click();
                }
            }
            // Executa após um breve atraso para garantir que o Streamlit terminou o processamento
            setTimeout(collapseSidebar, 50);
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun() # Re-executa o script com a nova página
    
st.sidebar.markdown("---")
st.sidebar.caption("Gestor Financeiro v1.0")


# ----------------------------------------------------------------------------------
# --- HEADER E LAYOUT DE DUAS COLUNAS ---
# ----------------------------------------------------------------------------------

# Divide o espaço de exibição em duas colunas (70% para o conteúdo, 30% para as métricas)
main_col, metric_col = st.columns([3, 1])

# --- BLOCO DE MÉTRICAS FIXAS (Coluna da Direita) ---
with metric_col:
    # Apenas exibe as métricas se houver dados
    if not df.empty:
        df["Sinal"] = df["Tipo"].apply(lambda x: 1 if x == "Receita" else -1)
        df["Valor Ajustado"] = df["Valor"] * df["Sinal"]
        total_balance = df["Valor Ajustado"].sum()
        total_income = df[df["Tipo"] == "Receita"]["Valor"].sum()
        total_expense = df[df["Tipo"] == "Despesa"]["Valor"].sum()
        
        # TÍTULO "RESUMO" CENTRALIZADO E AJUSTADO
        st.markdown("<h3 style='text-align: center; margin-top: 0; margin-bottom: 0.5rem;'>Resumo</h3>", unsafe_allow_html=True) 

        # Métricas empilhadas verticalmente para caber na coluna estreita
        st.markdown(
            f"<div style='background:#2E8B57;padding:8px;border-radius:8px;text-align:center;color:white; margin-bottom: 5px;'>"
            f"<h4 style='margin:0;font-size:12px;'>💰 Saldo Total</h4><h3 style='margin:0;font-size:16px;'>R$ {total_balance:,.2f}</h3></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background:#1E90FF;padding:8px;border-radius:8px;text-align:center;color:white; margin-bottom: 5px;'>"
            f"<h4 style='margin:0;font-size:12px;'>⬆️ Total de Receitas</h4><h3 style='margin:0;font-size:16px;'>R$ {total_income:,.2f}</h3></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background:#DC143C;padding:8px;border-radius:8px;text-align:center;color:white; margin-bottom: 5px;'>"
            f"<h4 style='margin:0;font-size:12px;'>⬇️ Total de Despesas</h4><h3 style='margin:0;font-size:16px;'>R$ {total_expense:,.2f}</h3></div>",
            unsafe_allow_html=True,
        )
        st.divider()


# ----------------------------------------------------------------------------------
# --- CONTEÚDO DA PÁGINA ATUAL (Coluna da Esquerda - Main) ---
# ----------------------------------------------------------------------------------
with main_col:
    
    # --- Página: NOVO LANÇAMENTO ---
    if st.session_state.page == "lancamento":
        st.subheader("💰 Gestor Financeiro")

        # Seleção do Tipo de Transação
        transaction_type = st.radio(
            "Tipo de Transação", 
            ["Receita", "Despesa"], 
            horizontal=True,
            index=0 if st.session_state.transaction_type == "Receita" else 1,
            key="transaction_type_radio"
        )
        st.session_state.transaction_type = transaction_type # Atualiza o state
        st.markdown("---")

        with st.form("novo_lancamento"):
            
            col_date, col_value = st.columns(2)
            with col_date:
                 date = st.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")
            with col_value:
                 value = st.number_input("Valor", min_value=0.01, format="%.2f", key="value_input")
                 
            description = st.text_input("Descrição (Opcional)", key="description_input")

            # Carregar categorias baseadas no tipo selecionado
            categories = get_categories(transaction_type)
            category = st.selectbox("Categoria", categories, key="category_select")

            # Opção de parcelamento/recorrência
            parcelas = 1
            recurring = False
            
            if transaction_type == "Despesa":
                recurring = st.checkbox("Despesa Parcelada / Recorrente", key="recurring_checkbox")
                
                if recurring:
                    parcelas = st.number_input(
                        "Número de parcelas (meses)", 
                        min_value=2, 
                        max_value=36, 
                        value=2, 
                        step=1,
                        key="parcelas_input"
                    )
            
            submitted = st.form_submit_button("Salvar Lançamento", type="primary", use_container_width=True)
            
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

                    st.rerun()
                else:
                    st.error("O valor deve ser maior que zero.")

    # --- Página: VISÃO GERAL (Dashboard Principal) ---
    elif st.session_state.page == "visao_geral":
        st.subheader("🏠 Visão Geral")

        if df.empty:
            st.info("Nenhuma transação registrada ainda. Use a barra lateral para ir em 'Lançamentos' e adicionar sua primeira transação.")
        else:
            # Gráficos principais
            col_graph1, col_graph2 = st.columns(2) # Colunas internas para os gráficos

            with col_graph1:
                # --- Gráfico de evolução mensal ---
                df["Ano"] = df["Data"].dt.year
                month_names_pt_br = {
                    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 
                    5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 
                    9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
                }
                df["Mês"] = df["Data"].dt.month.map(month_names_pt_br)
                monthly_balance = df.groupby(["Ano", "Mês", "Tipo"])["Valor"].sum().reset_index()
                
                month_order = [
                    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                ]
                
                fig = px.bar(
                    monthly_balance,
                    x="Mês",
                    y="Valor",
                    color="Tipo",
                    barmode="group",
                    facet_col="Ano",
                    title="📈 Evolução Mensal (Receitas vs Despesas)",
                    color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                    category_orders={"Mês": month_order} 
                )
                fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10)) # Diminui a altura
                st.plotly_chart(fig, use_container_width=True)

            with col_graph2:
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
                            title="Distribuição de Receitas",
                            hole=0.3,
                            color_discrete_sequence=px.colors.sequential.Blues
                        )
                        fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10)) # Diminui a altura
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
                            title="Distribuição de Despesas",
                            hole=0.3,
                            color_discrete_sequence=px.colors.sequential.Reds
                        )
                        fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10)) # Diminui a altura
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Nenhuma despesa registrada.")

    # --- Página: ANÁLISE ---
    elif st.session_state.page == "analise":
        st.subheader("📊 Análise de Transações")

        if df.empty:
            st.info("Nenhuma transação registrada ainda.")
        else:
            # Submenu para tipos de análise
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🧾 Despesas", use_container_width=True, type="primary" if st.session_state.analise_tipo == "despesas" else "secondary"):
                    st.session_state.analise_tipo = "despesas"
                    st.rerun()  # <--- ADICIONADO PARA FORÇAR A ATUALIZAÇÃO
            with col2:
                if st.button("💵 Receitas", use_container_width=True, type="primary" if st.session_state.analise_tipo == "receitas" else "secondary"):
                    st.session_state.analise_tipo = "receitas"
                    st.rerun()  # <--- ADICIONADO PARA FORÇAR A ATUALIZAÇÃO
            with col3:
                if st.button("📅 Mensal", use_container_width=True, type="primary" if st.session_state.analise_tipo == "mensal" else "secondary"):
                    st.session_state.analise_tipo = "mensal"
                    st.rerun()  # <--- ADICIONADO PARA FORÇAR A ATUALIZAÇÃO
            with col4:
                if st.button("📆 Anual", use_container_width=True, type="primary" if st.session_state.analise_tipo == "anual" else "secondary"):
                    st.session_state.analise_tipo = "anual"
                    st.rerun()  # <--- ADICIONADO PARA FORÇAR A ATUALIZAÇÃO

            st.markdown("---")

            # ... (Restante do código da análise)
            tipo = st.session_state.analise_tipo

            # 1️⃣ DESPESAS
            if tipo == "despesas":
                st.caption("Distribuição de Despesas por Categoria")
                expenses_df = df[df["Tipo"] == "Despesa"]
                if not expenses_df.empty:
                    summary = expenses_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Reds
                    )
                    fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.caption("Detalhes das Despesas")
                    st.dataframe(expenses_df[["Data", "Categoria", "Valor", "Descrição"]].sort_values("Data", ascending=False), 
                                 use_container_width=True, height=200) # Altura reduzida
                else:
                    st.info("Nenhuma despesa registrada.")

            # 2️⃣ RECEITAS
            elif tipo == "receitas":
                st.caption("Distribuição de Receitas por Categoria")
                income_df = df[df["Tipo"] == "Receita"]
                if not income_df.empty:
                    summary = income_df.groupby("Categoria")["Valor"].sum().reset_index()
                    fig = px.pie(
                        summary,
                        values="Valor",
                        names="Categoria",
                        hole=0.3,
                        color_discrete_sequence=px.colors.sequential.Blues
                    )
                    fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.caption("Detalhes das Receitas")
                    st.dataframe(income_df[["Data", "Categoria", "Valor", "Descrição"]].sort_values("Data", ascending=False), 
                                 use_container_width=True, height=200) # Altura reduzida
                else:
                    st.info("Nenhuma receita registrada.")

            # 3️⃣ COMPARATIVO MENSAL
            elif tipo == "mensal":
                st.caption("Comparativo Mensal (Receita x Despesa)")
                df["Ano"] = df["Data"].dt.year
                month_names_pt_br = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                df["Mês"] = df["Data"].dt.month.map(month_names_pt_br)
                monthly_summary = df.groupby(["Ano", "Mês", "Tipo"])["Valor"].sum().reset_index()
                month_order = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                
                if not monthly_summary.empty:
                    fig = px.bar(
                        monthly_summary,
                        x="Mês",
                        y="Valor",
                        color="Tipo",
                        barmode="group",
                        facet_col="Ano",
                        color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                        category_orders={"Mês": month_order} 
                    )
                    fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados mensais para exibir.")

            # 4️⃣ COMPARATIVO ANUAL
            elif tipo == "anual":
                st.caption("Comparativo Anual (Receita x Despesa)")
                df["Ano"] = df["Data"].dt.year
                yearly_summary = df.groupby(["Ano", "Tipo"])["Valor"].sum().reset_index()
                if not yearly_summary.empty:
                    fig = px.bar(
                        yearly_summary,
                        x="Ano",
                        y="Valor",
                        color="Tipo",
                        barmode="group",
                        color_discrete_map={"Receita": "#1E90FF", "Despesa": "#DC143C"},
                    )
                    fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados anuais para exibir.")

    # --- Página: HISTÓRICO ---
    elif st.session_state.page == "historico":
        st.subheader("📅 Histórico de Transações")

        if df.empty:
            st.info("Nenhuma transação registrada.")
        else:
            df_display = df.copy()
            df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y")
            df_display.reset_index(inplace=True) 
            df_display.rename(columns={"index": "ID"}, inplace=True)
            
            valid_ids = df_display["ID"].tolist()
            
            # Altura reduzida para caber na página
            st.dataframe(df_display[["ID", "Data", "Tipo", "Categoria", "Valor", "Descrição"]].sort_values(by="Data", ascending=False), 
                        use_container_width=True, 
                        height=250)

            st.markdown("---")
            
            st.caption("🗑️ Excluir Transação")
            
            if valid_ids:
                default_id = valid_ids[0] if valid_ids else None
                try:
                    default_index = valid_ids.index(default_id)
                except ValueError:
                    default_index = 0
                    
                selected_id = st.selectbox("Selecione o ID da transação:", valid_ids, index=default_index)
                
                selected_row = df_display.loc[df_display["ID"] == selected_id]
                st.caption("Transação selecionada:")
                st.dataframe(selected_row, use_container_width=True)

                if st.button("Excluir Transação", type="secondary"):
                    st.session_state.df = delete_transaction(st.session_state.df, selected_id)
                    st.success("Transação excluída com sucesso!")
                    st.rerun()
            else:

                st.info("Nenhuma transação disponível para exclusão.")

