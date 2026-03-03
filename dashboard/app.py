"""
Dashboard Streamlit para análise do ranking guardmissions.
Monitora evolução de pontos e calcula pontos ganhos por hora.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "rankings_history.csv"


def load_data() -> pd.DataFrame:
    """Carrega o histórico de rankings."""
    if not HISTORY_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(HISTORY_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Carrega CSV enviado pelo usuário."""
    df = pd.read_csv(uploaded_file)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def compute_points_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula pontos ganhos por hora para cada jogador.
    Agrupa por nick, ordena por timestamp, calcula diferença entre capturas.
    """
    if df.empty or len(df) < 2:
        return pd.DataFrame()

    result = []
    for nick, group in df.groupby("nick"):
        group = group.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
        if len(group) < 2:
            continue
        group = group.reset_index(drop=True)
        for i in range(1, len(group)):
            prev = group.iloc[i - 1]
            curr = group.iloc[i]
            hours = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 3600
            if hours > 0:
                pts_diff = curr["pontos"] - prev["pontos"]
                pts_per_hour = pts_diff / hours
                result.append({
                    "nick": nick,
                    "timestamp": curr["timestamp"],
                    "pontos": curr["pontos"],
                    "pontos_anterior": prev["pontos"],
                    "horas_decorridas": round(hours, 2),
                    "pontos_por_hora": round(pts_per_hour, 2),
                })
    if not result:
        return pd.DataFrame()
    return pd.DataFrame(result)


def main() -> None:
    st.set_page_config(
        page_title="Ranking Guard Missions - Monitor",
        page_icon="📊",
        layout="wide",
    )
    st.title("📊 Ranking Guard Missions - Monitor")
    st.markdown("Monitoramento do top 10 e evolução de pontos por hora.")

    # Upload opcional
    uploaded = st.sidebar.file_uploader(
        "Importar CSV (opcional)",
        type=["csv"],
        help="Envie um CSV com colunas: timestamp, rank, nick, pontos",
    )

    if uploaded:
        df = load_uploaded_file(uploaded)
        st.sidebar.success("Dados do arquivo carregados.")
    else:
        df = load_data()

    if df.empty:
        st.warning(
            "Nenhum dado encontrado. Execute o scraper primeiro: "
            "`python -m scraper.bot` ou aguarde o scheduler."
        )
        st.info("Estrutura esperada do CSV: timestamp, rank, nick, pontos")
        return

    # Filtro de período
    st.sidebar.subheader("Filtro de período")
    min_ts = df["timestamp"].min()
    max_ts = df["timestamp"].max()
    period = st.sidebar.selectbox(
        "Período",
        ["Últimos 7 dias", "Últimos 30 dias", "Todo o histórico", "Personalizado"],
    )
    if period == "Últimos 7 dias":
        cutoff = max_ts - pd.Timedelta(days=7)
        df = df[df["timestamp"] >= cutoff]
    elif period == "Últimos 30 dias":
        cutoff = max_ts - pd.Timedelta(days=30)
        df = df[df["timestamp"] >= cutoff]
    elif period == "Personalizado":
        start = st.sidebar.date_input("Início", min_ts.date())
        end = st.sidebar.date_input("Fim", max_ts.date())
        df = df[
            (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
        ]

    if df.empty:
        st.warning("Nenhum dado no período selecionado.")
        return

    # Top 10 atual
    last_capture = df["timestamp"].max()
    top10 = df[df["timestamp"] == last_capture].sort_values("rank").head(10)
    st.subheader(f"Top 10 atual ({last_capture.strftime('%Y-%m-%d %H:%M')})")
    st.dataframe(
        top10[["rank", "nick", "pontos"]].set_index("rank"),
        use_container_width=True,
    )

    # Pontos por hora
    pts_hour = compute_points_per_hour(df)
    if not pts_hour.empty:
        st.subheader("Pontos ganhos por hora")
        latest_pts = pts_hour.sort_values("timestamp").groupby("nick").last().reset_index()
        latest_pts = latest_pts.sort_values("pontos_por_hora", ascending=False)
        st.dataframe(
            latest_pts[["nick", "pontos", "pontos_por_hora", "horas_decorridas"]],
            use_container_width=True,
        )

        # Gráfico de evolução por jogador
        st.subheader("Evolução de pontos por jogador")
        nicks = df["nick"].unique().tolist()
        selected = st.multiselect("Selecione os jogadores", nicks, default=nicks[:5])
        if selected:
            plot_df = df[df["nick"].isin(selected)]
            st.line_chart(
                plot_df.pivot_table(
                    index="timestamp",
                    columns="nick",
                    values="pontos",
                    aggfunc="first",
                ).ffill(),
            )

        # Gráfico de pontos/hora ao longo do tempo
        st.subheader("Pontos por hora ao longo do tempo")
        if not pts_hour.empty and "nick" in pts_hour.columns:
            pts_wide = pts_hour.pivot_table(
                index="timestamp",
                columns="nick",
                values="pontos_por_hora",
            )
            st.line_chart(pts_wide)
    else:
        st.info("É necessário pelo menos 2 capturas para calcular pontos por hora.")


if __name__ == "__main__":
    main()
