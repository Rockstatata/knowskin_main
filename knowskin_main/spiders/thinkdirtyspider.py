import scrapy
import pymongo
import json
import random
import logging

class ThinkdirtyspiderSpider(scrapy.Spider):
    name = "thinkdirtyspider"
    allowed_domains = ["app.thinkdirtyapp.com"]
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1.0,
        'RETRY_TIMES': 3,
        'JOBDIR': 'crawls/thinkdirty',  # Enables resume support
        'LOG_LEVEL': 'INFO',
    }

    # Rotating headers
    USER_AGENTS = [
        "okhttp/5.0.0-alpha.2",
        "okhttp/4.9.3",
    ]
    X_DEVICE_UUIDS = [
        "dBEFxpVWQgykqOwx3PhEiz",
        "a1b2c3d4e5f6g7h8i9j0k",
        "ZxCvBnMqWeRtYuIoPlKjH"
    ]
    X_AUTH_TOKENS = [
        "mzHe5b16qKxRX_xoLEAi",
         "jH9vgJXtyMzfK5QVLx5N"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = pymongo.MongoClient(
            "mongodb+srv://algoadmin:0IHi82N9Hoi84yQp@knowskin-cluster.ogv7tvs.mongodb.net/?retryWrites=true&w=majority&appName=knowskin-cluster"
        )
        self.db = self.client["knowskin"]
        self.source_collection = self.db["products"]

        self.local_client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.local_db = self.local_client["Knowskin_demo"]
        self.ingredient_collection = self.local_db["ingredients"]

        self.batch_size = 1000  # Adjust per needs
        self.skip = int(kwargs.get("skip", 0))

    def start_requests(self):
        products = self.source_collection.find(
            {"$or": [{"status": {"$exists": False}}, {"status": "pending"}, {"status": "failed"}]},
            {"_id": 0, "id": 1, "name": 1}
        ).limit(self.batch_size)

        proxy = "http://ernusbhx-rotate:xkj6r6ecaqlz@p.webshare.io:80/"

        count = 0
        for product in products:
            product_id = product["id"]
            product_name = product.get("name", "Unknown Product")
            url = f"https://app.thinkdirtyapp.com/api/v2/products/{product_id}"

            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept-Encoding": "gzip",
                "x_device_uuid": random.choice(self.X_DEVICE_UUIDS),
                "x_device_platform": "android",
                "x_auth_token": random.choice(self.X_AUTH_TOKENS),
                "x_device_app_version": "422",
                "Connection": "Keep-Alive",
                "Accept": "*/*",
                "Content-Type": "application/json; charset=utf-8",
            }

            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "pending"}})

            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    'product_id': product_id,
                    'product_name': product_name,
                    'proxy': proxy,
                    'download_timeout': 10
                }
            )
            count += 1

        if count == 0:
            self.logger.info("No products found for processing.")

    def parse(self, response):
        product_id = response.meta['product_id']
        product_name = response.meta['product_name']
        try:
            data = json.loads(response.text)
            product = data.get("product", {})
            ingredients = product.get("ingredients", [])

            doc = {
                "product_id": product_id,
                "product_name": product_name,
                "ingredients": ingredients
            }

            self.ingredient_collection.update_one(
                {"product_id": product_id},
                {"$set": doc},
                upsert=True
            )
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "success"}})
            self.logger.info(f"✅ {product_id}: {len(ingredients)} ingredients saved. Response status = {response.status}")
        except Exception as e:
            self.logger.error(f"❌ Error parsing product {product_id}: {e}")
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})

    def handle_error(self, failure):
        product_id = failure.request.meta['product_id']
        self.logger.error(f"❌ Request failed for {product_id}: {failure.request.url}")
        self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})
