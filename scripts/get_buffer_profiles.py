#!/usr/bin/env python3
"""
Buffer Profile Discovery Helper for LITELAB.
Lists connected Buffer profiles and their IDs using BUFFER_ACCESS_TOKEN.
"""

import os
import requests

def main():
    token = os.getenv("BUFFER_ACCESS_TOKEN") or os.getenv("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        print("[!] Set BUFFER_ACCESS_TOKEN in .env first.")
        return
    resp = requests.get("https://api.bufferapp.com/1/profiles.json", params={"access_token": token}, timeout=15)
    resp.raise_for_status()
    for p in resp.json():
        print(f"Service: {p.get('service')} | Handle: {p.get('formatted_username')} | ID: {p.get('id')}")

if __name__ == "__main__":
    main()
