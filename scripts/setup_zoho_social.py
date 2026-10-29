#!/usr/bin/env python3
"""
LITELAB — Zoho Social One-Command Linker & Auto-Discovery Utility (`scripts/setup_zoho_social.py`)

Exchanges a 1-time Zoho Self-Client Grant Token for a permanent `ZOHO_REFRESH_TOKEN`,
auto-discovers your Zoho Social `portal_id`, `brand_id`, and connected `channels`
via Zoho Social REST API v2 (`https://social.zoho.in/social/v2`), and writes them into `.env`.

Usage:
    # 1. Check current Zoho Social configuration & connection status:
    python scripts/setup_zoho_social.py --status

    # 2. Link Zoho Social using a 1-time Self-Client Grant Token:
    python scripts/setup_zoho_social.py --grant-token 1000.xxxx.yyyy

    # 3. Or link a Zoho Flow Incoming Webhook URL for instant zero-approval scheduling:
    python scripts/setup_zoho_social.py --webhook-url "https://flow.zoho.in/..."
"""

import os
import sys
import json
import argparse
from pathlib import Path
import requests

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
LOCAL_ZOHO_CREDS_PATH = Path.home() / ".zoho-hr-mcp" / "credentials.json"

REQUIRED_ZOHO_SOCIAL_SCOPES = (
    "ZohoSocial.Publish.ALL,"
    "ZohoSocial.Media.ALL,"
    "ZohoSocial.Organization.READ,"
    "ZohoSocial.Integration.READ"
)


def load_existing_zoho_client() -> tuple[str, str, str]:
    """Load LITELAB's Zoho Client ID, Client Secret, and Region from ~/.zoho-hr-mcp/credentials.json or .env."""
    client_id = os.getenv("ZOHO_CLIENT_ID", "")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET", "")
    region = os.getenv("ZOHO_REGION", "in")

    if LOCAL_ZOHO_CREDS_PATH.exists():
        try:
            with open(LOCAL_ZOHO_CREDS_PATH, "r", encoding="utf-8") as f:
                creds = json.load(f)
            client_id = client_id or creds.get("clientId", "")
            client_secret = client_secret or creds.get("clientSecret", "")
            region = creds.get("region", region)
        except Exception:
            pass

    return client_id, client_secret, region


