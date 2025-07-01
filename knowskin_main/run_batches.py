import os
import time
import logging
import subprocess

# === CONFIGURATION ===
TOTAL_PRODUCTS = 80000
BATCH_SIZE = 5
DELAY_BETWEEN_JOBS = 10  # seconds between runs to avoid rate limiting
MAX_RETRIES = 3
LOG_FILE = "local_scheduler.log"

# === SETUP LOGGING ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === MAIN LOOP ===
def run():
    for skip in range(0, TOTAL_PRODUCTS, BATCH_SIZE):
        success = False

        for attempt in range(1, MAX_RETRIES + 1):
            logging.info(f"Starting batch with skip={skip} (Attempt {attempt})")
            print(f"Running batch with skip={skip} (Attempt {attempt})")

            try:
                result = subprocess.run(
                    ["scrapy", "crawl", "thinkdirtyspider", "-a", f"skip={skip}"],
                    check=True
                )
                logging.info(f"Batch skip={skip} completed successfully.")
                success = True
                break
            except subprocess.CalledProcessError as e:
                logging.warning(f"Error on skip={skip}, attempt {attempt}: {e}")
                time.sleep(5)  # wait a bit before retry

        if not success:
            logging.error(f"Batch skip={skip} failed after {MAX_RETRIES} attempts.")
        else:
            time.sleep(DELAY_BETWEEN_JOBS)

    logging.info("All batches processed.")

if __name__ == "__main__":
    run()
