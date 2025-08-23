# proxies/proxy_checker.py
import requests

def check_proxy(proxy):
    proxies = {
        "http": proxy,
        "https": proxy,
    }
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working. IP: {response.json().get('origin')}")
            return True
        else:
            print(f"Proxy {proxy} returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Proxy {proxy} failed: {e}")
        return False

if __name__ == "__main__":
    with open('proxy_list.txt', 'r') as f:
        proxies = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

    print(f"Checking {len(proxies)} proxies...")
    working_proxies = []
    for proxy in proxies:
        if check_proxy(proxy):
            working_proxies.append(proxy)
    
    print(f"\nFound {len(working_proxies)} working proxies.")
    if working_proxies:
        print("Working proxies:")
        for p in working_proxies:
            print(f"- {p}")

