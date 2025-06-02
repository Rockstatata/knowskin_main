import os

total_products = 200000  # approximate total count of products
batch_size = 20       # same as in your spider

for skip in range(0, total_products, batch_size):
    print(f"Running batch with skip={skip}")
    os.system(f"scrapy crawl thinkdirtyspider -a skip={skip}")