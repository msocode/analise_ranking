"""
Bot de web scraping para o ranking guardmissions (semanal).
Usa a API pública em https://rankingtc.squareweb.app/classic/semanais/guardmissions
para obter os dados do top 10 (Rank, Nick, Pontos) da aba Semanal.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

RANKING_URL = "https://rankingtc.squareweb.app/classic/semanais/guardmissions"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "rankings_history.csv"
TOP_N = 10


def fetch_ranking() -> list[dict]:
    """
    Busca os dados do ranking via API.
    Retorna lista de dicts com rank, nick, pontos.
    """
    try:
        response = requests.get(RANKING_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error("Erro ao buscar ranking: %s", e)
        raise
    except json.JSONDecodeError as e:
        logger.error("Erro ao decodificar JSON: %s", e)
        raise

    if not isinstance(data, list):
        logger.error("Resposta da API não é uma lista: %s", type(data))
        raise ValueError("Formato de resposta inesperado")

    return data


def extract_top_n(ranking_data: list[dict], n: int = TOP_N) -> list[dict]:
    """
    Extrai os top N do ranking.
    Campos: rank, nick (rname), pontos.
    """
    result = []
    for i, item in enumerate(ranking_data[:n]):
        try:
            result.append({
                "rank": int(item.get("rank", i + 1)),
                "nick": str(item.get("rname", "")).strip(),
                "pontos": int(item.get("pontos", 0)),
            })
        except (ValueError, TypeError) as e:
            logger.warning("Item %s ignorado: %s", item, e)
    return result


def save_rankings(top_data: list[dict], timestamp: datetime) -> None:
    """
    Salva os dados em CSV por execução e atualiza o histórico.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    ts_str = timestamp.strftime("%Y%m%d_%H%M")
    ts_display = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # DataFrame com timestamp
    rows = [
        {"timestamp": ts_display, "rank": r["rank"], "nick": r["nick"], "pontos": r["pontos"]}
        for r in top_data
    ]
    df = pd.DataFrame(rows)

    # Arquivo por execução
    snapshot_file = DATA_DIR / f"rankings_{ts_str}.csv"
    df.to_csv(snapshot_file, index=False)
    logger.info("Salvo: %s", snapshot_file)

    # Histórico consolidado (append)
    file_exists = HISTORY_FILE.exists()
    df.to_csv(
        HISTORY_FILE,
        mode="a",
        header=not file_exists,
        index=False,
    )
    logger.info("Histórico atualizado: %s", HISTORY_FILE)


def run(headless: bool = True) -> list[dict]:
    """
    Executa uma captura completa: busca, extrai top 10, salva.
    Retorna os dados extraídos.
    """
    timestamp = datetime.now()
    logger.info("Iniciando captura em %s", timestamp)

    ranking_data = fetch_ranking()
    top_data = extract_top_n(ranking_data)

    if not top_data:
        logger.warning("Nenhum dado extraído")
        return []

    save_rankings(top_data, timestamp)
    logger.info("Captura concluída: %d registros", len(top_data))
    return top_data


if __name__ == "__main__":
    run()
