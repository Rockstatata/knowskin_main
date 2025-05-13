import scrapy
import pymongo
import json


class ThinkdirtyspiderSpider(scrapy.Spider):
    name = "thinkdirtyspider"
    allowed_domains = ["app.thinkdirtyapp.com"]
    start_urls = ["https://app.thinkdirtyapp.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # MongoDB setup
        self.client = pymongo.MongoClient("mongodb+srv://algoadmin:0IHi82N9Hoi84yQp@knowskin-cluster.ogv7tvs.mongodb.net/?retryWrites=true&w=majority&appName=knowskin-cluster")
        self.db = self.client["knowskin"]
        self.source_collection = self.db["products"]
        self.ingredient_collection = self.db["product_ingredients"]
        self.failed_requests = []  # List to store failed requests

    def start_requests(self):
        products = self.source_collection.find({}, {"_id": 0, "id": 1, "name": 1}).limit(10000)
        proxies = {
            "http": "http://scrapeops:64cc759c-ab65-4161-acdf-92e9632075bb@residential-proxy.scrapeops.io:8181",
            "https": "http://scrapeops:64cc759c-ab65-4161-acdf-92e9632075bb@residential-proxy.scrapeops.io:8181"
        }
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
            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse,
                errback=self.handle_error,  # Add errback
                meta={'product_id': product_id, 'product_name': product_name, 
                      "proxy": proxies["https"], "download_timeout": 10}
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

            self.ingredient_collection.insert_one(doc)
            self.logger.info(f"Inserted {len(ingredients)} ingredients for product {product_id}.")

        except Exception as e:
            self.logger.error(f"Error parsing product {product_id}: {e}")

    def handle_error(self, failure):
        # Log the error
        self.logger.error(f"Request failed: {failure.request.url}")
        
        # Extract meta data from the failed request
        product_id = failure.request.meta['product_id']
        product_name = failure.request.meta['product_name']
        
        # Save the failed request details for retrying
        self.failed_requests.append({
            'url': failure.request.url,
            'product_id': product_id,
            'product_name': product_name
        })

    def closed(self, reason):
        if self.failed_requests:
            self.logger.info(f"Retrying {len(self.failed_requests)} failed requests...")
            for request in self.failed_requests:
                yield scrapy.Request(
                    url=request['url'],
                    headers={
                        "User-Agent": "okhttp/5.0.0-alpha.2",
                        "Accept-Encoding": "gzip",
                        "x_device_uuid": "dBEFxpVWQgykqOwx3PhEiz",
                        "x_device_platform": "android",
                        "x_auth_token": "mzHe5b16qKxRX_xoLEAi",
                        "x_device_app_version": "422"
                    },
                    callback=self.parse,
                    errback=self.handle_error,
                    meta={'product_id': request['product_id'], 'product_name': request['product_name']}
                )
