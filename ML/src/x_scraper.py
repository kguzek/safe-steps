import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime
import os

class TweetAnalyzer:
    
    CRIME_KEYWORDS = [
        'crime', 'criminal', 'theft', 'robbery', 'murder', 'assault', 'arrest',
        'police', 'investigation', 'suspect', 'victim', 'shooting', 'violence',
        'attack', 'burglary', 'vandalism', 'fraud', 'kidnapping', 'homicide',
        'stolen', 'gun', 'weapon', 'charged', 'convicted', 'sentenced',
        'przestępstwo', 'kradzież', 'napad', 'morderstwo', 'areszt', 'policja'
    ]
    
    PROTEST_KEYWORDS = [
        'protest', 'demonstration', 'rally', 'march', 'protest march',
        'demonstrators', 'protesters', 'riot', 'uprising', 'strike',
        'boycott', 'civil disobedience', 'activism', 'activist',
        'demonstracja', 'protest', 'manifestacja', 'strajk', 'wiec'
    ]
    
    LONDON_KEYWORDS = [
        'london', 'londyn', 'westminster', 'tower bridge', 'piccadilly',
        'camden', 'shoreditch', 'brixton', 'soho', 'covent garden',
        'kensington', 'chelsea', 'hackney', 'islington', 'greenwich',
        'canary wharf', 'city of london', 'big ben', 'trafalgar square'
    ]
    
    @staticmethod
    def contains_keywords(text, keywords):
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    @classmethod
    def is_crime_related(cls, tweet_text):
        return cls.contains_keywords(tweet_text, cls.CRIME_KEYWORDS)
    
    @classmethod
    def is_protest_related(cls, tweet_text):
        return cls.contains_keywords(tweet_text, cls.PROTEST_KEYWORDS)
    
    @classmethod
    def is_london_related(cls, tweet_text):
        return cls.contains_keywords(tweet_text, cls.LONDON_KEYWORDS)


def load_existing_tweets(output_file):
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_tweets(tweets, output_file):
    """Save tweets to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)


def scrape_user_tweets(driver, username, existing_urls, max_tweets=100):
    filtered_tweets = []
    username_has_london = 'london' in username.lower()
    
    try:
        url = f"https://twitter.com/{username}"
        print(f"  Navigating to {url}...")
        driver.get(url)
        
        time.sleep(5)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        tweets_collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        seen_tweet_texts = set()

        while tweets_collected < max_tweets and scroll_attempts < max_scroll_attempts:
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            
            for tweet_element in tweet_elements:
                if tweets_collected >= max_tweets:
                    break
                
                try:
                    tweet_text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    tweet_text = tweet_text_element.text
                    
                    if tweet_text in seen_tweet_texts:
                        continue
                    
                    seen_tweet_texts.add(tweet_text)
                    
                    try:
                        time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                        tweet_link_element = time_element.find_element(By.XPATH, '..')
                        tweet_url = tweet_link_element.get_attribute('href')
                    except:
                        tweet_url = f"https://twitter.com/{username}"
                    
                    # Skip if we already have this tweet
                    if tweet_url in existing_urls:
                        continue
                    
                    try:
                        time_element = tweet_element.find_element(By.CSS_SELECTOR, 'time')
                        tweet_datetime = time_element.get_attribute('datetime')
                        pub_date = datetime.fromisoformat(tweet_datetime.replace('Z', '+00:00'))
                    except:
                        pub_date = datetime.now()
                    
                    is_crime = TweetAnalyzer.is_crime_related(tweet_text)
                    is_demo = TweetAnalyzer.is_protest_related(tweet_text)
                    is_london = TweetAnalyzer.is_london_related(tweet_text)
                    
                    london_check = username_has_london or is_london
                    
                    if (is_crime or is_demo) and london_check:
                        title = tweet_text.split('\n')[0][:100] if tweet_text else "No title"
                        
                        lines = tweet_text.split('\n')
                        if len(lines) > 1:
                            description = '\n'.join(lines[1:])[:300]
                        else:
                            description = tweet_text[:300]
                        
                        tweet_data = {
                            "url": tweet_url,
                            "title": title,
                            "context": description if description else title,
                            "demonstration": is_demo,
                            "crime": is_crime,
                            "data": pub_date.isoformat(),
                            "source_account": username
                        }
                        
                        filtered_tweets.append(tweet_data)
                        print(f"    ✓ NEW tweet #{len(filtered_tweets)}: {title[:40]}...")
                    
                    tweets_collected += 1
                    
                except NoSuchElementException:
                    continue
                except Exception as e:
                    continue
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height
        
        print(f"  Completed: {tweets_collected} tweets checked, {len(filtered_tweets)} new relevant found\n")
        
    except Exception as e:
        print(f"  Error scraping @{username}: {str(e)}\n")
    
    return filtered_tweets


def scrape_cycle(usernames, output_file, max_tweets_per_user, driver):
    print(f"Starting scrape cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    existing_tweets = load_existing_tweets(output_file)
    existing_urls = set(tweet['url'] for tweet in existing_tweets)
    
    new_tweets = []
    
    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] Processing @{username}...")
        user_tweets = scrape_user_tweets(driver, username, existing_urls, max_tweets_per_user)
        new_tweets.extend(user_tweets)
        
        if i < len(usernames):
            time.sleep(3)
    
    if new_tweets:
        existing_tweets.extend(new_tweets)
        save_tweets(existing_tweets, output_file)
        
        print(f"\n{'='*60}")
        print(f"✓ Added {len(new_tweets)} new tweets!")
        print(f"✓ Total tweets in database: {len(existing_tweets)}")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"ℹ️  No new tweets found this cycle")
        print(f"{'='*60}")
    
    return len(new_tweets)


def run_continuous_scraper(usernames, output_file='all_accounts_filtered_tweets.json', 
                          max_tweets_per_user=100, interval_minutes=15, headless=True):
    usernames = [u.lstrip('@') for u in usernames]
    
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    cycle_count = 0
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        
        while True:
            cycle_count += 1
            
            try:
                new_count = scrape_cycle(usernames, output_file, max_tweets_per_user, driver)
                
                next_run = datetime.now().timestamp() + (interval_minutes * 60)
                next_run_time = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
                
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\nError in cycle {cycle_count}: {str(e)}")
                time.sleep(300)
    
    except KeyboardInterrupt:
        print(f"Completed {cycle_count} cycles")
        print(f"Data saved in: {output_file}")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Lista kont do przeszukania
    usernames = [
        "BBCLondonNews",
        "TimeOutLondon",
        "CTVLondon",
        "EveningStandard",
        "LondonNews24",
        "metpoliceuk",
    ]
    
    output_file = "all_accounts_filtered_tweets.json"
    
    # Run continuous scraper
    run_continuous_scraper(
        usernames=usernames,
        output_file=output_file,
        max_tweets_per_user=80,
        interval_minutes=15,
        headless=True
    )