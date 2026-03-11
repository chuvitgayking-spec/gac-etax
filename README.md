# E-Tax Invoice System for GAC Thailand

ระบบออกใบกำกับภาษีอิเล็กทรอนิกส์ (e-Tax Invoice) สำหรับ GAC Thailand
สอดคล้องกับมาตรฐาน ขมธ. 3-2560 ของกรมสรรพากรไทย

## 📋 Features

- ✅ **Streamlit UI** - สวยงาม ใช้งานง่าย
- ✅ **XML Generation** - สร้างไฟล์ XML ตามมาตรฐาน CII (ขมธ. 3-2560)
- ✅ **Environment Config** - ตั้งค่าผ่าน .env file
- ✅ **Docker Deployment** - Deploy ด้วย Docker
- ✅ **Modular Architecture** - แยกโมดูลชัดเจน
- ✅ **Logging System** - บันทึก log พร้อม rotation
- ✅ **Error Handling** - จัดการ error อย่างเป็นระบบ
- ✅ **Digital Signature Ready** - รองรับการเซ็นดิจิทัล (optional)

## 🚀 Quick Start

### 1. Clone และ Install

```bash
git clone https://github.com/chuvitgayking-spec/gac-etax.git
cd gac-etax
pip install -r requirements.txt
```

### 2. Configure

```bash
cp config/.env.example .env
# แก้ไข .env ตามข้อมูลบริษัท
nano .env
```

### 3. Run

```bash
streamlit run app.py
```

เปิด browser ไปที่: http://localhost:8501

## 🐳 Docker Deployment

### Development

```bash
cd docker
docker-compose up -d
```

### Production

```bash
# Build image
docker build -t gac-etax:latest .

# Run
docker run -d \
  --name gac-etax \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  gac-etax:latest
```

## 📁 Project Structure

```
gac-etax/
├── app.py                     # Main Streamlit application
├── config/
│   ├── __init__.py           # Configuration loader
│   └── .env.example         # Environment template
├── tools/
│   ├── xml_generator.py      # E-Tax XML Generator
│   └── core.py               # Core functions
├── utils/
│   ├── logging_config.py     # Logging setup
│   └── error_handling.py    # Error handling
├── docker/
│   ├── Dockerfile           # Docker image
│   └── docker-compose.yml   # Docker Compose
├── tests/                    # Unit tests
├── logs/                     # Log files
├── data/                     # Database files
└── requirements.txt          # Python dependencies
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PATH` | Path to SQLite database | `./data/invoices.db` |
| `COMPANY_NAME` | Company name | GAC Thailand |
| `COMPANY_TAX_ID` | Tax ID (13 digits) | 0105535169497 |
| `COMPANY_ADDRESS` | Company address | - |
| `COMPANY_TEL` | Phone number | - |
| `COMPANY_EMAIL` | Email | - |
| `DEFAULT_VAT_RATE` | VAT rate | 0.07 (7%) |
| `RD_API_URL` | Revenue Dept API | - |
| `SMTP_*` | Email settings | - |
| `LOG_LEVEL` | Logging level | INFO |

## 📊 Usage

### Upload Invoice

1. ไปที่หน้า **Upload Invoice**
2. Upload ไฟล์ XML/CSV ข้อมูล invoice
3. ตรวจสอบข้อมูล
4. กด **บันทึก**

### Generate e-Tax XML

1. เลือก invoice ที่ต้องการ
2. กด **Generate e-Tax XML**
3. ระบบจะสร้าง XML ตามมาตรธาน ขมธ. 3-2560

### Issue Receipt

1. ไปที่หน้า **ออกใบเสร็จ**
2. เลือก invoice
3. กรอกข้อมูลเพิ่มเติม
4. Generate PDF receipt

## 🔐 Digital Signature (Optional)

เพื่อใช้งาน digital signature:

1. ตั้งค่า `HSM_ENABLED=true` ใน .env
2. ระบุ path ของ private key และ certificate
3. ระบบจะ sign XML ก่อนส่งให้กรมสรรพากร

## 📝 E-Tax XML Schema

ระบบสร้าง XML ตามมาตรฐาน:

- **Format:** CII (Cross Industry Invoice)
- **Standard:** ขมธ. 3-2560
- **Document Type:** 380 (Tax Invoice)
- **Namespace:** 
  - rsm: urn:un:unece:uncefact:data:standard:InvoiceType
  - ram: urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntityType

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific module
python -m pytest tests/test_xml_generator.py -v
```

## 📄 License

MIT License

## 👨‍💻 Author

GAC Thailand IT Team

---

**หมายเหตุ:** ระบบนี้เป็นเครื่องมือช่วยสร้าง e-Tax Invoice ตามมาตรฐาน ขมธ. 3-2560 ควรตรวจสอบความถูกต้องของข้อมูลก่อนส่งให้กรมสรรพากรเสมอ
