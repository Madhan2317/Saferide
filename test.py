import streamlit as st
from ultralytics import YOLO
import torch, cv2, os, time, glob, json
import boto3, psycopg2
from dotenv import load_dotenv
import ollama

# Import utils
from accident_alert import send_accident_alert   # 🚨 Telegram alerts
from pdf_utils import generate_pdf_report        # 📄 PDF generator
from email_utils import send_email_with_pdf      # 📧 Email sender

# -------------------- ENV --------------------
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
DB_URL = os.getenv("DB_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "receiver@example.com")

# -------------------- AWS S3 --------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# -------------------- DB --------------------
def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            filename TEXT,
            s3_url TEXT,
            class_label VARCHAR(50),
            confidence REAL,
            bbox JSONB
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_metadata(filename, s3_url, class_label, confidence, bbox):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO detection_logs (filename, s3_url, class_label, confidence, bbox)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (filename, s3_url, class_label, confidence, json.dumps(bbox))
    )
    conn.commit()
    cur.close()
    conn.close()

# -------------------- UPLOAD TO S3 --------------------
def upload_to_s3(local_path, key, metadata_dict=None, content_type=None):
    """
    Upload file to S3 bucket for ACL-disabled public bucket.
    Bucket policy controls public access.
    """
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    # Upload main file
    s3.upload_file(local_path, S3_BUCKET, key, ExtraArgs=extra_args)

    url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

    # Upload metadata JSON
    if metadata_dict:
        meta_key = key.rsplit(".", 1)[0] + ".json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=meta_key,
            Body=json.dumps(metadata_dict),
            ContentType="application/json"
        )

    return url

# -------------------- YOLO MODEL --------------------
MODEL_PATH = "/home/ubuntu/Saferide/models/best.pt"
OUTPUT_DIR = "runs/streamlit_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
device = 0 if torch.cuda.is_available() else "cpu"
model = YOLO(MODEL_PATH)

# Init DB
init_db()

# -------------------- RAG Chatbot --------------------
def rag_chatbot(user_q):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, filename, class_label, confidence, s3_url
        FROM detection_logs
        WHERE class_label ILIKE '%helmet%' OR class_label ILIKE '%no helmet%'
        ORDER BY timestamp DESC LIMIT 50;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    context = "\n".join([
        f"{r[0]} | {r[2]} ({r[3]:.2f}) | {r[1]} | {r[4]}"
        for r in rows
    ]) if rows else "No helmet detection records found."

    prompt = f"""You are a safety assistant.
Answer ONLY based on the following helmet detection logs:

{context}

User Question: {user_q}
"""

    resp = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
    return resp['message']['content'], rows

# -------------------- STREAMLIT APP --------------------
st.set_page_config(page_title="SafeRide AI", layout="wide")
st.title("🚦 SafeRide AI — Helmet & Accident Detection + Chatbot")

mode = st.sidebar.radio("Choose Mode:", ["📂 Upload Image/Video", "🎥 Live Webcam", "💬 Chatbot"])

