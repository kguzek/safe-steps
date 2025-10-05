import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from dateutil import parser as dateparser


KEYWORDS_CRIME = ["crime", "attack", "shooting", "theft", "assault", "violence", "murder", "robbery", "vandalisme", "burglary", "arrest", "homicide"]
KEYWORDS_DEMO = ["protest", "demonstration", "manifestation", "strike", "riot", "march", "protester"]
OUTPUT_FILE = "paris_crime_news.json"
STATE_FILE = "latest_article_state.json"
CHECK_INTERVAL = 15 * 60  

def fetch_google_news():
    url = "https://news.google.com/rss/search?q=Paris+France+crime+OR+protest+OR+demonstration&hl=en&gl=FR&ceid=FR:en"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")
    return items

def analyze_article(title, description):
    text = f"{title} {description}".lower()
    is_crime = any(word in text for word in KEYWORDS_CRIME)
    is_demo = any(word in text for word in KEYWORDS_DEMO)
    return is_crime, is_demo

def parse_articles(items):
    news_data = []
    for item in items:
        title = item.title.text.strip()
        description = item.description.text.strip() if item.description else ""
        link = item.link.text.strip()
        pub_date_text = item.pubDate.text if item.pubDate else datetime.now().isoformat()
        try:
            pub_date = dateparser.parse(pub_date_text)
        except Exception:
            pub_date = datetime.now()

        if "paris" not in title.lower() and "paris" not in description.lower() and "paryż" not in title.lower():
            continue

        is_crime, is_demo = analyze_article(title, description)

        if not (is_crime or is_demo):
            continue

        news_item = {
            "url": link,
            "title": title,
            "context": f"{title} - {description}",
            "czy_demonstracja": is_demo,
            "czy_przestepstwo": is_crime,
            "data": pub_date.isoformat()
            
        }
        news_data.append(news_item)

    return news_data

def load_last_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return dateparser.parse(data.get("last_date"))
    except Exception:
        return None

def save_last_state(last_date):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_date": last_date.isoformat()}, f)

def save_to_json(data):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing_urls = {item["url"] for item in existing}
    new_data = [item for item in data if item["url"] not in existing_urls]

    if not new_data:
        print("No new articles")
        return None

    existing.extend(new_data)
    existing.sort(key=lambda x: x["data"], reverse=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f" Saved {len(new_data)} new article to {OUTPUT_FILE}")
    latest_date = max(dateparser.parse(a["data"]) for a in new_data)
    return latest_date

def main():

    last_saved_date = load_last_state()

    while True:
        try:
            items = fetch_google_news()
            news_data = parse_articles(items)

            if last_saved_date:
                # Filtruj tylko artykuły nowsze niż ostatnio zapisany
                news_data = [
                    a for a in news_data
                    if dateparser.parse(a["data"]) > last_saved_date
                ]

            if news_data:
                latest_date = save_to_json(news_data)
                if latest_date:
                    save_last_state(latest_date)
            else:
                print("No new relevant articles found")

        except Exception as e:
            print("error:", e)

        print(f" Next check at {CHECK_INTERVAL / 60:.0f} minut...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
