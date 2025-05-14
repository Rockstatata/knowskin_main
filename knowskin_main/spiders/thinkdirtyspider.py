import scrapy
import pymongo
import json

class ThinkdirtyspiderSpider(scrapy.Spider):
    name = "thinkdirtyspider"
    allowed_domains = ["app.thinkdirtyapp.com"]
    start_urls = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = pymongo.MongoClient("mongodb+srv://algoadmin:0IHi82N9Hoi84yQp@knowskin-cluster.ogv7tvs.mongodb.net/?retryWrites=true&w=majority&appName=knowskin-cluster")
        self.db = self.client["knowskin"]
        self.source_collection = self.db["products"]
        self.ingredient_collection = self.db["product_ingredients"]

    def start_requests(self):
        # Only fetch products that are not fetched or failed previously
        products = self.source_collection.find(
            {"$or": [{"status": {"$exists": False}}, {"status": "pending"}, {"status": "failed"}]},
            {"_id": 0, "id": 1, "name": 1}
        ).limit(1000)
        proxy = "http://scrapeops:64cc759c-ab65-4161-acdf-92e9632075bb@residential-proxy.scrapeops.io:8181"
        for product in products:
            product_id = product["id"]
            product_name = product.get("name", "Unknown Product")
            url = f"https://app.thinkdirtyapp.com/api/v2/products/{product_id}"
            headers = {
                "User-Agent": "okhttp/5.0.0-alpha.2",
                "Accept-Encoding": "gzip",
                "x_device_uuid": "dBEFxpVWQgykqOwx3PhEiz",
                "x_device_platform": "android",
                "x_auth_token": "mzHe5b16qKxRX_xoLEAi",
                "x_device_app_version": "422"
            }
            # Mark as pending before request
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "pending"}})
            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse,
                errback=self.handle_error,
                meta={'product_id': product_id, 'product_name': product_name, "proxy": proxy, "download_timeout": 10}
            )

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
            # Insert or update ingredient data
            self.ingredient_collection.update_one(
                {"product_id": product_id},
                {"$set": doc},
                upsert=True
            )
            # Mark as success
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "success"}})
            self.logger.info(f"Inserted {len(ingredients)} ingredients for product {product_id}.")
        except Exception as e:
            self.logger.error(f"Error parsing product {product_id}: {e}")
            self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})

    def handle_error(self, failure):
        product_id = failure.request.meta['product_id']
        self.logger.error(f"Request failed: {failure.request.url}")
        # Mark as failed
        self.source_collection.update_one({"id": product_id}, {"$set": {"status": "failed"}})