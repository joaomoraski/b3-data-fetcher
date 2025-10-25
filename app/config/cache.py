import datetime
import json
import os

from dotenv import load_dotenv

load_dotenv()
CACHE_FILE = "cache.mouras"
CACHE_TTL = int(os.getenv("CACHE_TTL_MINUTES", "30"))  # tempo em minutos


# check if is valid
def valid_cache():
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
        timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        return (datetime.datetime.now() - timestamp) < datetime.timedelta(
            minutes=CACHE_TTL
        )
    except Exception:
        return False


def save_cache(stock_data):
    data = {"timestamp": datetime.datetime.now().isoformat(), "stock_data": stock_data}
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def load_cache():
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
        return data["stock_data"]
