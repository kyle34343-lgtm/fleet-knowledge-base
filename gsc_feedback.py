import os
import json
from datetime import datetime, timedelta

def get_top_gsc_tags(site_url="https://kyle34343-lgtm.github.io/fleet-knowledge-base/"):
    """
    Connects to Google Search Console API via service account credentials.
    Returns prioritized tags weighted by real impressions.
    Falls back gracefully if no data exists yet.
    """
    creds_json = os.environ.get("GSC_CREDENTIALS_JSON")
    if not creds_json:
        return []

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )

        service = build("searchconsole", "v1", credentials=credentials)

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=28)

        body = {
            "startDate": str(start_date),
            "endDate": str(end_date),
            "dimensions": ["query"],
            "rowLimit": 20
        }

        response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        rows = response.get("rows", [])

        if not rows:
            return []

        # Sort by impressions and extract prominent keywords
        rows.sort(key=lambda r: r.get("impressions", 0), reverse=True)
        top_queries = [r["keys"][0].lower() for r in rows if "keys" in r and r["keys"]]

        tags = []
        for q in top_queries:
            for word in q.split():
                if len(word) > 3 and word not in ["error", "cannot", "failed", "how", "with"]:
                    tags.append(word)

        return list(dict.fromkeys(tags))[:10]

    except Exception as e:
        print(f"[!] GSC Feedback Notice: {e}")
        return []
