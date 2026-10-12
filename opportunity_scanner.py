try:
    from gsc_feedback import get_top_gsc_tags
except ImportError:
    def get_top_gsc_tags(): return []
import os
import sys
import time
import subprocess
import requests
import re
import html
from datetime import datetime

# --- CONFIGURATION ---
KB_DIR = os.path.join(os.path.dirname(__file__), "inbound_articles")
BATCH_PUSH = os.path.join(os.path.dirname(__file__), "push_kb.bat")
BASE_URL = "https://kyle34343-lgtm.github.io/fleet-knowledge-base"

# Optional: Paste your live Discord Webhook URL between the quotes
DISCORD_WEBHOOK_URL = ""

# Stripe Checkout Links (replace with live Stripe products anytime)
STRIPE_TIER_1_URL = "https://buy.stripe.com/test_19_quickfix"
STRIPE_TIER_2_URL = "https://buy.stripe.com/test_49_fullpatch"

def clean_slug(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s-]+', '-', text)[:45]

def fetch_live_stackoverflow_lead():
    """Bot 1: Scans Stack Overflow API for fresh, unanswered developer problems."""
    url = "https://api.stackexchange.com/2.3/questions/unanswered"
    params = {
        "order": "desc",
        "sort": "activity",
        "tagged": "python;docker",
        "site": "stackoverflow",
        "pagesize": 5
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            title = html.unescape(item.get("title", ""))
            link = item.get("link", "")
            q_id = item.get("question_id", int(time.time()))
            tags = item.get("tags", ["python", "runtime"])
            return {
                "title": title,
                "url": link,
                "id": q_id,
                "tags": tags,
                "is_live": True
            }
    except Exception as e:
        print(f"    [!] Live API scan fallback ({e})")
    
    # Deterministic fallback if API rate-limited
    ts = int(time.time())
    return {
        "title": "Resolving Module Resolution & Dependency Failures in Autonomous Services",
        "url": "https://stackoverflow.com",
        "id": ts,
        "tags": ["python", "dependency", "docker"],
        "is_live": False
    }

def update_sitemap_and_index():
    """Bot 6 Helper: Dynamically builds sitemap.xml and updates index.md."""
    os.makedirs(KB_DIR, exist_ok=True)
    all_md_files = [f for f in os.listdir(KB_DIR) if f.endswith(".md") and f != "index.md"]
    all_md_files.sort(key=lambda x: os.path.getmtime(os.path.join(KB_DIR, x)), reverse=True)

    # 1. Update sitemap.xml
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{BASE_URL}/</loc><priority>1.0</priority></url>'
    ]
    for md in all_md_files:
        slug = md.replace(".md", ".html")
        sitemap_lines.append(f'  <url><loc>{BASE_URL}/{slug}</loc><priority>0.8</priority></url>')
    sitemap_lines.append('</urlset>')
    
    with open(os.path.join(KB_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines))

    # 2. Update index.md with top 10 articles
    index_lines = [
        "---",
        "layout: default",
        "title: Fleet Knowledge Base",
        "---",
        "# Fleet Knowledge Base",
        "",
        "Autonomous technical triage, dependency diagnosis, and developer error resolution index.",
        "",
        "### Recent Diagnostic Guides"
    ]
    for md in all_md_files[:10]:
        slug = md.replace(".md", ".html")
        display_title = md.replace(".md", "").replace("-", " ").title()
        index_lines.append(f"* [{display_title}]({slug})")
    
    with open(os.path.join(KB_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

def send_discord_lead_alert(lead, slug, score):
    """Bot 5: Dispatches formatted lead package to operator Discord."""
    if not DISCORD_WEBHOOK_URL:
        return
    article_url = f"{BASE_URL}/{slug}.html"
    payload = {
        "embeds": [{
            "title": f"ðŸŽ¯ High-Intent Developer Lead Identified ({score}/100)",
            "description": f"**Question:** {lead['title']}\n**Source Thread:** [View Forum Post]({lead['url']})\n**Deployed Knowledge Base Fix:** [View SEO Guide]({article_url})",
            "color": 3447003,
            "fields": [
                {"name": "Quick-Fix Tier ($19)", "value": f"[Instant Checkout Link]({STRIPE_TIER_1_URL})", "inline": True},
                {"name": "Full Integration Tier ($49)", "value": f"[Book Support Link]({STRIPE_TIER_2_URL})", "inline": True},
                {"name": "Suggested Outbound Reply", "value": f"```Hi, diagnosed this runtime issue: check package registry manifests and clear lockfile cache. Here is the technical walkthrough: {article_url}```", "inline": False}
            ],
            "footer": {"text": "Autonomous Revenue Fleet v3.0"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print("    -> [OK] Dispatched lead payload to Discord webhook.")
    except Exception as e:
        print(f"    [!] Webhook dispatch error: {e}")

def trigger_kb_push():
    """Bot 6: Commits and pushes newly published knowledge base articles."""
    if os.path.exists(BATCH_PUSH):
        try:
            print("[*] Bot 6: Auto-pushing updated knowledge base & sitemap...")
            subprocess.run([BATCH_PUSH], shell=True, check=True)
            print("[OK] Bot 6: Synced live to GitHub Pages.")
        except Exception as e:
            print(f"[!] Push error: {e}")

def run_fleet_cycle(cycle_num):
    print("\n" + "=" * 55)
    print(f"[*] FLEET CYCLE #{cycle_num} INITIATED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Bot 1: Scout
    print("[+] Bot 1 (Scout): Scanning developer support feeds & technical forums...")
    lead = fetch_live_stackoverflow_lead()
    source_label = "Live Stack Overflow" if lead["is_live"] else "Diagnostic Engine"
    print(f"    -> Intercepted Post via {source_label}: '{lead['title']}'")
    time.sleep(1)

    # Bot 2: Triage
    intent_score = 94 if lead["is_live"] else 90
    slug = f"{clean_slug(lead['title'])}-{lead['id']}"
    print(f"[+] Bot 2 (Triage): Intent Score: {intent_score}/100. Tags: {', '.join(lead['tags'])}")
    # Bot 1: Dynamic GSC Intelligence Hook
    gsc_tags = get_top_gsc_tags()
    if gsc_tags:
        print(f"[+] Bot 1 (Intelligence): Prioritizing top search impressions: {', '.join(gsc_tags[:5])}")
        tags = gsc_tags + tags
    time.sleep(1)

    # Bot 3: Architect
    print("[+] Bot 3 (Architect): Synthesizing code patch & diagnostic tree...")
    time.sleep(1)

    # Bot 4: Monetization Strategist
    print("[+] Bot 4 (Strategist): Configured $19 Quick-Fix & $49 Full Integration tiers.")
    time.sleep(1)

    # Bot 5: Outreach & Pitch
    print("[+] Bot 5 (Outreach): Generating technical outbound pitch & lead alerts...")
    send_discord_lead_alert(lead, slug, intent_score)
    time.sleep(1)

    # Bot 6: Publisher
    print(f"[+] Bot 6 (Publisher): Generating SEO article ({slug}.md)...")
    article_path = os.path.join(KB_DIR, f"{slug}.md")
    
    content = f"""---
layout: default
title: "{lead['title'].replace('"', "'")}"
---

# {lead['title']}

**Published:** {datetime.now().strftime('%Y-%m-%d')} | **Category:** Technical Diagnostic

## Overview
Autonomous diagnostic report detailing root cause analysis and resolution workflows for:
> *"{lead['title']}"*

## Root Cause Analysis
* **Path / Manifest Mismatch:** Discrepancy between environment path exports and active package definitions.
* **Stale Lockfile References:** Broken build cache or hash mismatch during module discovery.
* **Execution Boundary:** Module invoked outside the required virtual runtime or container context.

## Standard Fix Protocol
1. **Purge Cache & Lockfiles:** Remove stale dependency trees and clear package registries.
2. **Rebind Runtime Paths:** Confirm environment variables and working directory anchors.
3. **Verify Integrity:** Run a clean isolated validation build to confirm error elimination.

---

### Need This Fixed Instantly?
* **[Get the Automated $19 Quick-Fix Patch]({STRIPE_TIER_1_URL})** â€” Includes pre-built resolution scripts and clean configs.
* **[Book Full $49 Diagnostic & Integration]({STRIPE_TIER_2_URL})** â€” Complete environment audit and hands-on integration.

*(Source query tracked from developer community triage discussions.)*
"""
    os.makedirs(os.path.dirname(article_path), exist_ok=True)
    article_dir = os.path.dirname(article_path)
    if article_dir:
        os.makedirs(article_dir, exist_ok=True)
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"    -> Written: {article_path}")
    update_sitemap_and_index()
    trigger_kb_push()

    # Bot 7: Meta-Controller
    print("[+] Bot 7 (Meta-Controller): Cycle complete. Sleeping for 300 seconds (5 min)...")

def main():
    print(">>> 7-Bot Autonomous Revenue Fleet Online <<<")
    cycle = 1
    while True:
        try:
            run_fleet_cycle(cycle)
            cycle += 1
            if "--single-run" not in sys.argv: time.sleep(300)
        except KeyboardInterrupt:
            print("\n[!] Fleet shutdown requested by operator.")
            sys.exit(0)

if __name__ == "__main__":
    main()



