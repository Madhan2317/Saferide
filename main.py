import streamlit as st
from ultralytics import YOLO
import torch
import os
import time
import glob

# ✅ Path to trained model
MODEL_PATH = r"D:\MDTE21\FINAL PROJECT\runs\train\helmet_accident_yolov8\weights\best.pt"

# ✅ Output directory
OUTPUT_DIR = "runs/streamlit_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ✅ Load model
device = 0 if torch.cuda.is_available() else "cpu"
model = YOLO(MODEL_PATH)

# ✅ Streamlit UI
st.set_page_config(page_title="SafeRide AI", layout="wide")
st.title("🚦 SafeRide AI — Helmet & Accident Detection")

# Upload file
uploaded_file = st.file_uploader("Upload an image or video", type=["jpg", "png", "mp4"])

if uploaded_file:
    # Save uploaded file temporarily
    file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info("⏳ Running detection... Please wait.")

    # Unique run name
    run_name = f"run_{int(time.time())}"

    # Run inference
    results = model.predict(
        source=file_path,
        save=True,
        project=OUTPUT_DIR,
        name=run_name,
        device=device,
        conf=0.5
    )

    # Find YOLO output file
    result_folder = os.path.join(OUTPUT_DIR, run_name)
    predicted_files = glob.glob(os.path.join(result_folder, "*"))
    predicted_files = [f for f in predicted_files if f.endswith((".jpg", ".png", ".mp4"))]

    if predicted_files:
        latest_file = max(predicted_files, key=os.path.getctime)
        if uploaded_file.type.startswith("image"):
            st.image(latest_file, caption="Detection Result")
        else:
            st.video(latest_file)
    else:
        st.error("⚠️ No YOLO output file found!")

    # Detection summary
    st.subheader("📊 Detection Results")
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            st.write(f"Detected **{model.names[cls_id]}** with {conf:.2f} confidence at {xyxy}")