def update_env_file(updates: dict[str, str]) -> None:
    """Create or update key=value pairs in .env."""
    if not ENV_PATH.exists() and ENV_EXAMPLE_PATH.exists():
        ENV_PATH.write_text(ENV_EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    elif not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    updated_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                updated_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def exchange_grant_token(client_id: str, client_secret: str, grant_token: str, region: str = "in") -> dict:
    """Exchange a 10-minute Zoho Self-Client Grant Token for a permanent Refresh Token."""
    url = f"https://accounts.zoho.{region}/oauth/v2/token"
    resp = requests.post(
        url,
        params={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": grant_token,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Zoho token exchange error: {data['error']}")
    return data


def discover_zoho_social_hierarchy(access_token: str, region: str = "in") -> dict:
    """Query /social/v2/socialportals, /socialbrands, and /channels."""
    base = f"https://social.zoho.{region}/social/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    info = {"portal_id": "", "portal_name": "", "brand_id": "", "brand_name": "", "channels": []}

    # 1. Portals
    r_portals = requests.get(f"{base}/socialportals", headers=headers, params={"fields": "id,portal_name,plan"}, timeout=20)
    if r_portals.status_code == 200:
        portals = r_portals.json().get("data") or r_portals.json().get("socialportals") or []
        if portals:
            info["portal_id"] = str(portals[0].get("id", ""))
            info["portal_name"] = portals[0].get("portal_name", "")

    # 2. Brands
    if info["portal_id"]:
        headers["portal_id"] = info["portal_id"]
        r_brands = requests.get(f"{base}/socialbrands", headers=headers, timeout=20)
        if r_brands.status_code == 200:
            brands = r_brands.json().get("data") or r_brands.json().get("socialbrands") or []
            if brands:
                info["brand_id"] = str(brands[0].get("id", ""))
                info["brand_name"] = brands[0].get("brand_name", "")

    # 3. Channels
    if info["portal_id"] and info["brand_id"]:
        headers["brand_id"] = info["brand_id"]
        r_ch = requests.get(f"{base}/channels", headers=headers, timeout=20)
        if r_ch.status_code == 200:
            info["channels"] = r_ch.json().get("data") or r_ch.json().get("channels") or []

    return info


def print_status() -> None:
    client_id, client_secret, region = load_existing_zoho_client()
    print("=" * 72)
    print("  LITELAB — Zoho Social Direct Scheduling Status & Setup Guide")
    print("=" * 72)
    print(f"  ✓ Zoho Region        : {region} (accounts.zoho.{region} / social.zoho.{region})")
    print(f"  ✓ Zoho Client ID     : {client_id[:16]}... (Auto-loaded from LITELAB Zoho config)")
    print(f"  ✓ Zoho Client Secret : {'*' * 12}{client_secret[-6:] if client_secret else 'MISSING'}")
    print("-" * 72)
    print("  HOW TO LINK DIRECT SCHEDULING (CHOOSE OPTION A OR OPTION B):")
    print("-" * 72)
    print("  OPTION A: Zoho Social REST API v2 (Direct OAuth Token)")
    print("    1. Open https://api-console.zoho.in/ -> Select your Self Client")
    print("    2. Click 'Generate Code' and paste these exact Zoho Social scopes:")
    print(f"       {REQUIRED_ZOHO_SOCIAL_SCOPES}")
    print("    3. Run:")
    print("       python scripts/setup_zoho_social.py --grant-token <YOUR_GRANT_TOKEN>")
    print("")
    print("  OPTION B: Zoho Flow Webhook -> Zoho Social 'Schedule Post' Action (Zero-Wait)")
    print("    1. Open https://flow.zoho.in/ -> Create Flow -> Configure Webhook Trigger (JSON)")
    print("    2. Add Action: Zoho Social -> 'Schedule post' (map caption, schedule_time_iso, media_urls)")
    print("    3. Run:")
    print("       python scripts/setup_zoho_social.py --webhook-url \"<YOUR_ZOHO_FLOW_WEBHOOK_URL>\"")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="LITELAB Zoho Social Setup & Auto-Discovery")
    parser.add_argument("--status", action="store_true", help="Show Zoho Social status and setup instructions")
    parser.add_argument("--grant-token", type=str, help="1-time Zoho Self-Client Grant Token with ZohoSocial scopes")
    parser.add_argument("--webhook-url", type=str, help="Zoho Flow Incoming Webhook URL for Zoho Social")
    parser.add_argument("--client-id", type=str, default=None, help="Optional override for Zoho Client ID")
    parser.add_argument("--client-secret", type=str, default=None, help="Optional override for Zoho Client Secret")
    args = parser.parse_args()

    client_id, client_secret, region = load_existing_zoho_client()
    if args.client_id:
        client_id = args.client_id
    if args.client_secret:
        client_secret = args.client_secret

    if args.webhook_url:
        update_env_file({
            "ZOHO_REGION": region,
            "ZOHO_CLIENT_ID": client_id,
            "ZOHO_CLIENT_SECRET": client_secret,
            "ZOHO_FLOW_WEBHOOK_URL": args.webhook_url.strip(),
        })
        print(f"[✓] Saved ZOHO_FLOW_WEBHOOK_URL to {ENV_PATH}")
        return

    if args.grant_token:
        print("[*] Exchanging Zoho Grant Token for permanent Refresh Token...")
        token_data = exchange_grant_token(client_id, client_secret, args.grant_token.strip(), region=region)
        refresh_token = token_data.get("refresh_token", "")
        access_token = token_data.get("access_token", "")
        print("[✓] Token exchange succeeded!")

        updates = {
            "ZOHO_REGION": region,
            "ZOHO_CLIENT_ID": client_id,
            "ZOHO_CLIENT_SECRET": client_secret,
        }
        if refresh_token:
            updates["ZOHO_REFRESH_TOKEN"] = refresh_token

        try:
            info = discover_zoho_social_hierarchy(access_token, region=region)
            if info["portal_id"]:
                updates["ZOHO_SOCIAL_PORTAL_ID"] = info["portal_id"]
                print(f"[✓] Auto-discovered Portal: {info['portal_name']} ({info['portal_id']})")
            if info["brand_id"]:
                updates["ZOHO_SOCIAL_BRAND_ID"] = info["brand_id"]
                print(f"[✓] Auto-discovered Brand : {info['brand_name']} ({info['brand_id']})")
            if info["channels"]:
                print(f"[✓] Connected Channels    : {len(info['channels'])} channel(s) found")
        except Exception as exc:
            print(f"[!] Note: Auto-discovery returned: {exc}")

        update_env_file(updates)
        print(f"[✓] Updated {ENV_PATH} with Zoho Social credentials!")
        return

    print_status()


if __name__ == "__main__":
    main()
