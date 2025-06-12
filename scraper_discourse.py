import requests
import json
from datetime import datetime, timezone
from tqdm import tqdm
import os

# Constants
BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34  # TDS category ID
START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 4, 14, tzinfo=timezone.utc)


#  AUTHENTICATED HEADERS using your shared values
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://discourse.onlinedegree.iitm.ac.in",
    "Cookie": "_forum_session=MVzfTA8kSbnDl%2B%2FVMVKx5EzmNzawusg%2Fny5lah1a3mrm%2FUxD1d13Z%2F9KzmK5GDENV7ye5I5uIk0dJ%2BXWBN4FM%2FOboGsCM%2FJsXvqpBUKEJWIDnOX8lwiBIeRI9gLOUjohGqqPnbkwivnq%2F4fzcvmyoFiC8eBIsMRUN8UsHiGSnZ5JGj0QJgxL7MfFpsQscx7AI4%2FjFQ8Zc5OSDUnipVWkzNgbdOIAtr4yIoYAVdIJttNZaSiQH6fVVcbobyzAAdE%2FXlsNR%2Fs4B9x1JFUShIp2KT5Wye9wDQ%3D%3D--Sh4XHUoygGTLggJ2--9YU4uCPocnyjd1tlEXWxjA%3D%3D; _t=66kwZMLewds3DbP7uDSnbnJos45NaXkFGbYF8c7pHCz8jCxekhpKCDSIZITV1F9MPevb%2BTaPkZkHb6M5oMzM1JXXHvpO6b8HBnVqbiSNveIv2HEc7JuWLDL28PawtAosWGIlP6%2FV%2FnSgaD1LNZ0DbBVEdKTFUu8XLYQbKNGAnGKmzv0MA4Ido1mur8%2FW2QCDVLpbJOZSOTFk8%2BANzTyPWD2yOuKezF4NoBwACGxPj8oKo9SxPoRPRPRtx%2FYIrWmQo4%2F6qHuM%2FCHL0IMxgITx4fLf0Nc7%2BdOE4BDm1%2FFz8tAEbZ2D8mtyBtAXAcgNYJfk--eRi7ldvBpsX%2FKmZ8--hfiWBPJ3f4vMq9GdhP2Qmw%3D%3D"
}

# Get topics from the category
def fetch_topics():
    url = f"{BASE_URL}/c/courses/tds-kb/{CATEGORY_ID}.json"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()["topic_list"]["topics"]

# Get posts from a topic
def fetch_posts(topic_id):
    url = f"{BASE_URL}/t/{topic_id}.json"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()["post_stream"]["posts"]

# Check if post date is in range
def is_within_range(date_str):
    post_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return START_DATE <= post_date <= END_DATE

# Scrape everything
def scrape():
    all_posts = []
    topics = fetch_topics()

    print(f"Found {len(topics)} topics")

    for topic in tqdm(topics, desc="Scraping topics"):
        topic_id = topic["id"]
        try:
            posts = fetch_posts(topic_id)
        except Exception as e:
            print(f"Skipping topic {topic_id}: {e}")
            continue

        for post in posts:
            if is_within_range(post["created_at"]):
                all_posts.append({
                    "topic_id": topic_id,
                    "post_id": post["id"],
                    "author": post["username"],
                    "created_at": post["created_at"],
                    "content": post["cooked"]
                })

    return all_posts

if __name__ == "__main__":
    data = scrape()

    os.makedirs("data", exist_ok=True)
    with open("data/discourse.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"{len(data)} posts saved to data/discourse.json")
