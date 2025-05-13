import imaplib
import email
from bs4 import BeautifulSoup

def connect_to_gmail(username, password):
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(username, password)
    return imap

def fetch_emails(imap, senders, max_results=10):
    imap.select("inbox")
    results = []
    for sender in senders.split(","):
        status, messages = imap.search(None, f'FROM "{sender.strip()}"')
        if status != "OK":
            continue
        email_ids = messages[0].split()[-max_results:]
        for eid in reversed(email_ids):
            res, msg_data = imap.fetch(eid, "(RFC822)")
            if res != "OK":
                continue
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            content = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        content = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                content = msg.get_payload(decode=True).decode(errors="ignore")
            soup = BeautifulSoup(content, "html.parser")
            links = list(set(a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("http")))
            text = soup.get_text()
            results.append({
                "subject": msg["subject"],
                "from": msg["from"],
                "links": links,
                "text": text[:1000]
            })
    return results