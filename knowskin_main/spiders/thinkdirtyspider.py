import os
import scrapy
import pymongo
import json
import random
from dotenv import load_dotenv

load_dotenv()

class ThinkdirtyspiderSpider(scrapy.Spider):
    name = "thinkdirtyspider"
    allowed_domains = ["app.thinkdirtyapp.com"]

    # Expanded rotating headers
    USER_AGENTS = [
        "okhttp/5.0.0-alpha.2",
        "okhttp/4.9.3",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36",
        "Dalvik/2.1.0 (Linux; U; Android 10; SM-G975F Build/QP1A.190711.020)",
    ]
    X_DEVICE_UUIDS = [
        "dBEFxpVWQgykqOwx3PhEiz",
        "a1b2c3d4e5f6g7h8i9j0k",
        "ZxCvBnMqWeRtYuIoPlKjH",
        "uuid-1234567890abcdef",
        "uuid-abcdef1234567890",
    ]
    X_AUTH_TOKENS = [
        "mzHe5b16qKxRX_xoLEAi",
        "jH9vgJXtyMzfK5QVLx5N"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mongo_uri = os.getenv("MONGO_URI")
        self.logger.info(f"Connecting to MongoDB at {mongo_uri}")
        local_mongo_uri = os.getenv("LOCAL_MONGO_URI")
        self.logger.info(f"Connecting to Local MongoDB at {local_mongo_uri}")
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client["knowskin"]
        self.source_collection = self.db["products"]

        self.local_client = pymongo.MongoClient(local_mongo_uri)
        self.local_db = self.local_client["Knowskin_demo"]
        self.ingredient_collection = self.local_db["ingredients"]

        self.batch_size = 5  # Adjust per needs
        self.skip = int(kwargs.get("skip", 0))

    def start_requests(self):
        """
        Only fetch products that are not fetched or failed previously.
        """
        products = self.source_collection.find(
            {"$or": [{"status": {"$exists": False}}, {"status": "pending"}, {"status": "failed"}]},
            {"_id": 0, "id": 1, "name": 1}
        ).skip(self.skip).limit(self.batch_size)

        #proxy = os.getenv("SCRAPY_PROXY")

        count = 0
        for product in products:
            product_id = int(product["id"])
            product_name = product.get("name", "Unknown Product")
            # Randomly choose v1 or v2 endpoint
            if random.choice([True, False]):
                url = f"https://app.thinkdirtyapp.com/api/v1/products/{product_id}"
                callback = self.parse_v1
            else:
                url = f"https://app.thinkdirtyapp.com/api/v2/products/{product_id}"
                callback = self.parse_v2

            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept-Encoding": "gzip",
                "x_device_uuid": random.choice(self.X_DEVICE_UUIDS),
                "x_device_platform": "android",
                "x_auth_token": random.choice(self.X_AUTH_TOKENS),
                "x_device_app_version": "422",
                "Connection": "Keep-Alive",
            }

            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "pending"}})

            yield scrapy.Request(
                url,
                headers=headers,
                callback=callback,
                errback=self.handle_error,
                meta={
                    'product_id': product_id,
                    'product_name': product_name,
                    #'proxy': proxy,
                    'download_timeout': 10
                },
                dont_filter=True
            )
            count += 1
            self.logger.info(f"Processing product {count}: {product_id} - {product_name}")

        if count == 0:
            self.logger.info("No products found for processing.")

    def parse_v1(self, response):
        product_id = response.meta['product_id']
        product_name = response.meta['product_name']
        try:
            data = json.loads(response.text)
            product = data.get("product", {})
            upcs = product.get("upcs", [])
            all_upc_ingredients = []
            for upc in upcs:
                upc_ingredients = upc.get("upc_ingredients", [])
                all_upc_ingredients.extend(upc_ingredients)

            self.logger.info(f"Parsing response for product_id={product_id}, status={response.status}")
            self.logger.debug(f"Response body: {response.text[:500]}")

            doc = {
                "product_id": product_id,
                "product_name": product_name,
                "ingredients": all_upc_ingredients
            }

            self.ingredient_collection.update_one(
                {"product_id": product_id},
                {"$set": doc},
                upsert=True
            )
            if len(all_upc_ingredients) == 0:
                self.logger.warning(f"⚠️ No ingredients found for product {product_id}.")
                self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})
            else:
                self.source_collection.update_one({"id": product_id}, {"$set": {"status": "success"}})
                self.logger.info(f"✅ {product_id}: {len(all_upc_ingredients)} upc_ingredients saved. Response status = {response.status}")
        except Exception as e:
            self.logger.error(f"❌ Error parsing product {product_id}: {e}")
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})

    def parse_v2(self, response):
        product_id = response.meta['product_id']
        product_name = response.meta['product_name']
        try:
            data = json.loads(response.text)
            product = data.get("product", {})
            ingredients = product.get("ingredients", [])

            self.logger.info(f"Parsing response for product_id={product_id}, status={response.status}")
            self.logger.debug(f"Response body: {response.text[:500]}")

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
            if len(ingredients) == 0:
                self.logger.warning(f"⚠️ No ingredients found for product {product_id}.")
                self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})
            else:
                self.source_collection.update_one({"id": product_id}, {"$set": {"status": "success"}})
                self.logger.info(f"✅ {product_id}: {len(ingredients)} ingredients saved. Response status = {response.status}")
        except Exception as e:
            self.logger.error(f"❌ Error parsing product {product_id}: {e}")
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})

    def handle_error(self, failure):
        product_id = failure.request.meta.get('product_id', 'unknown')
        self.logger.error(f"❌ Request failed for {product_id}: {failure.request.url}")
        self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})