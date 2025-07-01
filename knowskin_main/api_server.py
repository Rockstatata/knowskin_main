from fastapi import FastAPI, BackgroundTasks
import subprocess
import time
import logging

app = FastAPI()

# === CONFIG ===
MAX_RETRIES = 3
LOG_FILE = "fastapi_batch_runner.log"

# === SETUP LOGGING ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_batches_task(total_products: int, batch_size: int, delay_between_jobs: int):
    for skip in range(0, total_products, batch_size):
        success = False

        for attempt in range(1, MAX_RETRIES + 1):
            logging.info(f"Starting batch with skip={skip} (Attempt {attempt})")
            try:
                subprocess.run(
                    ["scrapy", "crawl", "thinkdirtyspider", "-a", f"skip={skip}"],
                    check=True
                )
                logging.info(f"Batch skip={skip} completed successfully.")
                success = True
                break
            except subprocess.CalledProcessError as e:
                logging.warning(f"Error on skip={skip}, attempt {attempt}: {e}")
                time.sleep(5)  # short delay before retry

        if not success:
            logging.error(f"Batch skip={skip} failed after {MAX_RETRIES} attempts.")
        else:
            time.sleep(delay_between_jobs)

    logging.info("All batches processed.")

@app.post("/run_batches/")
def run_batches(
    background_tasks: BackgroundTasks,
    total_products: int = 80000,
    batch_size: int = 5,
    delay_between_jobs: int = 10
):
    background_tasks.add_task(run_batches_task, total_products, batch_size, delay_between_jobs)
    return {"status": "Batch job started in background"}
