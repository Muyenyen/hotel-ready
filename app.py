import streamlit as st
from email_reader import connect_to_gmail, fetch_emails
from article_scraper import scrape_article
from linkedin_monitor import start_browser_with_cookie, scrape_engagement
from openai_helpers import run_lead_qualifier, run_outreach_crafter
from airtable_helpers import save_lead_to_airtable
import time

st.set_page_config(page_title="Hotel Investment Lead Generator", layout="wide")
st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", [
    "1. Read Gmail + Extract Links",
    "2. Scrape Articles from Links",
    "3. Score Articles with GPT",
    "4. Generate LinkedIn Posts",
    "5. Scrape LinkedIn Engagement",
    "6. Score Leads",
    "7. Generate Outreach + Save"
])

# ---------------- PAGE 1: Gmail Reader ----------------
if page == "1. Read Gmail + Extract Links":
    st.title("📨 Read Gmail for Hotel News")
    username = st.text_input("Gmail address", st.secrets.get("SMTP_EMAIL", ""))
    password = st.text_input("App Password", st.secrets.get("SMTP_PASSWORD", ""), type="password")
    senders = st.text_input("Sender Filters (comma-separated)", st.secrets.get("NEWS_SENDERS", ""))
    max_results = st.slider("How many recent emails to check?", 1, 20, 5)

    if st.button("Fetch Emails"):
        imap = connect_to_gmail(username, password)
        emails = fetch_emails(imap, senders, max_results=max_results)
        st.session_state["emails"] = emails
        st.success(f"✅ Fetched {len(emails)} emails.")
        for e in emails:
            st.markdown("**" + e['subject'] + "**")
            st.markdown("🔗 Links:")
            for link in e["links"]:
                st.markdown(f"- [{link}]({link})")
            st.divider()

# ---------------- PAGE 2: Article Scraper ----------------
elif page == "2. Scrape Articles from Links":
    st.title("🔎 Scrape Article Text from Links")
    links = []
    for email_data in st.session_state.get("emails", []):
        links.extend(email_data["links"])
    links = list(set(links))
    if not links:
        st.warning("No links found. Please extract from Gmail first.")
    else:
        selected_links = st.multiselect("Select links to scrape:", links)
        articles = []
        for url in selected_links:
            with st.spinner(f"Scraping {url}..."):
                content = scrape_article(url)
                if content:
                    st.session_state.setdefault("articles", []).append({
                        "url": url, "content": content
                    })
                    st.text_area(f"Scraped from: {url}", content[:1500], height=200)

# ---------------- PAGE 3: Score Articles ----------------
elif page == "3. Score Articles with GPT":
    st.title("🧠 Score Articles for Relevance")
    assistant_id = st.text_input("GPT Assistant ID (e.g. HotelNewsScorer)")
    if st.button("Run Scoring on Articles"):
        results = []
        for article in st.session_state.get("articles", []):
            prompt = (
                f"Analyze the following hotel news article and classify which persona it is most relevant to:

"
                f"{article['content']}

"
                "Personas: Analyst, Steward, Maverick.
"
                "Respond with: Persona + short reason."
            )
            try:
                from openai import OpenAI
                client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "sk-REPLACE_WITH_YOUR_REAL_KEY"))
                thread = client.beta.threads.create()
                run = client.beta.threads.create_and_run(
                    assistant_id=assistant_id,
                    thread_id=thread.id,
                    messages=[{"role": "user", "content": prompt}]
                )
                while run.status not in ["completed", "failed"]:
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                result = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
                article["score"] = result
                st.markdown(f"**{article['url']}**")
                st.code(result)
                results.append(article)
            except Exception as e:
                st.error(f"Error scoring article: {e}")
        st.session_state["scored_articles"] = results

# ---------------- PAGE 4: LinkedIn Posts ----------------
elif page == "4. Generate LinkedIn Posts":
    st.title("✍️ Create LinkedIn Posts from Scored Articles")
    scored = st.session_state.get("scored_articles", [])
    if not scored:
        st.warning("No scored articles found.")
    else:
        for article in scored:
            prompt = (
                f"Based on this hotel investment news article:

{article['content']}

"
                f"And the fact that it is most relevant to this persona:
{article['score']}

"
                "Write a concise, engaging LinkedIn post in Will Huston's voice."
            )
            try:
                from openai import OpenAI
                client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "sk-REPLACE_WITH_YOUR_REAL_KEY"))
                thread = client.beta.threads.create()
                run = client.beta.threads.create_and_run(
                    assistant_id=st.text_input("Post Assistant ID", key=article["url"]),
                    thread_id=thread.id,
                    messages=[{"role": "user", "content": prompt}]
                )
                while run.status not in ["completed", "failed"]:
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                result = client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value
                st.text_area(f"LinkedIn Post for: {article['url']}", result, height=200)
            except Exception as e:
                st.error(f"Error generating post: {e}")

# ---------------- PAGE 5+: LinkedIn Flow ----------------
elif page == "5. Scrape LinkedIn Engagement":
    st.title("🔗 Scrape LinkedIn Post Engagement")
    post_url = st.text_input("Enter LinkedIn Post URL", "")
    li_cookie = st.secrets.get("LINKEDIN_SESSION", "")
    if st.button("Scrape Engagement"):
        driver = start_browser_with_cookie(li_cookie)
        data = scrape_engagement(driver, post_url)
        st.session_state["engagers"] = data["top_engagers"]
        st.success(f"✅ Scraped {len(data['top_engagers'])} engagers.")
        st.write(data)

elif page == "6. Score Leads":
    st.title("🎯 Score Engagers with GPT")
    engagers = st.session_state.get("engagers", [])
    assistant_id = st.text_input("LeadQualifier Assistant ID")
    category = st.selectbox("Post Category", ["M&A", "Development", "Trends"])
    if st.button("Run Scoring"):
        scored = []
        for user in engagers:
            with st.spinner(f"Scoring {user['name']}..."):
                result = run_lead_qualifier(assistant_id, user['name'], user['profile_url'], category)
                st.markdown(f"**{user['name']}**")
                st.code(result, language="markdown")
                scored.append((user, result))
        st.session_state["scored_leads"] = scored

elif page == "7. Generate Outreach + Save":
    st.title("✉️ Generate Outreach Messages")
    leads = st.session_state.get("scored_leads", [])
    outreach_id = st.text_input("OutreachCrafter Assistant ID")
    post_text = st.text_area("Paste the LinkedIn Post Text for context")
    if st.button("Generate Messages and Save to Airtable"):
        for user, score_output in leads:
            name = user["name"]
            url = user["profile_url"]
            lines = score_output.split("\n")
            category = next((l.split(":")[1].strip() for l in lines if l.lower().startswith("category")), "General")
            score = int(next((l.split(":")[1].strip() for l in lines if "score" in l.lower()), "5"))
            reason = next((l for l in lines if "reason" in l.lower()), "")
            with st.spinner(f"Generating message for {name}..."):
                msg = run_outreach_crafter(outreach_id, name, url, category, reason, post_text)
                st.text_area(f"To {name}", msg, height=100)
                record = {
                    "name": name,
                    "profile_url": url,
                    "category": category,
                    "score": score,
                    "reason": reason,
                    "message": msg,
                    "post_category": category,
                    "post_text": post_text
                }
                try:
                    save_lead_to_airtable(record)
                    st.success(f"Saved {name} to Airtable")
                except Exception as e:
                    st.error(f"Failed to save {name}: {e}")