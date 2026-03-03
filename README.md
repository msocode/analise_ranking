# Ranking Guard Missions - Monitor

Bot de web scraping e dashboard para monitorar o top 10 do ranking **Semanal** de [Guard Missions](https://ranking.theclassic.games/rankings/classic/guardmissions) do The Classic Games. Os dados são obtidos via API (aba Semanal) e salvos a cada 2 horas. O dashboard permite analisar a evolução de pontos e calcular quanto cada jogador está subindo por hora.

## Estrutura

```
ranking/
├── scraper/
│   ├── bot.py          # Captura top 10 via API
│   └── scheduler.py    # Agendamento a cada 2 horas
├── data/               # CSVs de rankings (gerados automaticamente)
├── dashboard/
│   └── app.py          # Dashboard Streamlit
└── requirements.txt
```

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Captura única

```bash
python -m scraper.bot
```

Salva em `data/rankings_YYYYMMDD_HHMM.csv` e atualiza `data/rankings_history.csv`.

### Agendador (a cada 2 horas)

```bash
python -m scraper.scheduler
```

Mantém o processo rodando e executa a captura imediatamente e depois a cada 2 horas.

### Dashboard

```bash
streamlit run dashboard/app.py
```

Abre o navegador em `http://localhost:8501` com:

- Top 10 atual
- Tabela de pontos ganhos por hora
- Gráficos de evolução por jogador
- Filtro de período (7 dias, 30 dias, personalizado)
- Upload manual de CSV

## Alternativa: Task Scheduler (Windows)

Para rodar o scraper sem manter o Python ativo:

1. Abra o Agendador de Tarefas
2. Crie uma tarefa que execute a cada 2 horas:
   - Programa: `python`
   - Argumentos: `-m scraper.bot`
   - Diretório: pasta do projeto

## Formato dos dados

- **Por execução:** `timestamp`, `rank`, `nick`, `pontos`
- **Histórico:** mesmo formato, acumulado em `rankings_history.csv`
