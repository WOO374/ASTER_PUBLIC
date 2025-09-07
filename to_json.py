# to_json.py
import os, glob, pandas as pd
os.makedirs("data", exist_ok=True)
files = sorted(glob.glob("outputs/google_news_*.csv"))
if not files:
    raise SystemExit("No CSV found in outputs/")
df = pd.read_csv(files[-1])
keep = ["query","title","summary_1line","link","published_kst","source"]
for col in keep:
    if col not in df.columns: df[col] = ""
df = df[keep].fillna("")
# 빈 키워드 라벨링(드롭다운에 보이게)
df["query"] = df["query"].apply(lambda x: x.strip() if isinstance(x,str) else "").replace("", "(키워드없음)")
# 최신순 정렬
df["published_kst"] = pd.to_datetime(df["published_kst"], errors="coerce")
df = df.sort_values("published_kst", ascending=False, na_position="last")
df["published_kst"] = df["published_kst"].dt.strftime("%Y-%m-%d %H:%M:%S")
df.to_json("data/google_news_latest.json", orient="records", force_ascii=False)
print("Wrote data/google_news_latest.json")
