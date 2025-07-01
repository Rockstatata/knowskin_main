import requests
resp = requests.post("http://18.183.220.114:8000/run_batches/")
print(resp.json())