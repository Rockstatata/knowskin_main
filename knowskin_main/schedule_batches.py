import requests
import time
import logging

# === CONFIGURATION ===
SCRAPYD_URL = "http://localhost:6800"
PROJECT = "knowskin_main"
SPIDER = "thinkdirtyspider"

TOTAL_PRODUCTS = 200000
BATCH_SIZE = 5
POLL_INTERVAL = 5  # seconds to wait before checking again
MAX_RETRIES = 3
LOG_FILE = "scheduler.log"

# === SETUP LOGGING ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === HELPER FUNCTIONS ===
def is_spider_idle():
    try:
        response = requests.get(f"{SCRAPYD_URL}/listjobs.json", params={"project": PROJECT})
        response.raise_for_status()
        jobs = response.json()
        running = jobs.get("running", [])
        pending = jobs.get("pending", [])
        return len(running) == 0 and len(pending) == 0
    except Exception as e:
        logging.error(f"Error checking job status: {e}")
        return False

def schedule_job(skip):
    for attempt in range(MAX_RETRIES):
        try:
            data = {
                'project': PROJECT,
                'spider': SPIDER,
                'skip': str(skip)
            }
            response = requests.post(f"{SCRAPYD_URL}/schedule.json", data=data)
            response.raise_for_status()
            jobid = response.json().get('jobid')
            logging.info(f"Scheduled job with skip={skip}, jobid={jobid}")
            return jobid
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed to schedule job with skip={skip}: {e}")
            time.sleep(2)
    logging.error(f"Failed to schedule job with skip={skip} after {MAX_RETRIES} attempts.")
    return None

# === MAIN SEQUENTIAL LOOP ===
def run():
    for skip in range(0, TOTAL_PRODUCTS, BATCH_SIZE):
        logging.info(f"Waiting for previous jobs to finish before scheduling skip={skip}")
        while not is_spider_idle():
            time.sleep(POLL_INTERVAL)

        job_id = schedule_job(skip)
        if not job_id:
            logging.error(f"Skipping batch {skip} due to persistent errors.")

    logging.info("All batches scheduled successfully.")

if __name__ == "__main__":
    run()
