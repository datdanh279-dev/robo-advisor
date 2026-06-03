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
