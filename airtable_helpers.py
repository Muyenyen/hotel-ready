import os
import requests

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Leads"

def save_lead_to_airtable(lead: dict):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": lead["name"],
            "LinkedIn URL": lead["profile_url"],
            "Category": lead["category"],
            "Score": lead["score"],
            "Qualification Note": lead["reason"],
            "Message": lead["message"],
            "Post Category": lead["post_category"],
            "Post Text": lead["post_text"],
            "Status": "New"
        }
    }
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Failed to save to Airtable: {res.text}")
    return res.json()