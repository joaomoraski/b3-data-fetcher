from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

from app.database.db import SessionLocal
from app.database.models.fii import Fii, FiiFinancialHistory

# === Config ===
BASE_DIR = Path("app/consumers/data/cvm_fii/inf_mensal")  # onde ficam as pastas por ano
CNPJ_TICKER_CSV = Path("app/consumers/data/fii_cnpj_ticker.csv")

# Nome padrão de coluna de CNPJ usado internamente
CNPJ_COL = "CNPJ_Fundo_Classe"


# === Utils ===
def normalize_cnpj(cnpj: str) -> str | None:
    if pd.isna(cnpj):
        return None
    return "".join(filter(str.isdigit, str(cnpj)))


def ensure_cnpj_col(df: pd.DataFrame, target: str = CNPJ_COL) -> pd.DataFrame:
    """
    Garante que o DataFrame tenha uma coluna padronizada com o nome `CNPJ_Fundo_Classe`,
    independente de o CSV ter vindo com `CNPJ_Fundo`, `CNPJ_Fundo_Classe` ou `CNPJ`.
    """
    candidates = ["CNPJ_Fundo_Classe", "CNPJ_Fundo", "CNPJ"]
    src = next((c for c in candidates if c in df.columns), None)
    if src is None:
        raise RuntimeError(
            f"Nenhuma coluna de CNPJ encontrada. Esperado uma de {candidates}. "
            f"Colunas encontradas: {list(df.columns)}"
        )
    df[target] = df[src].apply(normalize_cnpj)
    return df


def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def safe_date(x):
    try:
        v = pd.to_datetime(x, errors="coerce")
        if pd.isna(v):
            return None
        return v.date()
    except Exception:
        return None


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", decimal=".", encoding="latin1", low_memory=False)
    df = ensure_cnpj_col(df, target=CNPJ_COL)

    if "Data_Referencia" in df.columns:
        df["Data_Referencia"] = pd.to_datetime(df["Data_Referencia"], errors="coerce")

    if {CNPJ_COL, "Data_Referencia", "Versao"}.issubset(df.columns):
        df = df.sort_values([CNPJ_COL, "Data_Referencia", "Versao"])
        df = df.drop_duplicates(subset=[CNPJ_COL, "Data_Referencia"], keep="last")

    return df


def print_section(title: str):
    print(f"\n{'=' * 30}\n{title}\n{'=' * 30}")


# === Funções de persistência ===
def upsert_fiis(session, general_df: pd.DataFrame, ticker_df: pd.DataFrame):
    print_section("SALVANDO FIIs (CADASTRO)")
    merged = pd.merge(general_df, ticker_df, on=CNPJ_COL, how="left")
    merged["TICKER"] = merged["TICKER"].apply(
        lambda x: None
        if (
            x is None
            or (isinstance(x, float) and pd.isna(x))
            or str(x).lower() == "nan"
        )
        else x
    )

    for _, row in tqdm(merged.iterrows(), total=len(merged), desc="FIIs", ncols=100):
        values = {
            "cnpj": row.get(CNPJ_COL),
            "ticker": row.get("TICKER"),
            "name": row.get("Nome_Fundo_Classe"),
            "segment": row.get("Segmento_Atuacao"),
            "management_type": row.get("Tipo_Gestao"),
            "administrator": row.get("Nome_Administrador"),
            "target_audience": row.get("Publico_Alvo"),
            "start_date": safe_date(row.get("Data_Funcionamento")),
            "website": row.get("Site"),
            "isin_code": row.get("Codigo_ISIN"),
            "updated_at": datetime.now(timezone.utc),
        }

        stmt = insert(Fii).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["cnpj"], set_=values)
        session.execute(stmt)

    session.commit()
    print("✅ FIIs upsert concluído.")


def upsert_history(session, history_df: pd.DataFrame):
    print_section("SALVANDO HISTÓRICO FINANCEIRO")
    cnpj_to_id = {cnpj: _id for (cnpj, _id) in session.query(Fii.cnpj, Fii.id).all()}

    inserted = updated = skipped = 0
    for _, row in tqdm(
        history_df.iterrows(), total=len(history_df), desc="Histórico", ncols=100
    ):
        cnpj = row.get(CNPJ_COL)
        fii_id = cnpj_to_id.get(cnpj)
        if not fii_id:
            skipped += 1
            continue

        ref_date = row.get("Data_Referencia")
        if ref_date is None or (isinstance(ref_date, float) and pd.isna(ref_date)):
            skipped += 1
            continue
        if hasattr(ref_date, "date"):
            ref_date = ref_date.date()

        values = {
            "fii_id": fii_id,
            "reference_date": ref_date,
            "net_worth": safe_float(row.get("Patrimonio_Liquido")),
            "issued_shares": safe_float(row.get("Cotas_Emitidas")),
            "book_value_per_share": safe_float(row.get("Valor_Patrimonial_Cotas")),
            "monthly_dividend_yield": safe_float(
                row.get("Percentual_Dividend_Yield_Mes")
            ),
            "monthly_equity_return": safe_float(
                row.get("Percentual_Rentabilidade_Patrimonial_Mes")
            ),
            "monthly_effective_return": safe_float(
                row.get("Percentual_Rentabilidade_Efetiva_Mes")
            ),
            "amortization_per_share": safe_float(
                row.get("Percentual_Amortizacao_Cotas_Mes")
            ),
            "total_investors": safe_float(row.get("Total_Numero_Cotistas")),
            "total_liabilities": safe_float(row.get("Total_Passivo")),
            "created_at": datetime.now(timezone.utc),
        }

        stmt = insert(FiiFinancialHistory).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="_fii_date_uc",
            set_={
                k: v for k, v in values.items() if k not in ("fii_id", "reference_date")
            },
        )
        result = session.execute(stmt)
        if result.rowcount == 1:
            inserted += 1
        else:
            updated += 1

    session.commit()
    print(
        f"Histórico inserido: {inserted} | atualizado: {updated} | ignorado: {skipped}"
    )


# === Execução ===
if __name__ == "__main__":
    print_section("INICIANDO IMPORTAÇÃO GLOBAL")
    ticker_df = load_csv(CNPJ_TICKER_CSV)

    with SessionLocal() as session:
        for year_dir in sorted(BASE_DIR.iterdir()):
            if not year_dir.is_dir():
                continue

            geral = year_dir / "fii_geral.csv"
            compl = year_dir / "fii_complemento.csv"
            ativo = year_dir / "fii_ativo_passivo.csv"

            if not geral.exists() or not compl.exists() or not ativo.exists():
                print(f"⚠️ Pulando {year_dir.name} — arquivos CSV faltando.")
                continue

            print_section(f"PROCESSANDO {year_dir.name}")
            general_df = load_csv(geral)
            complemento_df = load_csv(compl)
            ativo_passivo_df = load_csv(ativo)

            # merge histórico
            history_df = pd.merge(
                complemento_df,
                ativo_passivo_df[[CNPJ_COL, "Data_Referencia", "Total_Passivo"]],
                on=[CNPJ_COL, "Data_Referencia"],
                how="left",
            )
            history_df = pd.merge(
                history_df,
                ticker_df[[CNPJ_COL, "TICKER"]],
                on=CNPJ_COL,
                how="left",
            )
            history_df = history_df.where(pd.notnull(history_df), None)

            # grava no banco
            upsert_fiis(session, general_df, ticker_df)
            upsert_history(session, history_df)

    print_section("🏁 IMPORTAÇÃO CONCLUÍDA COM SUCESSO")
