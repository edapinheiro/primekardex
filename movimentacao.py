import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

@st.cache_data
def load_data(uploaded_file):
    """
    Carrega e processa o arquivo CSV com cache para melhor performance
    """
    df = pd.read_csv(uploaded_file, delimiter=';')
    
    # Conversão dos campos necessários para os tipos apropriados
    df['DTAENTRADASAIDA'] = pd.to_datetime(df['DTAENTRADASAIDA'])
    df['QTDLANCTO'] = pd.to_numeric(df['QTDLANCTO'].str.replace(',', '.'), errors='coerce')
    df['VALORVLRNF'] = pd.to_numeric(df['VALORVLRNF'].str.replace(',', '.'), errors='coerce')
    
    return df

def apply_color(row):
    """
    Aplica cores às linhas do DataFrame baseado nas condições
    """
    if row['TIPLANCTO'] == "E":
        return ["background-color: blue; color: white"] * len(row)
    elif row['TIPLANCTO'] == "S":
        return ["background-color: yellow; color: black"] * len(row)
    elif pd.isna(row['GERALTERACAOESTQFISC']) or row['GERALTERACAOESTQFISC'] == "N":
        return ["background-color: red; color: white"] * len(row)
    return [""] * len(row)

def main():
    # Configuração inicial do Streamlit
    st.title("Relatório Kardex")
    
    # Upload do arquivo CSV
    uploaded_file = st.file_uploader("Carregue o arquivo CSV", type="csv")

    if uploaded_file:
        try:
            # Carregar o arquivo CSV em um DataFrame
            df = load_data(uploaded_file)
            
            # Configurar o Pandas para exibir mais colunas
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)

            # Filtros usando selectbox para todos os campos possíveis
            nroempresa = df['NROEMPRESA'].unique()
            nroempresa_selecionada = st.selectbox('Selecione o Código da Loja', sorted(nroempresa))
            
            # CGO com opção "Todos"
            cgo = list(df['CODGERALOPER'].unique())
            cgo.insert(0, "Todos")
            cgo_selecionado = st.selectbox('Selecione o CGO', cgo, index=0)
            
            seqproduto = df['SEQPRODUTO'].unique()
            seqproduto_selecionado = st.selectbox('Selecione o Produto', sorted(seqproduto))
            
            # Local com opção "Todos"
            local = list(df['LOCAL'].unique())
            local.insert(0, "Todos")
            local_selecionado = st.selectbox('Selecione o LOCAL', local, index=0)

            # Filtros de data
            st.write("### Filtro de Período")
            col1, col2 = st.columns(2)
            
            with col1:
                periodo_inicial_calendario = st.date_input("Data Inicial:", value=None)
            
            with col2:
                periodo_final_calendario = st.date_input("Data Final:", value=None)

            if periodo_inicial_calendario and periodo_final_calendario:
                if periodo_inicial_calendario > periodo_final_calendario:
                    st.error("Data inicial não pode ser maior que a data final")
                    return

            # Filtros de estoque com opção "Indiferente"
            gera_estoque_gerencial = st.selectbox("Gera Estoque Gerencial", 
                                                ["Indiferente", "Sim", "Não"], 
                                                index=0)
            gera_estoque_fiscal = st.selectbox("Gera Estoque Fiscal", 
                                             ["Indiferente", "Sim", "Não"], 
                                             index=0)

            # Aplicar os filtros ao DataFrame
            df_filtrado = df.copy()

            try:
                if nroempresa_selecionada:
                    df_filtrado = df_filtrado[df_filtrado['NROEMPRESA'] == nroempresa_selecionada]
                
                # Aplicar filtro CGO apenas se não for "Todos"
                if cgo_selecionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['CODGERALOPER'] == cgo_selecionado]
                
                if seqproduto_selecionado:
                    df_filtrado = df_filtrado[df_filtrado['SEQPRODUTO'] == seqproduto_selecionado]
                
                if periodo_inicial_calendario and periodo_final_calendario:
                    df_filtrado = df_filtrado[
                        (df_filtrado['DTAENTRADASAIDA'].dt.date >= periodo_inicial_calendario) &
                        (df_filtrado['DTAENTRADASAIDA'].dt.date <= periodo_final_calendario)
                    ]
                
                # Aplicar filtro LOCAL apenas se não for "Todos"
                if local_selecionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['LOCAL'] == local_selecionado]

                # Aplicar filtros de estoque apenas se não for "Indiferente"
                if gera_estoque_gerencial != "Indiferente":
                    valor_filtro = "S" if gera_estoque_gerencial == "Sim" else "N"
                    df_filtrado = df_filtrado[df_filtrado['GERALTERACAOESTQ'] == valor_filtro]

                if gera_estoque_fiscal != "Indiferente":
                    valor_filtro = "S" if gera_estoque_fiscal == "Sim" else "N"
                    df_filtrado = df_filtrado[df_filtrado['GERALTERACAOESTQFISC'] == valor_filtro]

            except Exception as e:
                st.error(f"Erro ao aplicar filtros: {str(e)}")
                return

            # Exibir o relatório com estilização
            st.write("### Relatório Kardex")
            styled_df = df_filtrado.style.apply(apply_color, axis=1)
            st.dataframe(styled_df)

            # Calcular e exibir totais
            total_entradas = df_filtrado[df_filtrado['TIPLANCTO'] == "E"]['QTDLANCTO'].sum()
            total_saidas = df_filtrado[df_filtrado['TIPLANCTO'] == "S"]['QTDLANCTO'].sum()
            saldo = total_entradas - total_saidas

            st.write("### Totais")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Entradas", f"{total_entradas:.3f}")
            
            with col2:
                st.metric("Total de Saídas", f"{total_saidas:.3f}")
            
            with col3:
                st.metric("Saldo", f"{saldo:.3f}", 
                         delta=f"{saldo:.3f}",
                         delta_color="normal" if saldo >= 0 else "inverse")

            # Gráfico comparativo
            st.write("### Gráfico Comparativo")
            fig, ax = plt.subplots(figsize=(10, 6))
            
            bars = ax.bar(["Entradas", "Saídas"], 
                         [total_entradas, total_saidas],
                         color=["blue", "yellow"])
            
            # Adicionar valores sobre as barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}',
                       ha='center', va='bottom')
            
            ax.set_ylabel("Quantidade")
            ax.set_title("Comparativo Entradas vs. Saídas")
            ax.grid(True, linestyle='--', alpha=0.7)
            
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")
            return

    else:
        st.warning("Por favor, carregue um arquivo CSV para continuar.")

if __name__ == '__main__':
    main()