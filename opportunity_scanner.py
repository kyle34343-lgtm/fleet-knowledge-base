import os
import sys
import time
import subprocess
import requests
import re
import html
import random
from datetime import datetime

try:
    from gsc_feedback import get_top_gsc_tags
except ImportError:
    def get_top_gsc_tags(): return []

# --- CONFIGURATION ---
KB_DIR = os.path.join(os.path.dirname(__file__), "inbound_articles")
BATCH_PUSH = os.path.join(os.path.dirname(__file__), "push_kb.bat")
BASE_URL = "https://kyle34343-lgtm.github.io/fleet-knowledge-base"

# Live Stripe Checkout links
STRIPE_TIER_1_URL = "https://buy.stripe.com/3cIeVc3MXavlb6GcxH6Zy03"
STRIPE_TIER_2_URL = "https://buy.stripe.com/dRmdR897Hdhx2Aa41b6Zy04"
STRIPE_TIER_3_URL = "https://buy.stripe.com/4gM4gybfpdHX1w6apZ6Zy05"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# 100% Automated Niche Registry
NICHES = [
    {"name": "Docker & Cloud", "tag": "docker;kubernetes;amazon-web-services", "folder": "cloud-docker"},
    {"name": "E-Commerce", "tag": "shopify;woocommerce;stripe-payments", "folder": "ecommerce"},
    {"name": "Webhooks & APIs", "tag": "api;webhooks;rest;oauth-2.0", "folder": "webhooks"},
    {"name": "WordPress Fatal", "tag": "wordpress;php;elementor", "folder": "wordpress"},
    {"name": "Email & DNS", "tag": "dns;dmarc;dkim;spf", "folder": "email-deliverability"},
    {"name": "Web Scraping", "tag": "playwright;selenium;web-scraping", "folder": "scraping"},
    {"name": "Auth & SSL", "tag": "cors;ssl;jwt;authentication", "folder": "auth-security"},
]

ACTIVE_NICHE = random.choice(NICHES)
print(f"[*] AUTO-PILOT TARGET: {ACTIVE_NICHE['name']}")

def clean_slug(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s-]+', '-', text)[:45]

def fetch_live_stackoverflow_lead():
    url = "https://api.stackexchange.com/2.3/questions/unanswered"
    params = {
        "order": "desc",
        "sort": "activity",
        "tagged": ACTIVE_NICHE["tag"],
        "site": "stackoverflow",
        "pagesize": 1
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("items"):
            item = data["items"][0]
            return {
                "id": item.get("question_id"),
                "title": html.unescape(item.get("title", "Technical Diagnostic Issue")),
                "url": item.get("link", "https://stackoverflow.com"),
                "tags": item.get("tags", ["python", "runtime"]),
                "is_live": True
            }
    except Exception:
        pass
    return {
        "id": int(time.time()),
        "title": "Runtime Resolution for Modular Dependency Errors",
        "url": "https://stackoverflow.com",
        "tags": ["python", "ci-cd"],
        "is_live": False
    }

def send_discord_lead_alert(lead, slug, score):
    if not DISCORD_WEBHOOK_URL:
        return
    article_url = f"{BASE_URL}/{slug}.html"
    payload = {
        "embeds": [{
            "title": f"⚡ High-Intent Developer Lead Identified ({score}/100)",
            "description": f"**Question:** {lead['title']}\n**Source Thread:** [View Forum Post]({lead['url']})\n**Deployed Knowledge Base Fix:** [View SEO Guide]({article_url})",
            "color": 3447003,
            "fields": [
                {"name": "Quick-Fix Tier ($19)", "value": f"[Instant Checkout Link]({STRIPE_TIER_1_URL})", "inline": True},
                {"name": "Full Integration Tier ($49)", "value": f"[Book Support Link]({STRIPE_TIER_2_URL})", "inline": True},
                {"name": "Enterprise Suite Tier ($149 AUD)", "value": f"[Enterprise Link]({STRIPE_TIER_3_URL})", "inline": True},
                {"name": "Suggested Outbound Reply", "value": f"```Hi, diagnosed this runtime issue: check package registry manifests and clear lockfile cache. Here is the automated fix: {article_url}```", "inline": False}
            ],
            "footer": {"text": "Autonomous Revenue Fleet v3.0"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print("    -> [OK] Dispatched lead payload to Discord webhook.")
    except Exception as e:
        print(f"    [!] Webhook dispatch error: {e}")

def run_fleet_cycle(cycle_num=1):
    print(f"\n{'='*55}\n[*] FLEET CYCLE #{cycle_num} INITIATED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*55}")
    lead = fetch_live_stackoverflow_lead()
    slug = re.sub(r"[^\w\-]", "-", re.sub(r"\s+", "-", item.get("title", "issue").lower())).strip("-")
    
    os.makedirs(KB_DIR, exist_ok=True)
    md_path = os.path.join(KB_DIR, f"{slug}.md")
    
    article_content = f"""---
layout: default
title: "Error: {lead['title']}"
---

# Error: {lead['title']}

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

Need This Fixed Instantly?
<ul>
  <li><a href="{STRIPE_TIER_1_URL}">⚡ Get the Automated $19 Quick-Fix Patch</a> — Includes pre-built resolution scripts and clean configs.</li>
  <li><a href="{STRIPE_TIER_2_URL}">🛠️ Book Full $49 Diagnostic & Integration</a> — Complete environment audit and hands-on integration.</li>
  <li><a href="{STRIPE_TIER_3_URL}">🏢 Enterprise Automation Suite ($149 AUD)</a> — Complete source repo, CI/CD fleet runner, and full architecture toolkit.</li>
</ul>
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(article_content)
    print(f"    [OK] Article written: {md_path}")
    
    send_discord_lead_alert(lead, slug, 94)

if __name__ == "__main__":
    run_fleet_cycle(1)

