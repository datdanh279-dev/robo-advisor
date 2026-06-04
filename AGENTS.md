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

## Console noise (chỉ trên mạng công ty / ad-block)

Nếu DevTools → Console có các lỗi dưới đây, **KHÔNG phải bug app** — chỉ là network bị chặn:

- `cdn.segment.com/analytics.js` / `www.google-analytics.com/analytics.js` → đã được tắt bằng `[browser] gatherUsageStats = false` trong `.streamlit/config.toml`. Nếu vẫn còn, kiểm tra file `config.toml` đã push lên `main` chưa.
- `translate.google.com/gen204` / `translate.googleapis.com/element/log` → Chrome auto‑offer dịch vì page chưa khai báo ngôn ngữ. Đã fix bằng `<meta http-equiv="Content-Language" content="vi">` trong `app.py` (ngay sau `set_page_config`).
- `bufferedData-*.js:5 INITIAL -> (10, 0, ) -> ERROR` → state machine của Streamlit gửi Segment events fail do network block. Không ảnh hưởng render app.

## React removeChild bug (đã fix)

Nếu console có `NotFoundError: Failed to execute 'removeChild' on 'Node'` trong `routes-Bl4CT19H.js`:

- Nguyên nhân: CSS block lớn (`.main-header`, `.metric-box`, …) bị re‑emit mỗi `st.rerun()` → React reconciliation vỡ.
- Fix: tất cả `<style>` / `<link>` blocks được inject qua flag `session_state._main_css_injected` / `_login_css_injected`, đảm bảo **chỉ inject 1 lần / session**.
- Ngoài ra: bỏ `#root { ... }` selector (đụng React root), đổi `header[data-testid="stHeader"] { display: none; }` thành `visibility: hidden; height: 0` (giữ node trong DOM).
