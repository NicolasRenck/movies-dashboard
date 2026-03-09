import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================
# 🔹 CONFIGURAÇÃO INICIAL
# =====================
# Otimizando a responsividade e o título
st.set_page_config(page_title="Movies Dashboard", layout="wide")

# =====================
# 🔹 CARREGAMENTO E LIMPEZA DOS DADOS (CORRIGIDO)
# =====================
@st.cache_data
def load_data(path="data/movies.csv"):
    """
    Carrega e limpa o CSV.
    Adapta nomes de colunas (especialmente Rating e Votes) e converte tipos.
    """
    if not os.path.isfile(path):
        st.error(f"O arquivo {path} não foi encontrado. Certifique-se de que ele está no local correto.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return pd.DataFrame()

    # Normaliza nomes das colunas (minúsculas e sem espaços)
    df.columns = [c.lower().strip() for c in df.columns]

    # Cria a coluna release_year com tolerância a diferentes nomes
    if 'release_year' not in df.columns:
        if 'startyear' in df.columns:
            df['release_year'] = df['startyear']
        elif 'year' in df.columns:
            df['release_year'] = df['year']
        elif 'start_year' in df.columns:
            df['release_year'] = df['start_year']
        else:
            df['release_year'] = None 

    # Renomeia colunas comuns, incluindo o mapeamento corrigido para IMDb/TMDB
    rename = {}
    
    # 1. Nota (Rating)
    if 'vote_average' in df.columns and 'rating' not in df.columns:
        rename['vote_average'] = 'rating'
    if 'averagerating' in df.columns and 'rating' not in df.columns:
        rename['averagerating'] = 'rating' 

    # 2. Votos (Votes)
    if 'vote_count' in df.columns and 'votes' not in df.columns:
        rename['vote_count'] = 'votes'
    if 'numvotes' in df.columns and 'votes' not in df.columns:
        rename['numvotes'] = 'votes' 

    # 3. Runtime
    if 'runtime' in df.columns and 'runtimeminutes' not in df.columns:
        rename['runtime'] = 'runtimeminutes'
        
    if rename:
        df = df.rename(columns=rename)

    # Converte tipos
    if 'release_year' in df.columns:
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
        df = df.dropna(subset=['release_year']) # Remove linhas sem ano válido

    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

    if 'votes' in df.columns:
        df['votes'] = pd.to_numeric(df['votes'], errors='coerce')
        df['votes'] = df['votes'].fillna(0) # Zera votos NaN para evitar problemas nos filtros

    # Cria coluna de lista de gêneros
    if 'genres' in df.columns:
        # Garante que gêneros são strings antes de aplicar split
        df['genres_list'] = df['genres'].astype(str).fillna('').apply(lambda x: [g.strip() for g in x.split(',') if g.strip()])
    else:
        df['genres_list'] = [[]] * len(df) 

    return df


# =====================
# 🔹 CARREGAR OS DADOS
# =====================
df = load_data()

# Se o DataFrame estiver vazio, pare a execução do Streamlit
if df.empty:
    
    st.stop()

# =====================
# 🔹 SIDEBAR – FILTROS
# =====================
st.sidebar.header("Filtros")

# Lógica de Ano (Aprimorada para robustez)
year_col = 'release_year'
if year_col in df.columns and df[year_col].notna().any():
    # Garantir que min/max são inteiros e não NaN
    year_min = int(df[year_col].min(skipna=True))
    year_max = int(df[year_col].max(skipna=True))
else:
    year_min, year_max = 1900, 2025 # Default robusto

year_range = st.sidebar.slider(
    "Ano de lançamento",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1
)


genres = sorted(set([g for sublist in df['genres_list'] for g in sublist if g]))
selected_genres = st.sidebar.multiselect("Gêneros", genres)

# Lógica de Votos (Aprimorada para robustez)
votes_col = 'votes'
if votes_col in df.columns:
    min_votes = int(df[votes_col].min(skipna=True))
    max_votes = int(df[votes_col].max(skipna=True))
else:
    min_votes, max_votes = 0, 1000000

vote_range = st.sidebar.slider(
    "Número de votos",
    min_value=min_votes,
    max_value=max_votes,
    value=(min_votes, max_votes)
)

# =====================
# 🔹 FILTRAR DADOS
# =====================
filtered_df = df.copy()

# Aplicação dos filtros
if year_col in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df[year_col] >= year_range[0]) &
        (filtered_df[year_col] <= year_range[1])
    ]

