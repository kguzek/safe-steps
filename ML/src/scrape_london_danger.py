import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from dateutil import parser as dateparser


# CONFIGURATION
NEWSAPI_KEY = ""  # ← PUT YOUR NEWSAPI KEY HERE

KEYWORDS_CRIME = [
    "crime", "attack", "shooting", "theft", "assault",
    "violence", "murder", "robbery", "vandalism", "burglary",
    "arrest", "homicide", "stabbing", "knife", "mugging",
    "beaten", "injured", "killed", "died", "dead", "victim",
    "scam", "fraud", "hijacked"
]

LONDON_AREAS = [
    # Central London
    "Westminster", "Soho", "Covent Garden", "Leicester Square", "Piccadilly",
    "Oxford Street", "Bond Street", "Mayfair", "Bloomsbury", "Fitzrovia",
    "King's Cross", "St Pancras", "Euston", "Marylebone", "Paddington",
    "Holborn", "Clerkenwell", "Farringdon", "City of London", "Shoreditch",
    
    # North London
    "Camden", "Islington", "Holloway", "Finsbury Park", "Highgate", "Hampstead",
    "Kentish Town", "Chalk Farm", "Belsize Park", "Swiss Cottage", "Kilburn",
    "Wembley", "Harrow", "Barnet", "Enfield", "Wood Green", "Tottenham",
    "Hornsey", "Crouch End", "Muswell Hill", "Finchley", "Hendon",
    
    # East London
    "Hackney", "Dalston", "Bethnal Green", "Whitechapel", "Tower Hamlets",
    "Stratford", "Newham", "East Ham", "Barking", "Ilford", "Romford",
    "Canary Wharf", "Isle of Dogs", "Poplar", "Bow", "Mile End", "Stepney",
    "Hackney Wick", "Leyton", "Leytonstone", "Walthamstow", "Wanstead",
    
    # South London
    "Brixton", "Clapham", "Streatham", "Tooting", "Wandsworth", "Battersea",
    "Peckham", "Camberwell", "Dulwich", "Greenwich", "Lewisham", "Deptford",
    "Croydon", "Bromley", "Sutton", "Kingston", "Woolwich", "Eltham",
    "Catford", "Forest Hill", "New Cross", "Balham", "Clapham Junction",
    
    # West London
    "Kensington", "Chelsea", "Notting Hill", "Hammersmith", "Fulham",
    "Shepherd's Bush", "White City", "Ealing", "Acton", "Chiswick",
    "Brentford", "Hounslow", "Richmond", "Twickenham", "Wimbledon",
    "Putney", "Barnes", "Kew", "Holland Park", "Earl's Court",
    
    # Other areas
    "Southwark", "Lambeth", "Vauxhall", "Elephant and Castle", "London Bridge",
    "Bank", "Monument", "Liverpool Street", "Waterloo", "Victoria",
    "Pimlico", "Knightsbridge", "South Kensington", "Sloane Square"
]

OUTPUT_FILE = "london_crime_news.json"
STATE_FILE = "latest_article_state.json"
CHECK_INTERVAL = 15 * 60  # 15 minutes

