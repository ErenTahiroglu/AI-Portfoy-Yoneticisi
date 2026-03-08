import requests

def fetch_all_funds():
    url = "https://www.tefas.gov.tr/api/DB/BindCurrentFundInfo"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    data = {
        "fontip": "YAT"
    }
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        json_resp = resp.json()
        print(f"Got {len(json_resp.get('data', []))} YAT funds")
        for fund in json_resp.get('data', [])[:5]:
            print(f"{fund.get('FONKODU')}: {fund.get('FONUNVAN')}")
    except Exception as e:
        print("YAT error:", e)

if __name__ == "__main__":
    fetch_all_funds()
