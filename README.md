# e-Tax Invoice System for GAC Thailand 🌐

ระบบออกใบเสร็จ/ใบกำกับภาษีอัตโนมัติ - Cloud Ready!

## 🚀 Quick Start (Local)

```bash
# Clone/_download and install
cd gac_etax
pip install -r requirements.txt

# Run
streamlit run app.py
```

## ☁️ Deploy to Streamlit Cloud

### Step 1: GitHub Setup
```bash
# Create GitHub repo and push code
git init
git add .
git commit -m "e-Tax System v1"
git remote add origin https://github.com/YOUR_USERNAME/gac-etax.git
git push -u origin main
```

### Step 2: Streamlit Cloud
1. ไปที่ https://share.streamlit.io
2. Login ด้วย GitHub
3. Click "New app"
4. เลือก Repository, Branch, Main file path: `app.py`
5. Click "Deploy!"

### Step 3: Add Secrets
หลัง Deploy แล้ว:
1. ไปที่ App > Settings > Secrets
2. ใส่:
```toml
BOT_CLIENT_ID = "your_client_id"
BOT_CLIENT_SECRET = "your_client_secret"
```

## 📋 Features

| Feature | Status |
|---------|--------|
| 📤 In-Memory CSV Upload | ✅ |
| 🎯 Interactive Tax Edit | ✅ |
| ⚠️ OCEAN FREIGHT VAT Input | ✅ |
| 📄 PDF Generation | ✅ |
| 📄 e-Tax XML (ISO 20022) | ✅ |
| 💾 SQLite Persistence | ✅ |
| 🔐 BOT API Connection | ✅ |
| 📊 Dashboard History | ✅ |

## 🎯 Tax Categories

- **กลุ่ม A - NON VAT (0%)**: บริการระหว่างประเทศ
- **กลุ่ม B - VAT 7%**: บริการในประเทศ  
- **กลุ่ม C - Partial VAT**: กำหนดเอง (เช่น OCEAN FREIGHT)

## 📁 Files

```
gac_etax/
├── app.py                    # Main Streamlit app
├── requirements.txt         # Python packages
├── .streamlit/
│   └── secrets.toml        # Secrets template
├── data/
│   └── etax.db            # SQLite database (auto-created)
└── README.md
```

## 🌐 Access

- **Local**: http://localhost:8501
- **Cloud**: https://your-app-name.streamlit.app

---

**Created**: 2026-03-10
**Author**: Chuvit (AI Assistant)
