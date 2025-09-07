# google_news_rss.py
import os, time, json, html, re, requests, feedparser, pandas as pd
from datetime import datetime, timezone
from dateutil import tz

OUT_DIR = "outputs"
DEFAULT_QUERIES = json.loads(os.getenv("QUERIES_JSON","[\"생성형 AI\",\"RAG\",\"파인튜닝\",\"멀티모달\",\"오픈소스 LLM\"]"))

def clean(s): 
    if not s: return ""
    s = html.unescape(s)
    return re.sub("<[^>]+>", "", s).strip()

def one_liner(t, d):
    t, d = (t or "").strip(), (d or "").strip()
    if not t and not d: return ""
    if t and d:
        d = d.replace(t, "").strip()
        return f"{t} — {d[:80]}".strip(" —")
    return t or d

def to_kst(dt_struct):
    if not dt_struct: return ""
    utc_dt = datetime(*dt_struct[:6], tzinfo=timezone.utc)
    return utc_dt.astimezone(tz.gettz("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

def build_url(q, lang="ko", region="KR"):
    q = requests.utils.quote(q, safe="")
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang}"

def fetch_one(q):
    url = build_url(q)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    feed = feedparser.parse(r.content)
    rows = []
    for e in feed.entries:
        title = clean(getattr(e,"title",""))
        summary = clean(getattr(e,"summary",""))
        rows.append({
            "query": q,
            "title": title,
            "summary": summary,
            "summary_1line": one_liner(title, summary),
            "link": getattr(e,"link",""),
            "published_kst": to_kst(getattr(e,"published_parsed",None)),
            "source": getattr(getattr(e,"source",{}),"title",""),
        })
    return rows

def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_rows = []
    for q in DEFAULT_QUERIES:
        print(f"[INFO] {q}")
        all_rows += fetch_one(q)
        time.sleep(0.8)
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["link"])
    df["__null"] = df["published_kst"].eq("") | df["published_kst"].isna()
    df = df.sort_values(by=["__null","published_kst"], ascending=[True,False]).drop(columns="__null")
    ts = datetime.now(tz.gettz("Asia/Seoul")).strftime("%Y-%m-%d_%H%M%S")
    out = f"{OUT_DIR}/google_news_{ts}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print("[DONE]", out)
    return out

if __name__ == "__main__":
    run()
