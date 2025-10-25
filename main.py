import json
import pandas as pd
import yfinance as yf
import datetime
from cache import valid_cache, load_cache, save_cache


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
            cnpj_ticker[cnpj] = {"ticker": ticker, "preco": ticker_info.get("currentPrice")}
    save_cache(cnpj_ticker)
    print("Cache atualizado.")


general_file = "fii_geral.csv"
active_passive_file = "fii_ativo_passivo.csv"
complement_file = "fii_complemento.csv"

df = pd.read_csv(
    general_file,
    sep=';',           # separador padrão da CVM
    decimal='.',       # vírgula decimal
    encoding='latin1', # evita erro de acentuação
    low_memory=False
)

df1 = pd.read_csv(
    active_passive_file,
    sep=';',           # separador padrão da CVM
    decimal='.',       # vírgula decimal
    encoding='latin1', # evita erro de acentuação
    low_memory=False
)

df2 = pd.read_csv(
    complement_file,
    sep=';',           # separador padrão da CVM
    decimal='.',       # vírgula decimal
    encoding='latin1', # evita erro de acentuação
    low_memory=False
)

colunas_fii_geral = [
    'CNPJ_Fundo_Classe',
    'Nome_Fundo_Classe',
    'Segmento_Atuacao',
    'Codigo_ISIN', # ex: MXRF11 → ISIN
    'Data_Referencia',
    'Versao'
]

colunas_ativo_passivo = [
    'CNPJ_Fundo_Classe',
    'Data_Referencia',
    'Total_Passivo',
    'Versao'
]

# Seleciona só as colunas que você precisa
colunas_complemento = [
    'CNPJ_Fundo_Classe',
    'Data_Referencia',
    'Patrimonio_Liquido',
    'Cotas_Emitidas',
    'Valor_Patrimonial_Cotas',
    'Percentual_Dividend_Yield_Mes',
    'Percentual_Amortizacao_Cotas_Mes',
    'Percentual_Rentabilidade_Patrimonial_Mes',
    'Percentual_Rentabilidade_Efetiva_Mes',
    'Versao'
]

general_data = df[colunas_fii_geral].copy()
active_passive_data = df1[colunas_ativo_passivo].copy()
complement_data = df2[colunas_complemento].copy()


# === 3. Ordena por CNPJ + Data + Versão e mantém só o mais recente ===
complement_data["Data_Referencia"] = pd.to_datetime(complement_data["Data_Referencia"], errors="coerce")
active_passive_data["Data_Referencia"] = pd.to_datetime(active_passive_data["Data_Referencia"], errors="coerce")

complement_data = complement_data.sort_values(["CNPJ_Fundo_Classe", "Data_Referencia", "Versao"])
complement_data = complement_data.drop_duplicates(subset="CNPJ_Fundo_Classe", keep="last")

active_passive_data = active_passive_data.sort_values(["CNPJ_Fundo_Classe", "Data_Referencia", "Versao"])
active_passive_data = active_passive_data.drop_duplicates(subset="CNPJ_Fundo_Classe", keep="last")

general_data = general_data.sort_values(["CNPJ_Fundo_Classe", "Data_Referencia", "Versao"])
general_data = general_data.drop_duplicates(subset="CNPJ_Fundo_Classe", keep="last")


# === 4. Merge com as outras planilhas ===
merged = complement_data.merge(
    general_data[["CNPJ_Fundo_Classe", "Nome_Fundo_Classe", "Segmento_Atuacao", "Codigo_ISIN"]],
    on="CNPJ_Fundo_Classe", how="left"
)

merged = merged.merge(
    active_passive_data[["CNPJ_Fundo_Classe", "Data_Referencia", "Total_Passivo"]],
    on=["CNPJ_Fundo_Classe", "Data_Referencia"], how="left"
)

final = merged[[
    "CNPJ_Fundo_Classe",
    "Nome_Fundo_Classe",
    "Segmento_Atuacao",
    "Data_Referencia",
    "Patrimonio_Liquido",
    "Cotas_Emitidas",
    "Valor_Patrimonial_Cotas",
    "Percentual_Dividend_Yield_Mes",
    "Total_Passivo",
    "Codigo_ISIN"
]]

for cnpj in cnpj_ticker:
    line = final.loc[final["CNPJ_Fundo_Classe"] == cnpj].iloc[0]
    vpcota = line['Valor_Patrimonial_Cotas']
    dymes = line['Percentual_Dividend_Yield_Mes']
    divEmReal = dymes * vpcota
    pvp = cnpj_ticker[cnpj]["preco"] / vpcota

    print("============================")
    print(f"Ativo: {cnpj_ticker[cnpj]["ticker"]}")
    print(f"Valor patrimonial por cota: {vpcota}")
    print(f"DY MES: {dymes}")
    print(f"Div em REal: {divEmReal}")
    print(f"p/Vp: {pvp}")
    print(f"Preço: {cnpj_ticker[cnpj]["preco"]}")

