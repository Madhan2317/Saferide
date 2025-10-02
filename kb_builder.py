import os, json, psycopg2, faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")
EMB_MODEL = "all-MiniLM-L6-v2"
INDEX_PATH = "kb_index.faiss"
META_PATH = "kb_metadata.json"

model = SentenceTransformer(EMB_MODEL)

def fetch_detections():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, timestamp::text, filename, s3_url, class_label, confidence
        FROM detection_logs
        WHERE lower(class_label) IN ('helmet', 'no_helmet', 'no-helmet')
        ORDER BY timestamp DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def build_docs(rows):
    docs, metas = [], []
    for r in rows:
        id_, ts, filename, s3_url, label, conf = r
        text = f"{ts} - {label} with confidence {conf:.2f} in {filename}"
        docs.append(text)
        metas.append({
            "id": id_, "timestamp": ts, "filename": filename,
            "s3_url": s3_url, "class_label": label, "confidence": float(conf)
        })
    return docs, metas

def build_index(docs):
    embeddings = model.encode(docs, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

if __name__ == "__main__":
    rows = fetch_detections()
    docs, metas = build_docs(rows)
    index = build_index(docs)
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(metas, f, indent=2)
    print(f"✅ KB built with {len(docs)} records")
