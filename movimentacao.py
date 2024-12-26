import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime




def main():
# Configuração inicial do Streamlit
 st.title("Relatório Kardex")
 
# Upload do arquivo CSV
uploaded_file = st.file_uploader("Carregue o arquivo CSV", type="csv")

if uploaded_file:
    # Carregar o arquivo CSV em um DataFrame, usando ponto e vírgula como delimitador
    df = pd.read_csv(uploaded_file, delimiter=';')

  
    # Configurar o Pandas para exibir mais colunas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    # Conversão dos campos necessários para os tipos apropriados
    df['DTAENTRADASAIDA'] = pd.to_datetime(df['DTAENTRADASAIDA'])
    df['QTDLANCTO'] = pd.to_numeric(df['QTDLANCTO'].str.replace(',', '.'), errors='coerce')
    df['VALORVLRNF'] = pd.to_numeric(df['VALORVLRNF'].str.replace(',', '.'), errors='coerce')

      # Verificar se o DataFrame já foi carregado
    if 'df' in st.session_state:
        df = st.session_state['df']

    # Filtros
   # nroempresa = st.text_input("Empresa (NROEMPRESA)", key="nroempresa")
    nroempresa = df['NROEMPRESA'].unique()  # Obter lista de lojas únicas
    nroempresa_selecionada = st.selectbox('Selecione o Código da Loja', sorted(nroempresa))
    cgo = st.text_input("CGO (CODGERALOPER)", key="cgo")
    seqproduto = st.text_input("Produto (SEQPRODUTO)", key="seqproduto")

    # Filtro de período inicial
    st.write("### Filtro de Período Inicial")
    periodo_inicial_str = st.text_input("Digite a data no formato dd/mm/aaaa:", value="", key="periodo_inicial_str")
    try:
        periodo_inicial = datetime.strptime(periodo_inicial_str, "%d/%m/%Y") if periodo_inicial_str else None
    except ValueError:
        st.error("Formato inválido. Use dd/mm/aaaa.")
        periodo_inicial = None

    # Filtro de período final
    st.write("### Filtro de Período Final")
    periodo_final_str = st.text_input("Digite a data no formato dd/mm/aaaa:", value="", key="periodo_final_str")
    try:
        periodo_final = datetime.strptime(periodo_final_str, "%d/%m/%Y") if periodo_final_str else None
    except ValueError:
        st.error("Formato inválido. Use dd/mm/aaaa.")
        periodo_final = None

    # Adiciona a opção de escolher a data pelo calendário (inicia vazio)
    periodo_inicial_calendario = st.date_input("Ou selecione a data inicial:", value=None, key="calendario_inicial")
    periodo_final_calendario = st.date_input("Ou selecione a data final:", value=None, key="calendario_final")

    # Usa o valor preenchido manualmente ou pelo calendário
    if not periodo_inicial:
        periodo_inicial = periodo_inicial_calendario
    if not periodo_final:
        periodo_final = periodo_final_calendario

    local = st.text_input("Local (LOCAL)", key="local")
    gera_estoque_gerencial = st.selectbox("Gera Estoque Gerencial", ["Sim", "Não"], key="gera_estoque_gerencial")
    gera_estoque_fiscal = st.selectbox("Gera Estoque Fiscal", ["Sim", "Não"], key="gera_estoque_fiscal")

    # Aplicar os filtros ao DataFrame
    if nroempresa:
        df = df[df['NROEMPRESA'] == int(nroempresa_selecionada)]
    if cgo:
        df = df[df['CODGERALOPER'] == int(cgo)]
    if seqproduto:
        df = df[df['SEQPRODUTO'] == int(seqproduto)]
    if periodo_inicial and periodo_final:
        df = df[(df['DTAENTRADASAIDA'] >= periodo_inicial) & (df['DTAENTRADASAIDA'] <= periodo_final)]
    if local:
        df = df[df['LOCAL'] == local]

    # Gerenciar os campos de estoque gerencial e fiscal
    if gera_estoque_gerencial == "Sim":
        df = df[df['GERALTERACAOESTQ'] == "S"]
    elif gera_estoque_gerencial == "Não":
        df = df[df['GERALTERACAOESTQ'] == "N"]

    if gera_estoque_fiscal == "Sim":
        df = df[df['GERALTERACAOESTQFISC'] == "S"]
    elif gera_estoque_fiscal == "Não":
        df = df[df['GERALTERACAOESTQFISC'] == "N"]

    # Adicionar coloração às movimentações
    def apply_color(row):
        if row['TIPLANCTO'] == "E":
            return ["background-color: blue; color: white"] * len(row)
        elif row['TIPLANCTO'] == "S":
            return ["background-color: yellow; color: black"] * len(row)
        elif pd.isna(row['GERALTERACAOESTQFISC']) or row['GERALTERACAOESTQFISC'] == "N":
            return ["background-color: red; color: white"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(apply_color, axis=1)

    # Exibir o relatório
    st.write("### Relatório Kardex")
    st.dataframe(styled_df)

    # Calcular totais
    total_entradas = df[df['TIPLANCTO'] == "E"]['QTDLANCTO'].sum()
    total_saidas = df[df['TIPLANCTO'] == "S"]['QTDLANCTO'].sum()
    saldo = total_entradas - total_saidas

    # Exibir totais
    st.write("### Totais")
    st.write(f"Total de Entradas: **{total_entradas:.3f}**")
    st.write(f"Total de Saídas: **{total_saidas:.3f}**")
    st.write(f"Saldo: **{'<span style=\"color:red;\">' if saldo < 0 else '<span style=\"color:blue;\">'}{saldo:.3f}</span>**", unsafe_allow_html=True)

    # Gráfico comparativo
    st.write("### Gráfico Comparativo")
    fig, ax = plt.subplots()
    ax.bar(["Entradas", "Saídas"], [total_entradas, total_saidas], color=["blue", "yellow"])
    ax.set_ylabel("Quantidade")
    ax.set_title("Comparativo Entradas vs. Saídas")
    st.pyplot(fig)

else:
    st.warning("Por favor, carregue um arquivo CSV para continuar.")

if __name__ == '__main__':
    main()
