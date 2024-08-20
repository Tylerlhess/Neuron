import requests, json, random

wallets = [
    "ENPNnTWAWvC38vTLkRgv6TDcNdt9uzspDJ",
    "EM6G7njEXAeUjBSPtYw4N6CPHf6xT3Sbta",
    "EfdejUh2pUgGM9xxfeaMgMpNEaYFiaemif",
    "EPAsgytzqwZqcjwWt68781W9afrAa4di2k",
    "EJmhXbMofz2bo3XCN1wW8FZUg81x3sCrzv",
    "ES4up7JXR8ETP7d4SGTeyozS8p9DExwuda",
    "ELcUPfiDLYasYrpAT1XrG2wPRMKWU6HCLo",
    "ELGBBSqc5nxsyocBbxEKHEv5ZL897vSn7m",
    "EVSykaqfKt2PSGFBNzdBqmZhFT5SqHweHV",
    "EN6BDV5wG6YwWaLojVEbpEHftXNkKuUcEJ",
    "EgA9zNZNZFq1fNX9TvhL7tvL39jj4ZeXjm",
    "EbScJHYmTWje4pZeRJ9KF8X7ZSrSH8p8uo",
    "EeuFypdFw8Ti914FhGg9dqegArPbNMpwyS",
    "EPxrGGc6YrBQKLvVEwrZ5r7NjbqdGdJHhD",
    "ETUXv9WExnnBzJAK6v789svtkZZdsqHwLq",
    "EaLE7AZBdmGau1hUExdoJCoFb99sqazCAV",
    "ELjQ2Rx2L5jhTVThJY9fRpReyd3UmbyZdh",
    "ENAV3TxejD5w9zQEXfi3Q7M6PJ8Tf6Unp3",
    "EdgBxTRwZZo1xHq24p4rrTB7ZyPfgeN1Ah",
    "EVednaMKprwVQzwAE1KFRYLx3vTbwUbXNk",
]

r = requests.session()
result = r.get("http://45.8.148.105:61208/api/4/diskio")
print(result.json()[2]["write_bytes_gauge"])
data = {"data": result.json()[2]["write_bytes_gauge"]}
print(data)
result = r.post(f"http://127.0.0.1:24622/submit_data/{data['data']}")
print(result.status_code, result.text)

result = r.get(f"http://127.0.0.1:24622/json")
print(result.status_code, result.text)

result = r.get(f"http://127.0.0.1:24622/topic")
print(result.status_code, result.text)

prediction = {"wallet": "", "prediction": data["data"]}

print("Begginging posting data")
for wallet in wallets:
    variance = random.uniform(-0.01, 0.01)
    prediction["prediction"] *= 1 + variance
    prediction["wallet"] = wallet
    result = r.post(f"http://127.0.0.1:24622/rec_pred", json=prediction)
    print(result.status_code, result.text)

result = r.post(f"http://127.0.0.1:24622/latest_data")
print(result.status_code, result.text)

result = r.get(f"http://127.0.0.1:24622/get_current_data")
print(result.status_code, result.text)

result = r.get(f"http://127.0.0.1:24622/buildBlock")
print(result.status_code, result.text)

