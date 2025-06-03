# Knowskin Ingredient Scraper

## Overview

**Knowskin Ingredient Scraper** is a scalable, production-ready web scraping system built with [Scrapy](https://scrapy.org/) and [FastAPI](https://fastapi.tiangolo.com/). It is designed to fetch ingredient data for cosmetic products from the ThinkDirty API, using product IDs sourced from a MongoDB database. The system supports robust batching, error handling, and retry logic to ensure data completeness and efficiency, and is deployable both locally and on cloud servers (e.g., AWS) using [Scrapyd](https://scrapyd.readthedocs.io/en/latest/).

---

## Features

- **Batch scraping:** Processes products in configurable batches to avoid rate limits and maximize throughput.
- **Retry logic:** Automatically retries failed or incomplete fetches in future runs, ensuring no duplicate or wasted requests.
- **Rotating headers and proxies:** Uses pools of user agents, device UUIDs, and authentication tokens to evade anti-bot measures.
- **MongoDB integration:** Reads product IDs and stores ingredient data and fetch status in MongoDB.
- **FastAPI server:** Exposes endpoints to trigger batch scraping jobs via HTTP requests.
- **Scrapyd support:** Easily deploy and schedule spiders on remote servers.
- **Environment-based configuration:** All sensitive credentials and settings are managed via environment variables.

---

## Tech Stack

- **Python 3.8+**
- [Scrapy](https://scrapy.org/) (web scraping framework)
- [FastAPI](https://fastapi.tiangolo.com/) (API server for batch control)
- [MongoDB](https://www.mongodb.com/) (data storage)
- [Pymongo](https://pymongo.readthedocs.io/en/stable/) (MongoDB client)
- [Scrapyd](https://scrapyd.readthedocs.io/en/latest/) (remote spider deployment)
- [ScrapeOps](https://scrapeops.io/) (optional, for proxy management and monitoring)
- [Requests](https://docs.python-requests.org/en/latest/) (for batch scheduling scripts)

---

## Project Structure

```
.
├── knowskin_main/
│   ├── api_server.py         # FastAPI server for batch job control
│   ├── items.py              # Scrapy item definitions (boilerplate)
│   ├── middlewares.py        # Scrapy middlewares (customize as needed)
│   ├── pipelines.py          # Scrapy pipelines (customize as needed)
│   ├── run_batches.py        # Script to run batches locally
│   ├── schedule_batches.py   # Script to schedule batches via Scrapyd
│   ├── settings.py           # Scrapy project settings
│   └── spiders/
│       └── thinkdirtyspider.py # Main spider for ThinkDirty API
├── requirements.txt
├── scrapy.cfg
├── .env                      # Environment variables (not committed)
├── scrapinghub.yml           # (Optional) Scrapinghub deployment config
├── dbs/                      # Local database files (if any)
├── crawls/                   # Scrapy crawl state and queues
├── build/, eggs/, project.egg-info/ # Build artifacts
```

---

## How It Works

### 1. **Data Flow**

- Product IDs are stored in a MongoDB collection (`products`).
- The spider fetches only those products whose status is `pending`, `failed`, or not set.
- For each product, the spider randomly selects an API version (v1 or v2) and rotates headers and tokens to mimic real device traffic.
- Ingredient data is parsed and stored in another MongoDB collection (`ingredients`).
- Fetch status (`success` or `failed`) is updated in the source collection to avoid duplicate work.
- Failed products are retried in future runs.

### 2. **Batch Processing**

- Batching is controlled via the `batch_size` and `skip` parameters.
- Batches can be triggered via the FastAPI server or via Scrapyd scheduling scripts.
- Each batch only processes a subset of products, making the system scalable and restartable.

### 3. **FastAPI Server**

- Exposes a `/run_batches/` endpoint to trigger batch jobs asynchronously.
- Handles retries and logs progress to a file.

### 4. **Scrapyd Deployment**

- The project can be deployed to a Scrapyd server for remote scheduling and monitoring.
- `scrapyd-deploy` and `scrapy.cfg` are used for deployment configuration.

---

## Setup & Installation

### 1. **Clone the Repository**

```sh
git clone <your-repo-url>
cd knowskin_main
```

### 2. **Install Dependencies**

```sh
pip install -r requirements.txt
```

### 3. **Configure Environment Variables**

Create a `.env` file in the project root with the following (example):

```
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster-url>/<dbname>
LOCAL_MONGO_URI=mongodb://localhost:27017/
SCRAPY_PROXY=http://<proxy-user>:<proxy-pass>@<proxy-host>:<proxy-port>
```

### 4. **Prepare MongoDB**

- Ensure your `products` collection is populated with product IDs and names.

---

## Usage

### **A. Run Spider Locally**

```sh
scrapy crawl thinkdirtyspider
```

- Use `-a skip=XX` to skip a number of products (for batching).

### **B. Run Batches via FastAPI**

Start the API server:

```sh
uvicorn knowskin_main.api_server:app --reload
```

Trigger a batch job:

```sh
curl -X POST "http://localhost:8000/run_batches/" -H "accept: application/json" -d ""
```

### **C. Deploy & Schedule on Scrapyd**

- Deploy with:  
  `scrapyd-deploy <target> -p knowskin_main`
- Schedule jobs using Scrapyd's API or `schedule_batches.py`.

---

## Configuration

- **Batch size, delays, and concurrency** are controlled in `settings.py` and via API/script parameters.
- **Header and token pools** can be expanded in `thinkdirtyspider.py` for better anti-bot evasion.
- **Logging** is written to both console and log files for debugging and monitoring.

---

## Best Practices & Recommendations

- **Expand your pools** of user agents, device UUIDs, and tokens for production use.
- **Monitor MongoDB** for failed products and investigate persistent failures.
- **Keep your credentials** and sensitive data in `.env` or environment variables.
- **Adjust concurrency and delays** to avoid rate limits and bans.
- **Review logs** regularly for errors and blocked requests.
- **Add tests** for your FastAPI endpoints and core logic for better reliability.

---

## Troubleshooting

- **Access Denied/Rate Limited:**  
  Expand header/token pools, slow down requests, and check proxy health.
- **MongoDB Connection Issues:**  
  Verify your URIs and network/firewall settings.
- **Scrapyd Deployment Issues:**  
  Ensure your `scrapy.cfg` and `scrapinghub.yml` are correctly configured.

---

## License

This project is for educational and research purposes only. Respect the terms of service of any third-party APIs you interact with.

---

## Author

Maintained by Sarwad.  
For questions or contributions, please open an issue or pull request.