# -------------------- CHATBOT --------------------
if mode == "💬 Chatbot":
    st.subheader("🤖 Helmet Detection Chatbot")
    
    user_q = st.text_input("Ask me about helmet detections...")
    ask_btn = st.button("Ask")

    if ask_btn and user_q:
        with st.spinner("Thinking..."):
            answer, logs = rag_chatbot(user_q)
        st.success(answer)

    receiver_email = st.text_input("Enter receiver email:")

    if st.button("📤 Send PDF Report to Email"):
        if not receiver_email:
            st.error("❌ Please enter a valid email address first!")
        else:
            try:
                conn = psycopg2.connect(DB_URL)
                cur = conn.cursor()
                cur.execute("""
                    SELECT timestamp, filename, class_label, confidence, s3_url
                    FROM detection_logs
                    WHERE class_label ILIKE '%helmet%' OR class_label ILIKE '%no helmet%'
                    ORDER BY timestamp DESC LIMIT 50;
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    pdf_path = "helmet_report.pdf"
                    generate_pdf_report(rows, pdf_path)  

                    send_email_with_pdf(
                        subject="Helmet Detection Report",
                        body="Please find the attached helmet detection report.",
                        pdf_path=pdf_path,
                        receiver_email=receiver_email
                    )
                    st.success(f"✅ PDF report generated and emailed successfully to {receiver_email}!")
                else:
                    st.warning("⚠️ No helmet detection records found.")
            except Exception as e:
                st.error(f"❌ Failed to send PDF report: {e}")

# -------------------- UPLOAD MODE --------------------
elif mode == "📂 Upload Image/Video":
    uploaded_file = st.file_uploader("Upload an image or video", type=["jpg", "png", "mp4"])

    if uploaded_file:
        file_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("⏳ Running detection...")
        run_name = f"run_{int(time.time())}"

        results = model.predict(
            source=file_path,
            save=True,
            project=OUTPUT_DIR,
            name=run_name,
            device=device,
            conf=0.5
        )

        result_folder = os.path.join(OUTPUT_DIR, run_name)
        predicted_files = glob.glob(os.path.join(result_folder, "*"))
        predicted_files = [f for f in predicted_files if f.endswith((".jpg", ".png", ".mp4"))]

        if predicted_files:
            latest_file = max(predicted_files, key=os.path.getctime)
            s3_key = f"detections/{os.path.basename(latest_file)}"

            detections = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    label = model.names[cls_id]

                    detections.append({
                        "class": label,
                        "confidence": conf,
                        "bbox": xyxy
                    })

                    insert_metadata(os.path.basename(latest_file), f"s3://{S3_BUCKET}/{s3_key}", label, conf, xyxy)

            # Determine content type
            if latest_file.endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif latest_file.endswith(".png"):
                content_type = "image/png"
            else:
                content_type = "video/mp4"

            s3_url = upload_to_s3(latest_file, s3_key, {"detections": detections}, content_type=content_type)

            if uploaded_file.type.startswith("image"):
                st.image(latest_file, caption=f"Detection Result (S3: {s3_url})")
            else:
                st.video(latest_file)
                st.write(f"📂 S3 URL: {s3_url}")

            st.subheader("📊 Detections")
            for det in detections:
                st.write(f"Detected **{det['class']}** with {det['confidence']:.2f} at {det['bbox']}")

                if "accident" in det["class"].lower() and det["confidence"] > 0.5:
                    send_accident_alert(os.path.basename(latest_file), s3_url, "Accident Detected")
                    st.error("🚨 Accident detected! Telegram alert sent.")

# -------------------- LIVE WEBCAM MODE --------------------
elif mode == "🎥 Live Webcam":
    st.info("📸 Starting webcam...")

    cap = cv2.VideoCapture(0)
    stframe = st.empty()
    run_live = st.checkbox("▶️ Run Live Detection")

    while run_live:
        ret, frame = cap.read()
        if not ret:
            st.error("❌ Webcam not accessible")
            break

        results = model(frame)
        annotated_frame = results[0].plot()
        stframe.image(annotated_frame, channels="BGR", use_column_width=True)

        timestamp = int(time.time())
        temp_path = f"frame_{timestamp}.jpg"
        cv2.imwrite(temp_path, annotated_frame)

        s3_key = f"live/{timestamp}.jpg"
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                label = model.names[cls_id]

                detections.append({
                    "class": label,
                    "confidence": conf,
                    "bbox": xyxy
                })

                insert_metadata(os.path.basename(temp_path), f"s3://{S3_BUCKET}/{s3_key}", label, conf, xyxy)

        s3_url = upload_to_s3(temp_path, s3_key, {"detections": detections}, content_type="image/jpeg")

        for det in detections:
            if "accident" in det["class"].lower() and det["confidence"] > 0.6:
                send_accident_alert(os.path.basename(temp_path), s3_url, "Accident Detected")
                st.error("🚨 Accident detected! Telegram alert sent.")

    cap.release()

