import requests

SCRAPYD_URL = "http://localhost:6800"
PROJECT = "knowskin_main"
SPIDER = "thinkdirtyspider"

total_products = 200000
batch_size = 20

for skip in range(0, total_products, batch_size):
    data = {
        'project': PROJECT,
        'spider': SPIDER,
        'setting': 'CONCURRENT_REQUESTS=20',
        'setting': 'DOWNLOAD_DELAY=2.0',
        'skip': str(skip)
    }
    response = requests.post(f"{SCRAPYD_URL}/schedule.json", data=data)
    print(f"Scheduled batch with skip={skip}: {response.json()}")
