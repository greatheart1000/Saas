"""
test_clients.py

功能：
- 创建 3 个账号（NORMAL / VIP / ENTERPRISE）
- 登录获取 JWT
- 使用 JWT 创建 API Key（服务端在创建时返回明文一次）
- 用 API Key / JWT 调用 /generate 验证
- 并发压测每个账号的 API Key（粗略模拟 QPS），统计响应码（包括 429）
- 将结果保存到 test_report.json
"""

import os
import time
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE = os.environ.get("SAAS_BASE", "http://127.0.0.1:8000")

USERS = [
    {"org_name": "org_normal_test", "username": "user_normal_test", "password": "pass123", "user_type": "NORMAL"},
    {"org_name": "org_vip_test", "username": "user_vip_test", "password": "pass123", "user_type": "VIP"},
    {"org_name": "org_enterprise_test", "username": "user_enterprise_test", "password": "pass123", "user_type": "ENTERPRISE"},
]

HEADERS = {"Content-Type": "application/json"}


def signup(user):
    url = f"{BASE}/signup"
    resp = requests.post(url, json=user, headers=HEADERS, timeout=10)
    return resp

def login(username, password):
    url = f"{BASE}/token"
    data = {"username": username, "password": password}
    resp = requests.post(url, data=data, timeout=10)
    return resp

def create_api_key(token, name=None, scopes=None, expires_days=None):
    url = f"{BASE}/apikeys"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {}
    if name:
        payload["name"] = name
    if scopes:
        payload["scopes"] = scopes
    if expires_days:
        payload["expires_days"] = expires_days
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    return resp

def generate_with_api_key(api_key, payload=None):
    url = f"{BASE}/generate"
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    resp = requests.post(url, json=payload or {"prompt": "hello"}, headers=headers, timeout=10)
    return resp

def generate_with_jwt(token, payload=None):
    url = f"{BASE}/generate"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload or {"prompt": "hello"}, headers=headers, timeout=10)
    return resp

def simulate_qps_api_key(api_key, concurrency: int, duration_sec: int):
    """
    简单并发模拟器：在 duration_sec 时间内，通过并发线程持续发送请求，
    返回统计： {total, success_2xx, counts_by_status}
    """
    end_time = time.time() + duration_sec
    stats = {"total": 0, "success": 0, "status_counts": {}}

    def worker():
        try:
            r = generate_with_api_key(api_key)
            return r.status_code, r.text
        except Exception as e:
            return 0, str(e)

    with ThreadPoolExecutor(max_workers=concurrency) as exe:
        futures = []
        # initial batch
        for _ in range(concurrency):
            futures.append(exe.submit(worker))
        while time.time() < end_time:
            # wait for any future to complete and resubmit
            done, not_done = [], []
            for f in futures:
                if f.done():
                    done.append(f)
                else:
                    not_done.append(f)
            for f in done:
                try:
                    status, _ = f.result()
                except Exception:
                    status = 0
                stats["total"] += 1
                key = str(status)
                stats["status_counts"][key] = stats["status_counts"].get(key, 0) + 1
                if 200 <= status < 300:
                    stats["success"] += 1
                # resubmit if still within time
                if time.time() < end_time:
                    not_done.append(exe.submit(worker))
            # small sleep to avoid busy loop
            time.sleep(0.005)
            futures = not_done
        # wait remaining futures
        for f in futures:
            try:
                status, _ = f.result(timeout=2)
            except Exception:
                status = 0
            stats["total"] += 1
            key = str(status)
            stats["status_counts"][key] = stats["status_counts"].get(key, 0) + 1
            if 200 <= status < 300:
                stats["success"] += 1
    return stats

def main():
    results = {}
    # 1. signup & login & create apikey
    for u in USERS:
        print(f"===> Setting up {u['username']} ({u['user_type']})")
        resp = signup(u)
        if resp.status_code not in (200, 201):
            print(f" signup status {resp.status_code}: {resp.text}")
            # continue anyway - maybe already exists
        lr = login(u["username"], u["password"])
        if lr.status_code != 200:
            print(f" login failed for {u['username']}: {lr.status_code} {lr.text}")
            continue
        token = lr.json()["access_token"]
        print(" got token len:", len(token))
        ck = create_api_key(token, name=f"{u['username']}-key")
        if ck.status_code != 200:
            print(" create apikey failed:", ck.status_code, ck.text)
            key_plain = None
        else:
            data = ck.json()
            key_plain = data.get("key")
            print(" created apikey:", key_plain)
        results[u["username"]] = {"token": token, "api_key": key_plain, "user_type": u["user_type"]}
        time.sleep(0.3)

    # 2. quick sanity calls
    for uname, info in results.items():
        print(f"\n==== quick call test for {uname}")
        if info["api_key"]:
            r = generate_with_api_key(info["api_key"])
            print(" api_key call:", r.status_code, r.text[:200])
        r2 = generate_with_jwt(info["token"])
        print(" jwt call:", r2.status_code, r2.text[:200])

    # 3. concurrency / qps simulation using API Key
    # We'll approximate:
    # - NORMAL target QPS 10 -> use concurrency 10 for 10s
    # - VIP target QPS 100 -> use concurrency 100 for 10s
    # - ENTERPRISE -> high concurrency to show not limited
    sim_config = {
        "user_normal_test": {"concurrency": 10, "duration": 10},
        "user_vip_test": {"concurrency": 100, "duration": 10},
        "user_enterprise_test": {"concurrency": 200, "duration": 10},
    }

    report = {}
    for uname, cfg in sim_config.items():
        info = results.get(uname)
        if not info:
            print("no info for", uname)
            continue
        api_key = info.get("api_key")
        if not api_key:
            print(f"no api key for {uname}, skipping concurrency test")
            continue
        print(f"\n===> Simulating for {uname} concurrency={cfg['concurrency']} duration={cfg['duration']}s")
        stats = simulate_qps_api_key(api_key, concurrency=cfg["concurrency"], duration_sec=cfg["duration"])
        print(f" result for {uname}: total={stats['total']}, success={stats['success']}, status_counts={stats['status_counts']}")
        report[uname] = stats

    out = {"results": results, "report": report}
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nSaved test_report.json")

if __name__ == "__main__":
    main()