import io
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/"
DOWNLOAD_DIR = Path("app/consumers/data/cvm_fii/inf_mensal")
RENAMINGS = {
    "fii_geral.csv": ["geral", "geral_fundo", "Fundo_Classe"],
    "fii_complemento.csv": ["complemento", "compl"],
    "fii_ativo_passivo.csv": ["ativo_passivo", "passivo"],
}


def get_zip_urls(years: list[int]) -> list[str]:
    return [f"{BASE_URL}inf_mensal_fii_{year}.zip" for year in years]


def download_and_extract(url: str, out_dir: Path):
    print(f"Download: {url}")
    r = requests.get(url)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(out_dir)
    print(f"Extraído para: {out_dir}")


def rename_files_in_dir(dir_path: Path):
    for csv_file in dir_path.glob("*.csv"):
        name = csv_file.name.lower()
        for target_name, keywords in RENAMINGS.items():
            if any(kw in name for kw in keywords):
                new_path = dir_path / target_name
                csv_file.rename(new_path)
                print(f"Renomeado: {csv_file.name} → {target_name}")
                break


def main():
    # pega o ano do argumento (ou baixa todos)
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
            years = [year]
        except ValueError:
            print("⚠️ Ano inválido, use: python download_fii_data.py 2023")
            sys.exit(1)
    else:
        current_year = datetime.now().year
        years = list(range(2016, current_year + 1))

    print(f"Anos selecionados: {years}")

    urls = get_zip_urls(years)
    for url in urls:
        year = url.split("_")[-1].replace(".zip", "")
        out_dir = DOWNLOAD_DIR / year
        download_and_extract(url, out_dir)
        rename_files_in_dir(out_dir)

    print("\n🏁 Todos os arquivos foram baixados e preparados com sucesso!")


if __name__ == "__main__":
    main()
