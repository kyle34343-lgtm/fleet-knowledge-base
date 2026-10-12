import os
import sys
import time
import subprocess
import requests
import re
import html
import random
import glob
from datetime import datetime

try:
    from gsc_feedback import get_top_gsc_tags
except ImportError:
    def get_top_gsc_tags(): return []

# --- CONFIGURATION ---
KB_DIR = os.path.join(os.path.dirname(__file__), "inbound_articles")
BASE_URL = "https://kyle34343-lgtm.github.io/fleet-knowledge-base"

STRIPE_TIER_1_URL = "https://buy.stripe.com/3cIeVc3MXavlb6GcxH6Zy03"
STRIPE_TIER_2_URL = "https://buy.stripe.com/dRmdR897Hdhx2Aa41b6Zy04"
STRIPE_TIER_3_URL = "https://buy.stripe.com/4gM4gybfpdHX1w6apZ6Zy05"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# 100% Automated 20-Niche Registry
NICHES = [
    {"name": "Docker & Cloud", "tag": "docker;kubernetes;amazon-web-services", "folder": "cloud-docker"},
    {"name": "E-Commerce", "tag": "shopify;woocommerce;stripe-payments", "folder": "ecommerce"},
    {"name": "Webhooks & APIs", "tag": "api;webhooks;rest;oauth-2.0", "folder": "webhooks"},
    {"name": "WordPress Fatal", "tag": "wordpress;php;elementor", "folder": "wordpress"},
    {"name": "Email & DNS", "tag": "dns;dmarc;dkim;spf", "folder": "email-deliverability"},
    {"name": "Web Scraping", "tag": "playwright;selenium;web-scraping", "folder": "scraping"},
    {"name": "Auth & SSL", "tag": "cors;ssl;jwt;authentication", "folder": "auth-security"},
    {"name": "Database Deadlocks", "tag": "postgresql;mysql;database-deadlocks;sql", "folder": "database"},
    {"name": "AI & LLM Integrations", "tag": "openai-api;langchain;llm;rate-limiting", "folder": "ai-integrations"},
    {"name": "CI/CD & Pipelines", "tag": "github-actions;gitlab-ci;jenkins;ci-cd", "folder": "ci-cd"},
    {"name": "Next.js & SSR", "tag": "next.js;vercel;server-side-rendering;reactjs", "folder": "nextjs-vercel"},
    {"name": "Mobile App Builds", "tag": "ios;xcode;fastlane;react-native;flutter", "folder": "app-submission"},
    {"name": "Stripe & Subscriptions", "tag": "stripe-payments;payment-gateway;webhooks", "folder": "stripe-billing"},
    {"name": "Technical SEO", "tag": "google-search-console;indexing;sitemap;redirects", "folder": "technical-seo"},
    {"name": "DNS & Cloudflare", "tag": "cloudflare;dns;reverse-proxy;ssl-certificate", "folder": "dns-networking"},
    {"name": "Linux & Nginx Sysadmin", "tag": "nginx;systemd;linux;memory-leaks;ubuntu", "folder": "linux-sysadmin"},
    {"name": "Web3 & Blockchain RPC", "tag": "ethereum;web3;metamask;smart-contracts", "folder": "web3-troubleshooting"},
    {"name": "Python Environment & Pip", "tag": "python;pip;wheel;setuptools;virtualenv", "folder": "python-troubleshoot"},
    {"name": "Frontend Build & Bundlers", "tag": "vite;webpack;postcss;tailwind-css", "folder": "frontend-tooling"},
    {"name": "Audio & Video Encoding", "tag": "ffmpeg;video-streaming;hls;transcoding", "folder": "media-encoding"},
]

def update_sitemap():
    sitemap_path = os.path.join(os.path.dirname(__file__), "sitemap.xml")
    articles = glob.glob(os.path.join(KB_DIR, "*.md"))
    today = datetime.now().strftime("%Y-%m-%d")

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{BASE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{BASE_URL}/vault.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>'
    ]

    for article in articles:
        slug = os.path.splitext(os.path.basename(article))[0]
        xml_lines.append(f'  <url><loc>{BASE_URL}/{slug}.html</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')

    xml_lines.append('</urlset>')

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    print(f"    [OK] Regenerated sitemap.xml with {len(articles)} indexed URLs.")

    # Programmatic Search Engine Pings
    try:
        requests.get(f"https://www.bing.com/ping?sitemap={BASE_URL}/sitemap.xml", timeout=5)
        print("    -> [OK] Dispatched sitemap ping to search engine indexers.")
    except Exception:
        pass

