import requests

r = requests.session()
result = r.get("http://45.8.148.105:61208/api/4/diskio")
print(result.json())


