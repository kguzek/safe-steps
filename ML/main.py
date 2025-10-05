import os
import re
import json
import asyncio
import random
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, APITimeoutError
from dotenv import load_dotenv

load_dotenv()

# --------------------------- Konfiguracja ---------------------------

API_KEY = os.getenv("OPENAI_API_KEY")
assert API_KEY, "Ustaw zmienną środowiskową OPENAI_API_KEY."
client = AsyncOpenAI(api_key=API_KEY)

MODEL = os.getenv("MODEL", "gpt-5-nano")
INPUT_PATH = "data/london_crime_news.json"
OUTPUT_PATH = "outputs/london_crime_news_labeled.json"

# Ile jednoczesnych wywołań API 
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "8"))
# Maksymalna liczba ponowień na wpis
MAX_RETRIES = 5

# --------------------------- Schemat (tools) ---------------------------

TOOLS = [{
    "type": "function",
    "function": {
        "name": "set_labels",
        "description": "Nadaj etykiety dla wpisu newsowego o zdarzeniu w mieście.",
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "miejsce": {
                    "type": "string",
                    "description": "Dokładne miejsce (ulica i numer / skrzyżowanie / plac / stacja / punkt charakterystyczny + dzielnica/arr.). Jeśli brak, oszacuj najbliższe nazwane miejsce PO ANGIELSKU."
                },
                "data": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Data/godzina zdarzenia w ISO 8601 z offsetem strefy, np. 2025-10-04T13:45:00+02:00. Jeśli znana tylko data, użyj 00:00 dla czasu."
                },
                "szacowany_czas_zakonczenia": {
                    "type": "string",
                    "description": "Szacunek zakończenia na podstawie podobnych wydarzeń (najlepiej podać ISO 8601 z offsetem strefy, np. 2025-10-04T13:45:00+02:00. Jeśli znana tylko data, użyj 00:00 dla czasu.)."
                },
                "poziom_zagrozenia": {
                    "type": "integer", "minimum": 1, "maximum": 5,
                    "description": "Skala 1–5: jak bardzo niebezpiecznie w danym obszarze."
                },
                "komfort": {
                    "type": "integer", "minimum": 1, "maximum": 5,
                    "description": "Skala 1–5: wpływ na komfort przemieszczania się po mieście."
                },
                "podsumowanie": {
                    "type": "string",
                    "description": "Pare słów podsumowania po polsku."
                },
                "adres_url": {
                    "type": "string",
                    "description": "Adres URL źródła."
                }
            },
            "required": [
                "miejsce","data","szacowany_czas_zakonczenia",
                "poziom_zagrozenia","komfort","podsumowanie","adres_url"
            ]
        }
    }
}]

# --------------------------- Prompt ---------------------------

def build_user_prompt(entry: Dict[str, Any]) -> str:
    return (
        "Z danych prasowych wyekstrahuj etykiety wg schematu.\n"
        "Wymagania:\n"
        "- 'miejsce' ma być bardziej szczegółowe niż kraj/miasto. Podaj ulicę i numer lub skrzyżowanie/plac/stację/punkt charakterystyczny oraz dzielnicę/arrondissement PO ANGIELSKU. "
        "Jeśli nie ma wprost, oszacuj najbliższe nazwane miejsce.\n"
        "- 'data' wpisz w ISO 8601 (format z T i strefą), np. 2025-10-04T13:45:00+02:00. "
        "Jeśli znana tylko data bez godziny, użyj 00:00 i prawidłowy offset strefy.\n"
        "- 'szacowany_czas_zakonczenia' oszacuj na bazie podobnych wydarzeń z przeszłości.\n"
        "- 'poziom_zagrozenia' i 'komfort' to liczby całkowite 1–5.\n"
        "- 'podsumowanie' pare słów, rzeczowo po polsku.\n"
        "- Zwróć wyłącznie argumenty funkcji zgodne ze schematem.\n\n"
        f"Dane wejściowe:\n"
        f"- url: {entry.get('url','')}\n"
        f"- tytuł: {entry.get('tytul','')}\n"
        f"- treść: {entry.get('tresc','')}\n"
        f"- czy_demonstracja: {entry.get('czy_demonstracja')}\n"
        f"- czy_przestepstwo: {entry.get('czy_przestepstwo')}\n"
        f"- data_surowa: {entry.get('data','')}\n"
    )

# --------------------------- Walidacja wyników ---------------------------

ISO_DT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(?:\.\d+)?([+-]\d{2}:\d{2}|Z)$"
)