if selected_genres:
    filtered_df = filtered_df[
        filtered_df['genres_list'].apply(lambda g: any(genre in g for genre in selected_genres))
    ]

if votes_col in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df[votes_col] >= vote_range[0]) &
        (filtered_df[votes_col] <= vote_range[1])
    ]

# =====================
# 🔹 TÍTULO E INTRODUÇÃO
# =====================
st.title("Movies Dashboard")

st.markdown(
    "Este painel permite visualizar dados de filmes, como notas, votos e gêneros. "
    "Use os filtros à esquerda para refinar sua análise."
)

st.markdown("---")

## 2. Indicadores Chave (KPIs)

# Verifica se o DataFrame filtrado está vazio
if filtered_df.empty:
    st.warning("**Nenhum filme encontrado** com os filtros selecionados. Tente ajustar o ano, gênero ou número de votos.")
    st.stop() # Para a execução aqui se não houver dados


total_filmes = len(filtered_df)
media_rating = filtered_df['rating'].mean().round(2) if 'rating' in filtered_df.columns else 0
total_votos = filtered_df['votes'].sum() if 'votes' in filtered_df.columns else 0

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    st.metric(label="Total de Filmes", value=total_filmes)

with col_kpi2:
    st.metric(label="Média de Nota (Rating)", value=f"{media_rating:.2f}")

with col_kpi3:
    st.metric(label="Total de Votos (Sum)", value=f"{total_votos:,.0f}")

st.markdown("---")


# =====================
# 🔹 GRÁFICOS
# =====================
col1, col2 = st.columns(2)

# Gráfico 1: Média de Notas por Ano
with col1:
    st.subheader("Tendência de Notas ao Longo do Tempo")
    if year_col in filtered_df.columns and 'rating' in filtered_df.columns:
        # Garante que os dados do gráfico não são NaN
        avg_rating = (
            filtered_df.groupby(year_col)['rating']
            .mean()
            .reset_index()
            .sort_values(year_col)
            .dropna(subset=['rating']) # Remove anos sem nota
        )
        if not avg_rating.empty:
            fig_line = px.line(
                avg_rating, x=year_col, y='rating',
                title="Média de notas por ano",
                labels={year_col: 'Ano de Lançamento', 'rating': 'Média de Nota'},
                height=400 # Altura fixa para melhor layout
            )
            # Adiciona uma linha suave e marcadores
            fig_line.update_traces(mode='lines+markers')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Nenhuma média de nota calculável para o período selecionado.")

# Gráfico 2: Top Gêneros por Média de Nota
with col2:
    st.subheader("Ranking de Gêneros")
    if 'genres_list' in filtered_df.columns and 'rating' in filtered_df.columns:
        # Remove linhas onde a lista de gêneros está vazia
        temp_df = filtered_df[filtered_df['genres_list'].apply(bool)].copy()
        
        if not temp_df.empty:
            # Explode a lista de gêneros para uma linha por gênero/filme
            genres_df = temp_df.explode('genres_list')
            
            # Calcula a média de notas por gênero
            genre_rating = (
                genres_df.groupby('genres_list')['rating']
                .mean()
                .reset_index()
                .sort_values('rating', ascending=False)
                .head(10)  # Top 10 gêneros por nota média
            )
            
            if not genre_rating.empty:
                # Cria e exibe o gráfico de barras
                fig_bar = px.bar(
                    genre_rating, x='rating', y='genres_list',
                    orientation='h',
                    title=" Top 10 Gêneros por Nota Média",
                    labels={'rating': 'Média de Nota', 'genres_list': 'Gênero'},
                    height=400 
                )
                # Inverte o eixo Y para o maior valor no topo
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Não foi possível calcular a média de notas para os gêneros selecionados.")
        else:
            st.info("Nenhum gênero disponível com os filtros aplicados.")