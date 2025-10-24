# 🚦 SafeRide AI — Intelligent Helmet & Accident Detection System  

> An AI-powered safety monitoring system that detects **helmet usage** and **accidents** in real-time from images, videos, or live webcam feeds.  
> Built with **YOLOv8**, **Streamlit**, and **Ollama (LLaMA 3.1)** — it also integrates **AWS S3**, **PostgreSQL**, and **automated Telegram/email alerts**.

---

## 🧠 Overview  

**SafeRide AI** ensures rider safety by detecting whether helmets are worn and identifying accidents from CCTV or uploaded media.  
It automatically:  
- Logs detections to PostgreSQL  
- Uploads results and metadata to AWS S3  
- Generates PDF reports  
- Sends real-time alerts through Telegram and Email  
- Supports a **Chatbot Assistant** powered by **LLaMA 3.1** for intelligent safety insights  

---

## 🚀 Features  

✅ **Helmet & Accident Detection** (YOLOv8-based)  
✅ **Streamlit Web Interface** (Upload / Webcam / Chatbot modes)  
✅ **AWS S3 Integration** for evidence storage  
✅ **PostgreSQL Logging** of detections  
✅ **PDF Report Generation** & Email Sending  
✅ **Telegram Alerts** for critical events  
✅ **LLaMA 3.1 Chatbot** for querying detection history  
✅ **Fully Deployable on AWS EC2 (Free Tier Compatible)**  

---

## 🏗️ Tech Stack  

| Component | Technology |
|------------|-------------|
| Frontend | Streamlit |
| Model | YOLOv8 (Ultralytics) |
| Chatbot | Ollama (LLaMA 3.1:8B) |
| Database | PostgreSQL |
| Storage | AWS S3 |
| Backend | Python (Boto3, Psycopg2, dotenv) |
| Alerts | Telegram Bot + Email |
| Deployment | AWS EC2 (Ubuntu) |

---

## 📦 Installation  

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/Saferide.git
cd Saferide

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
