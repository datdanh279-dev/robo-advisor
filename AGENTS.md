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

- `runtime.txt` = `python-3.11` (KHÔNG đổi sang 3.13/3.14, sẽ vỡ wheel)
- `requirements.txt` để `streamlit>=1.40,<2` (KHÔNG pin cứng 1.58.0)
- `.streamlit/config.toml` KHÔNG để `address = "0.0.0.0"` (Cloud sẽ tự bind)
- Push lên `main` → Streamlit Cloud auto-redeploy ~1–3 phút.
