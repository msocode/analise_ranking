"""
Agendador para executar o scraper a cada 2 horas.
"""

import logging
import time

import schedule

from scraper.bot import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

INTERVAL_HOURS = 2


def job() -> None:
    """Tarefa agendada: executa o scraper."""
    try:
        run()
    except Exception as e:
        logger.exception("Erro na execução do scraper: %s", e)


def main() -> None:
    """Inicia o agendador e executa a primeira captura imediatamente."""
    logger.info("Agendando capturas a cada %d hora(s)", INTERVAL_HOURS)
    schedule.every(INTERVAL_HOURS).hours.do(job)

    # Primeira execução imediata
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