GENERIC_PLACES = {
    "francja", "france", "paryż", "paris",
    "ile-de-france", "ile de france",
    "polska", "warszawa", "warsaw"  # zabezpieczenie przed uogólnieniami
}

def is_specific_place(miejsce: str) -> bool:
    if not miejsce:
        return False
    s = miejsce.strip().lower()
    if s in GENERIC_PLACES:
        return False
    # zbyt krótko lub wyłącznie miasto/kraj
    if len(s) < 5:
        return False
    # proste heurystyki: obecność typu obiektu/ulicy/placu/numeru
    tokens = ["ul.", "ulica", "rue", "avenue", "av.", "boulevard", "bd", "place", "pl.", "square",
              "quai", "pont", "gare", "station", "stacja", "skrzyżowanie", "cross", "rond-point",
              "rue de", "rue du", "rue des", "bd ", "boul.", "allee", "allée"]
    if any(t in s for t in tokens):
        return True
    # numer porządkowy lub skrzyżowanie typu "X / Y"
    if re.search(r"\d", s) or "/" in s:
        return True
    # arrondissement/dzielnica
    if re.search(r"\b(\d{1,2})(er|e)?\s*arr", s) or "arrondissement" in s:
        return True
    return False

def clamp(v: Optional[int], lo=1, hi=5) -> Optional[int]:
    if v is None:
        return None
    try:
        iv = int(v)
        return max(lo, min(hi, iv))
    except Exception:
        return None

def post_validate(entry: Dict[str, Any], labels: Dict[str, Any]) -> Dict[str, Any]:
    # adres_url – zawsze z wejścia, jeśli brak
    if not labels.get("adres_url"):
        labels["adres_url"] = entry.get("url", "")

    # ISO 8601 – jeśli model nie trafi w pattern, zostaw jak zwrócił (logika biznesowa może potem odfiltrować)
    data_val = labels.get("data")
    if isinstance(data_val, str) and not ISO_DT_RE.match(data_val.strip()):
        labels["data_warning"] = "data nie przeszła walidacji ISO 8601"

    # miejsce – odrzuć ogólne
    if not is_specific_place(labels.get("miejsce", "")):
        labels["miejsce_warning"] = "miejsce zbyt ogólne – rozważ doprecyzowanie lub oszacowanie"

    # skale
    labels["poziom_zagrozenia"] = clamp(labels.get("poziom_zagrozenia"))
    labels["komfort"] = clamp(labels.get("komfort"))

    return labels

# --------------------------- Jedno zapytanie z retry ---------------------------

async def fetch_labels(entry: Dict[str, Any], sem: asyncio.Semaphore) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": "Zwracasz etykiety w JSON przez function-calling; przestrzegaj ISO 8601 dla pola 'data' i precyzuj lokalizację poniżej poziomu miasta."},
        {"role": "user", "content": build_user_prompt(entry)}
    ]

    delay = 1.0
    last_err: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with sem:
                comp = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice={"type": "function", "function": {"name": "set_labels"}},
                    temperature=1
                )
            msg = comp.choices[0].message
            if not getattr(msg, "tool_calls", None):
                raise RuntimeError("Brak wywołania funkcji z danymi etykiet.")
            args_str = msg.tool_calls[0].function.arguments
            labels = json.loads(args_str)
            labels = post_validate(entry, labels)
            return {"wejscie": entry, "labels": labels, "error": None}
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            last_err = e
            # wykładniczy backoff + jitter
            await asyncio.sleep(delay + random.random() * 0.3)
            delay = min(delay * 2, 16.0)
        except Exception as e:
            # błąd „merytoryczny” – nie retry’ujemy w nieskończoność, ale jeszcze 1–2 próby pomogą
            last_err = e
            await asyncio.sleep(0.5)

    # Po wyczerpaniu retry – zwróć z błędem, ale nie zatrzymuj całości
    return {"wejscie": entry, "labels": None, "error": str(last_err) if last_err else "unknown error"}

# --------------------------- Main ---------------------------

async def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items: List[Dict[str, Any]] = json.load(f)

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [asyncio.create_task(fetch_labels(entry, sem)) for entry in items]
    results = []
    done = 0
    total = len(tasks)

    for coro in asyncio.as_completed(tasks):
        res = await coro
        results.append(res)
        done += 1
        if done % 10 == 0 or done == total:
            print(f"Postęp: {done}/{total}")

    # zapisujemy w takim samym układzie jak wcześniej (wejście + labels)
    out = []
    for r in results:
        if r["labels"] is not None:
            out.append({"labels": r["labels"]})
        else:
            out.append({"labels": {"error": r["error"]}})

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"OK — zapisano: {OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