# FUNCTIONS
def fetch_newsapi(query, from_date=None):
    """Fetch news from NewsAPI.org"""
    if not NEWSAPI_KEY or NEWSAPI_KEY == "":
        print("ERROR: Please set your NewsAPI key in the script!")
        print("Get your free key at: https://newsapi.org/register")
        return []
    
    url = "https://newsapi.org/v2/everything"
    
    if not from_date:
        from_date = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')
    
    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'from': from_date,
        'apiKey': NEWSAPI_KEY,
        'pageSize': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 401:
            print("ERROR: Invalid API key!")
            return []
        elif response.status_code == 429:
            print("ERROR: Rate limit exceeded!")
            return []
        
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'ok':
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return []
        
        articles = data.get('articles', [])
        print(f"Fetched {len(articles)} articles from NewsAPI")
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def fetch_full_article_content(url):
    """Scrape full article content from the URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        time.sleep(2)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()
        
        content = ""
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        if not content or len(content) < 200:
            main = soup.find('main')
            if main:
                paragraphs = main.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        if not content or len(content) < 200:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        content = ' '.join(content.split())
        return content if len(content) > 100 else ""
        
    except Exception as e:
        print(f"Could not scrape article: {e}")
        return ""

def is_crime_related(title, description, content):
    """Check if article is about a crime."""
    text = f"{title} {description} {content}".lower()
    return any(word in text for word in KEYWORDS_CRIME)

def process_articles(articles):
    """Process and filter crime articles."""
    crime_data = []
    
    for i, article in enumerate(articles, 1):
        found_locations = []
        try:
            title = article.get('title', 'No title')
            description = article.get('description', '')
            api_content = article.get('content', '')
            url = article.get('url', '')
            pub_date = article.get('publishedAt', datetime.now().isoformat())
            source = article.get('source', {}).get('name', 'Unknown')
            
            if not url:
                continue
            
            print(f"\n[{i}/{len(articles)}] {title[:70]}...")
            print(f"  Source: {source}")
            
            try:
                pub_date_obj = dateparser.parse(pub_date)
                formatted_date = pub_date_obj.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            except Exception:
                formatted_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
            
            # Crime relevance check
            if not is_crime_related(title, description or '', api_content or ''):
                print("  ⏭ Skipped: Not crime-related")
                continue
            
            # London or specific area check
            full_text = f"{title} {description} {api_content}".lower()
            found_locations = [area for area in LONDON_AREAS if area.lower() in full_text]
            if "london" not in full_text and not found_locations:
                print("  ⏭ Skipped: Not London-related (no London area mentioned)")
                continue
            
            print(f"Fetching full article content...")
            full_content = fetch_full_article_content(url)
            
            if full_content:
                context = full_content
                print(f"  ✓ Got full article: {len(full_content)} characters")
            else:
                context_parts = []
                if description:
                    context_parts.append(description)
                if api_content:
                    clean_content = api_content.split('[+')[0].strip() if '[+' in api_content else api_content
                    context_parts.append(clean_content)
                context = ' '.join(context_parts).strip() or title
                print(f"Using API content: {len(context)} characters")
            
            # Find all London areas mentioned
            content_lower = context.lower()
            matched_locations = sorted({area for area in LONDON_AREAS if area.lower() in content_lower})
            
            crime_item = {
                "url": url,
                "title": title,
                "context": context,
                "demonstration": False,
                "crime": True,
                "data": formatted_date,
                "source_account": source,
                "locations": matched_locations if matched_locations else (found_locations if found_locations else [])
            }
            
            crime_data.append(crime_item)
            print(f"Crime article added")
            
        except Exception as e:
            print(f"Error processing article: {e}")
            continue
    
    return crime_data

def load_last_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_date = dateparser.parse(data.get("last_date"))
            print(f"Last check: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
            return last_date
    except FileNotFoundError:
        print("No previous state found, starting fresh")
        return None
    except Exception as e:
        print(f"Error loading state: {e}")
        return None

def save_last_state(last_date):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_date": last_date.isoformat()}, f, indent=2)
        print(f"Updated state: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error saving state: {e}")

def save_to_json(data):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []
        print("Creating new output file")

    existing_urls = {item["url"] for item in existing}
    new_data = [item for item in data if item["url"] not in existing_urls]

    if not new_data:
        print("No new crime incidents to save")
        return None

    existing.extend(new_data)
    existing.sort(key=lambda x: dateparser.parse(x["data"]), reverse=True)
    
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(new_data)} new crime incidents to {OUTPUT_FILE}")
        print(f"Total incidents in database: {len(existing)}")
        
        latest_date = max(dateparser.parse(a["data"]) for a in new_data)
        return latest_date
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return None

def main():
    print("=" * 70)
    print("🚨 LONDON CRIME NEWS MONITOR (NewsAPI.org)")
    print("=" * 70)
    print(f"⏰ Check interval: {CHECK_INTERVAL / 60:.0f} minutes")
    print(f"💾 Output file: {OUTPUT_FILE}")
    print(f"📁 State file: {STATE_FILE}")
    print(f"🔑 API: NewsAPI.org (Free: 100 requests/day)")
    print("=" * 70)
    
    last_saved_date = load_last_state()
    iteration = 0

    while True:
        iteration += 1
        print(f"\n{'=' * 70}")
        print(f"🔄 CHECK #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        try:
            if last_saved_date:
                from_date = last_saved_date.strftime('%Y-%m-%d')
            else:
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            print(f"🔍 Searching from: {from_date}")
            query = "London AND (crime OR stabbing OR shooting OR attack OR murder OR robbery OR scam)"
            articles = fetch_newsapi(query, from_date)
            
            if not articles:
                print("No articles fetched")
            else:
                crime_data = process_articles(articles)
                
                if last_saved_date and crime_data:
                    original_count = len(crime_data)
                    crime_data = [
                        a for a in crime_data
                        if dateparser.parse(a["data"]) > last_saved_date
                    ]
                    filtered_count = original_count - len(crime_data)
                    if filtered_count > 0:
                        print(f"\n🗓 Filtered out {filtered_count} old incidents")
                
                if crime_data:
                    latest_date = save_to_json(crime_data)
                    if latest_date:
                        save_last_state(latest_date)
                        last_saved_date = latest_date
                else:
                    print("\n🕓 No new crime incidents since last check")

        except KeyboardInterrupt:
            print("\n\n⏹ Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

        print(f"\n Next check in {CHECK_INTERVAL / 60:.0f} minutes...")
        print(f"   (Press Ctrl+C to stop)")
        
        try:
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n Monitoring stopped by user")
            break

if __name__ == "__main__":
    main()
