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

# --- skipping early pages here for brevity ---

# ---------------- PAGE 3: Score Articles ----------------
if page == "3. Score Articles with GPT":
    st.title("🧠 Score Articles for Relevance")
    assistant_id = st.text_input("GPT Assistant ID (e.g. HotelNewsScorer)")
    if st.button("Run Scoring on Articles"):
        results = []
        for article in st.session_state.get("articles", []):
            prompt = (
                f"Analyze the following hotel news article and classify which persona it is most relevant to:\n\n"
                f"{article['content']}\n\n"
                "Personas: Analyst, Steward, Maverick.\n"
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
