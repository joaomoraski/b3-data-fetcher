import yfinance as yf

from app.config.cache import load_cache, save_cache, valid_cache


def verify_load_cache() -> dict[dict]:
    cnpj_ticker: dict[dict] = {}
    if valid_cache():
        print("Usando cache existente.")
        cnpj_ticker = load_cache()
    else:
        print("Buscando dados Yahoo finance")
        with open("ativos.txt", "r") as fd:
            for line in fd:
                ticker, cnpj = line.strip().split(",")
                ticker_yf = yf.Ticker(f"{ticker}.SA")
                ticker_info = ticker_yf.info
                cnpj_ticker[cnpj] = {
                    "ticker": ticker,
                    "preco": ticker_info.get("currentPrice"),
                }
        save_cache(cnpj_ticker)
        print("Cache atualizado.")

    return cnpj_ticker
