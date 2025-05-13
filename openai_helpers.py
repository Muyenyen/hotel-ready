import os
from openai import OpenAI

# Pseudo/fake key for development; replace with actual key to run
api_key = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOUR_REAL_KEY")
client = OpenAI(api_key=api_key)

def run_lead_qualifier(assistant_id, name, profile_url, post_category):
    prompt = (
        f"User: {name}\nProfile: {profile_url}\n"
        f"Post Category: {post_category}\n"
        "Categorize as Owner/Developer, Broker, Brand/Exec, or General.\n"
        "Score from 1-10 and explain why."
    )
    try:
        thread = client.beta.threads.create()
        run = client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread_id=thread.id,
            messages=[{"role": "user", "content": prompt}]
        )
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        result = client.beta.threads.messages.list(thread_id=thread.id)
        return result.data[0].content[0].text.value
    except Exception as e:
        return f"[!] GPT scoring failed: {e}"

def run_outreach_crafter(assistant_id, name, profile_url, category, reason, post_text):
    prompt = (
        f"Create a LinkedIn message for: {name} ({category})\n"
        f"Profile: {profile_url}\n"
        f"Reason: {reason}\n"
        f"Post: {post_text}\n"
        "Make it personal, short, and professional."
    )
    try:
        thread = client.beta.threads.create()
        run = client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread_id=thread.id,
            messages=[{"role": "user", "content": prompt}]
        )
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        result = client.beta.threads.messages.list(thread_id=thread.id)
        return result.data[0].content[0].text.value
    except Exception as e:
        return f"[!] GPT message creation failed: {e}"