# Chạy app

```powershell
cd C:\Users\ACER\robo-advisor
python -m streamlit run app.py
```

App chạy tại http://localhost:8501

## Nếu app chết

1. Kill hết python cũ:
```powershell
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
```
2. Chạy lại:
```powershell
python -m streamlit run app.py
```

## Sau khi code thay đổi

Chỉ cần F5 refresh browser là đủ, Streamlit tự reload.

## Web chính thức (deploy)

Luôn dùng web này, KHÔNG dùng localhost:
https://robo-advisor-jkp9byppflcdsrgapbm4vd.streamlit.app/

## Deploy lên Streamlit Cloud

- **QUAN TRỌNG**: Streamlit Cloud **không đọc** `runtime.txt` / `.python-version` — phải vào **Advanced settings** trên dashboard để chọn Python version.
- Cloud hiện default **Python 3.14.x**, nên `requirements.txt` phải pin **minimum** đủ mới để có wheel 3.14:
  - `pandas>=2.2`, `numpy>=2.0`, `scipy>=1.13`, `scikit-learn>=1.4`
  - `aiohttp>=3.10`, `lxml>=5.0`, `yfinance>=0.2` (KHÔNG đặt `<1`, sẽ vỡ trên 3.14)
  - `streamlit>=1.50,<2`
- `.streamlit/config.toml` KHÔNG để `address = "0.0.0.0"` (Cloud sẽ tự bind).
- Push lên `main` → Streamlit Cloud auto‑redeploy ~1–3 phút.
