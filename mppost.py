import os
import requests
import time
from datetime import datetime

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = os.getenv("ACTOR_ID")
WEBHOOK = os.getenv("WEBHOOK")
FACEBOOK_URL = os.getenv("FACEBOOK_URL")
LAST_POST_FILE = os.getenv("LAST_POST_FILE", "last_post.txt")

# utolsó poszt betöltése
if os.path.exists(LAST_POST_FILE):
    with open(LAST_POST_FILE, "r") as f:
        last_post = f.read().strip()
else:
    last_post = None

def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")

def save_last_post(post):
    with open(LAST_POST_FILE, "w") as f:
        f.write(post)

def start_actor():
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {"startUrls": [{"url": FACEBOOK_URL}], "resultsLimit": 1}
    r = requests.post(url, json=payload)
    log(f"API státusz: {r.status_code}")
    if r.status_code != 201:
        log(f"Hiba az Actor indításánál: {r.text}")
        return None
    return r.json()["data"]["id"]

def wait_for_finish(run_id):
    import time
    while True:
        url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        r = requests.get(url)
        status = r.json()["data"]["status"]
        log(f"Run státusz: {status}")
        if status == "SUCCEEDED":
            return r.json()["data"]["defaultDatasetId"]
        elif status in ("FAILED", "ABORTED"):
            log("Futás nem sikerült vagy megszakadt.")
            return None
        time.sleep(5)

def get_latest_post(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?limit=1&token={APIFY_TOKEN}"
    r = requests.get(url)
    data = r.json()
    if data and len(data) > 0 and "url" in data[0]:
        return data[0]["url"]
    return None

# FUTÁS
log("🔎 Scraper indítása...")
run_id = start_actor()
if run_id:
    dataset_id = wait_for_finish(run_id)
    if dataset_id:
        post = get_latest_post(dataset_id)
        log(f"Legfrissebb poszt: {post}")
        log(f"Utolsó mentett poszt: {last_post}")
        if post and post != last_post:
            log("✅ Új poszt! Küldés Discordra...")
            try:
                requests.post(WEBHOOK, json={"content": f"🚨 Új Magyar Péter poszt 🚨\n{post}"})
                last_post = post
                save_last_post(post)
                log("📨 Üzenet elküldve és poszt elmentve.")
            except Exception as e:
                log(f"Discord küldési hiba: {e}")
        else:

            log("😢 Nincs új poszt")

