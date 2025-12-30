import streamlit as st
import pandas as pd

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Sistema Financeiro",
    layout="centered"
)

st.title("📊 Sistema de Análises Financeiras")

# =========================================================
# FUNÇÕES UTILITÁRIAS
# =========================================================
def br_to_float(x):
    if isinstance(x, str):
        x = x.replace(".", "").replace(",", ".")
    return float(x)

def formatar_real(x):
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================================================
# FUNÇÃO: TOP PRESTADORES
# =========================================================
def top_prestadores(df, top_n, filtro_categoria="servi"):
    df.columns = df.columns.str.strip()

    COL_PRESTADOR = "Nome"
    COL_VALOR = "Valor categoria/centro de custo"
    COL_CATEGORIA = "Categoria"

    df = df[
        df[COL_CATEGORIA].str.contains(filtro_categoria, case=False, na=False)
    ].copy()

    df["Total Pago"] = df[COL_VALOR].abs()

    ranking = (
        df
        .groupby(COL_PRESTADOR, as_index=False)["Total Pago"]
        .sum()
        .sort_values(by="Total Pago", ascending=False)
        .head(top_n)
    )

    ranking["Total Pago (R$)"] = ranking["Total Pago"].apply(formatar_real)

    return ranking[[COL_PRESTADOR, "Total Pago (R$)"]]

# =========================================================
# FUNÇÃO: CONCILIAÇÃO ND
# =========================================================
def conciliar_nd(df, solicitante, valor_alvo):
    COLUNA_VALOR = "valor"
    COLUNA_DATA = "DT Recebimento"
    COLUNA_SOLICITANTE = "Solicitante"
    COLUNA_ND = "ND"

    df = df[
        df[COLUNA_DATA].isna() &
        (df[COLUNA_SOLICITANTE] == solicitante)
    ].copy()

    df[COLUNA_VALOR] = df[COLUNA_VALOR].apply(br_to_float)
    valor_alvo = br_to_float(valor_alvo)

    nd_totais = (
        df
        .groupby(COLUNA_ND)[COLUNA_VALOR]
        .sum()
        .reset_index()
    )

    valores = nd_totais[COLUNA_VALOR].tolist()
    nds = nd_totais[COLUNA_ND].tolist()

    ordenado = sorted(zip(valores, nds), reverse=True)
    valores, nds = zip(*ordenado) if ordenado else ([], [])

    resultado = []

    def busca(i, soma, comb):
        if abs(soma - valor_alvo) < 0.00001:
            resultado.append(comb)
            return True
        if soma > valor_alvo or i == len(valores):
            return False
        if busca(i + 1, soma + valores[i], comb + [i]):
            return True
        return busca(i + 1, soma, comb)

    busca(0, 0, [])

    saida = []

    if resultado:
        for idx in resultado[0]:
            saida.append({
                "ND": nds[idx],
                "Total": formatar_real(valores[idx])
            })

        total = formatar_real(sum(valores[idx] for idx in resultado[0]))
        return pd.DataFrame(saida), total

    return None, None

# =========================================================
# SIDEBAR - MENU
# =========================================================
st.sidebar.title("📌 Menu")
opcao = st.sidebar.radio(
    "Escolha a análise:",
    ["Top Prestadores", "Conciliação ND"]
)

arquivo = st.sidebar.file_uploader(
    "📂 Upload do arquivo Excel",
    type=["xlsx"]
)

# =========================================================
# TELA: TOP PRESTADORES
# =========================================================
if opcao == "Top Prestadores":
    st.subheader("🏆 Top Prestadores de Serviços")

    top_n = st.selectbox("Selecione o Top N", [5, 10, 20, 50])

    if arquivo and st.button("▶ Executar"):
        df = pd.read_excel(arquivo)
        resultado = top_prestadores(df, top_n)

        st.success("Resultado gerado com sucesso!")
        st.dataframe(resultado, use_container_width=True)

        st.caption("💡 Você pode selecionar e copiar direto para o Excel")

# =========================================================
# TELA: CONCILIAÇÃO ND
# =========================================================
if opcao == "Conciliação ND":
    st.subheader("🧾 Conciliação de ND")

    solicitante = st.text_input("Solicitante")
    valor_alvo = st.text_input("Valor alvo (ex: 1.500,00)")

    if arquivo and solicitante and valor_alvo and st.button("▶ Executar"):
        df = pd.read_excel(arquivo)
        resultado, total = conciliar_nd(df, solicitante, valor_alvo)

        if resultado is not None:
            st.success("Combinação encontrada!")
            st.dataframe(resultado, use_container_width=True)
            st.markdown(f"### ✔ Soma total: **{total}**")
        else:
            st.error("❌ Nenhuma combinação de ND fecha o valor alvo.")

