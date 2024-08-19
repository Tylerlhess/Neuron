import requests

r = requests.session()
r.get("curl http://localhost:61208/api/4/diskio")
print(r.json)


