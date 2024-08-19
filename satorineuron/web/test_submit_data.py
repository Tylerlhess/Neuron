import requests, json

r = requests.session()
result = r.get("http://45.8.148.105:61208/api/4/diskio")
print(result.json()[2]["write_bytes_gauge"])
data = {"data": result.json()[2]["write_bytes_gauge"]}
print(data)
result = r.post("http://127.0.0.1:24622/submit_data", json=data)
print(result.status_code, result.json(), result.text)