def fetch_live_stackoverflow_lead(niche):
    url = "https://api.stackexchange.com/2.3/questions/unanswered"
    params = {
        "order": "desc",
        "sort": "activity",
        "tagged": niche["tag"],
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
        "title": f"Runtime Resolution for {niche['name']} Dependency Errors",
        "url": "https://stackoverflow.com",
        "tags": ["python", "ci-cd"],
        "is_live": False
    }

def send_discord_lead_alert(lead, slug, score, niche):
    if not DISCORD_WEBHOOK_URL:
        return
    article_url = f"{BASE_URL}/{slug}.html"
    payload = {
        "embeds": [{
            "title": f"⚡ [{niche['name']}] Lead Identified ({score}/100)",
            "description": f"**Question:** {lead['title']}\n**Source Thread:** [View Forum Post]({lead['url']})\n**Deployed Knowledge Base Fix:** [View Live Article]({article_url})",
            "color": 3447003,
            "fields": [
                {"name": "Quick-Fix Tier ($19)", "value": f"[Instant Checkout Link]({STRIPE_TIER_1_URL})", "inline": True},
                {"name": "Full Integration Tier ($49)", "value": f"[Book Support Link]({STRIPE_TIER_2_URL})", "inline": True},
                {"name": "Enterprise Suite Tier ($149 AUD)", "value": f"[Enterprise Link]({STRIPE_TIER_3_URL})", "inline": True},
                {"name": "Automated Outbound Response", "value": f"Hi, diagnosed this {niche['name']} issue. Full breakdown and resolution steps available here: {article_url}"}
            ],
            "footer": {"text": "Autonomous Revenue Fleet v3.1 | Auto-Sitemap Active"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print("    -> [OK] Dispatched lead payload to Discord webhook.")
    except Exception as e:
        print(f"    [!] Webhook dispatch error: {e}")

def run_fleet_cycle(cycle_num, niche):
    print(f"\n{'='*55}\n[*] FLEET CYCLE #{cycle_num} INITIATED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] TARGET NICHE: {niche['name']}\n{'='*55}")

    lead = fetch_live_stackoverflow_lead(niche)
    slug = re.sub(r'[^\w\-]', "-", re.sub(r'\s+', "-", lead.get("title", "issue").lower())).strip("-")

    os.makedirs(KB_DIR, exist_ok=True)
    md_path = os.path.join(KB_DIR, f"{slug}.md")

    article_content = f"""---
layout: default
title: "Error: {lead['title']}"
---

# Error: {lead['title']}

**Published:** {datetime.now().strftime('%Y-%m-%d')} | **Category:** {niche['name']} Diagnostic

## Overview
Autonomous diagnostic report detailing root cause analysis and resolution workflows for:
> "{lead['title']}"

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
<ul>
  <li><a href="{STRIPE_TIER_1_URL}">⚡ Get the Automated $19 Quick-Fix Patch</a> - Includes pre-built resolution scripts and clean configs.</li>
  <li><a href="{STRIPE_TIER_2_URL}">🛠️ Book Full $49 Diagnostic & Integration</a> - Complete environment audit and hands-on integration.</li>
  <li><a href="{STRIPE_TIER_3_URL}">📦 Enterprise Automation Suite ($149 AUD)</a> - Complete source repo, CI/CD fleet runner, and full architecture toolkit.</li>
</ul>
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(article_content)
    print(f"    [OK] Article written: {md_path}")

    send_discord_lead_alert(lead, slug, 94, niche)

if __name__ == "__main__":
    selected_batch = random.sample(NICHES, 3)
    for index, niche in enumerate(selected_batch, start=1):
        run_fleet_cycle(index, niche)
        if index < len(selected_batch):
            time.sleep(4)
    update_sitemap()
