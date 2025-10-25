# b3-data-fetcher

> Personal API for analyzing Brazilian stocks and REITs (FIIs) using custom investment heuristics.

---

## About the project

The **b3-data-fetcher** started as a simple script built out of frustration —  
there’s **no good free or public API** for getting structured investment data from the **Brazilian market (B3)**.  

So this project aims to become a **fully open-source API** that anyone can download and run locally:  
you grab the official CSVs from **CVM** or **B3**, plug them into the tool, and it automatically processes and serves financial data through an API.

The long-term goal is to create a **self-contained investment data engine**: one that reads, cleans, and exposes metrics like **P/VP**, **Dividend Yield**, and other key ratios through a simple REST API — no external paid services required.

---

## General idea

Currently, it’s a terminal script that reads data from **CVM** and **Yahoo Finance**, merges them through **CNPJ ↔ ticker mapping**,  
and prints custom-calculated metrics like:
- Asset: PVBI11
- Book Value per Share: 107.784393
- Monthly DY: 0.004306
- Dividend (R$): 0.464119596258
- P/VP: 0.6958335795424483
- Price: 75.0


In the future, it will evolve into a **FastAPI-based REST API**, returning ranked asset lists based on a custom heuristic,  
with caching, database storage, and automatic CSV updates.

---

## Current heuristic

The project implements a **personal investment heuristic** that prioritizes “undervalued” assets by combining:  

- **Current Price** (from Yahoo Finance)  
- **Book Value per Share (VP/cota)** (from CVM data)  
- **P/VP ratio:** `price / vp_cota`  
- **Dividend Yield (DY)** (monthly yield over book value)  
- **Dividend in R$:** `vp_cota × dy_mês`  
- **Opportunity score:** a combination of DY and P/VP  

This logic helps find assets that are both **cheap relative to their patrimonial value** and **still paying good dividends**.

---

## Current structure
b3-data-fetcher/ <br>
├── main.py # main script (fetch & heuristic calculation) <br>
├── ativos.txt # list of assets (ticker, CNPJ) <br>
├── cache.mouras # local cache with timestamp <br>
├── .env # configuration (e.g., cache duration) <br>
└── data/ # CVM and B3 CSVs <br>


---

## Development checklist

### Done
- [x] Load and normalize CVM CSVs (`fii_geral`, `fii_complemento`, `fii_ativo_passivo`)
- [x] Calculate main indicators (book value, P/VP, DY, dividend) # For my degree final thesis
- [x] Integrate with Yahoo Finance for real-time prices
- [x] Implement basic caching system (`cache.mouras`)
- [x] Map CNPJs and tickers via `ativos.txt`

### In progress
- [ ] Create a minimal FastAPI server
- [ ] Endpoint `/assets` returning the data
- [ ] Add filtering parameters (e.g., FIIs only, P/VP < 1, DY > X%)
- [ ] Improve logging and error handling

### Future roadmap
- [ ] Store normalized data in a database (SQLite → PostgreSQL)
- [ ] Auto-update CVM/B3 CSVs
- [ ] Add in-memory cache (Redis or similar)
- [ ] Build a simple dashboard (React or Vue)
<!-- - [ ] Deploy to cloud (Render, Railway, or GCP)
- [ ] Publish OpenAPI docs
- [ ] Open-source release with setup instructions for the community -->

---

## Final goal

Create a **free, open-source API** for Brazilian market data, so anyone can analyze **B3 stocks and FIIs** without relying on expensive or limited APIs.  

The idea is to make it **simple, transparent, and reproducible**: if you have the official CVM/B3 files, the project works out of the box.

---

---

## How to run locally

> This project uses [Poetry](https://python-poetry.org/) for dependency management and virtual environments.

### Clone the repository

```bash
git clone https://github.com/joaomoraski/b3-data-fetcher.git
cd b3-data-fetcher
```

### Install dependencies
```bash
poetry install
```

### Configure environment variables
Create a .env file in the root directory:
```bash
CACHE_TTL_MINUTES=30
```

### Run script
Using Poetry directly:
```bash
poetry run python main.py
```
Or with Makefile (if available):
```bash
make run
```


## Author

**João Vitor Moraski Lunkes**  
Software Engineer | Finance & Quantum Finance Enthusiast  
> “I got tired of waiting for a good free API — so I decided to build one myself.”
