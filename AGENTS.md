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

## Console noise (KHÔNG THỂ sửa triệt để từ app)

**Bản chất vấn đề**: Streamlit Cloud **hardcode** Segment analytics (`cdn.segment.com/analytics.js/v1/GI7vYWHNmWwHbyFjBrvL0jOBA1TpZOXC/analytics.min.js`) vào mọi app thông qua host page JS, kể cả khi `[browser] gatherUsageStats = false`. Trên mạng công ty (có firewall/proxy chặn external services), browser tải Segment script sẽ fail với `ERR_BLOCKED_BY_ADMINISTRATOR`.

**Đã làm** (không thể fix gốc, chỉ giảm noise):
- `[browser] gatherUsageStats = false` trong `.streamlit/config.toml` (giảm event gửi đi).
- `<script>` set `document.documentElement.lang='vi'` + thêm `<meta Content-Language>` trong head.
- Console filter override `console.error` / `console.warn` / `console.log` chặn 12 pattern (segment, GA, translate, bufferedData, routes-*.js, removeChild, NotFoundError, …).
- `fetch` + `XMLHttpRequest` override chặn request mới.
- `console.clear()` chạy đầu + `setInterval(console.clear, 2000)` xóa log cũ.

**Cách chắc chắn 100% ẩn lỗi khỏi console**:
1. Mở DevTools (F12) → tab Console.
2. Click vào ô **Filter** (có icon phễu ∇, phía trên danh sách log).
3. Gõ: `-ERR_BLOCKED` rồi Enter.
4. Hoặc filter mạnh hơn: `-ERR_BLOCKED -bufferedData -translate -segment -analytics`

**Cách giải quyết tận gốc** (ngoài phạm vi app):
- Dùng mạng khác (4G/5G, wifi nhà) không chặn segment.com/google.com.
- Hoặc nhờ IT công ty whitelist `cdn.segment.com`, `www.google-analytics.com`, `translate.google.com`.

## React removeChild bug (đã fix)

Nếu console có `NotFoundError: Failed to execute 'removeChild' on 'Node'` trong `routes-Bl4CT19H.js`:

- Nguyên nhân: CSS block lớn (`.main-header`, `.metric-box`, …) bị re‑emit mỗi `st.rerun()` → React reconciliation vỡ.
- Fix: tất cả `<style>` / `<link>` blocks được inject qua flag `session_state._main_css_injected` / `_login_css_injected`, đảm bảo **chỉ inject 1 lần / session**.
- Ngoài ra: bỏ `#root { ... }` selector (đụng React root), đổi `header[data-testid="stHeader"] { display: none; }` thành `visibility: hidden; height: 0` (giữ node trong DOM).
