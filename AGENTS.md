# Web chính thức (deploy - DÙNG DUY NHẤT URL NÀY)

**LUÔN DÙNG:** https://robo-advisor-jkp9byppflcdsrgapbm4vd.streamlit.app/
**KHÔNG** dùng localhost, **KHÔNG** mở web khác. Mọi hướng dẫn/test phải trỏ về URL này.

> User chỉ dùng web deploy, không cài local. Sau khi push lên `main`, đợi 1-3 phút rồi F5 web.

## Chạy local (CHỈ khi user yêu cầu debug trực tiếp)

```powershell
cd C:\Users\ACER\robo-advisor
python -m streamlit run app.py
```

Local: http://localhost:8501

### Nếu app chết

1. Kill python cũ:
```powershell
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
```
2. Chạy lại:
```powershell
python -m streamlit run app.py
```

### Sau khi code thay đổi (local)

F5 refresh browser là đủ, Streamlit tự reload.

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

## Vàng SJC giá sai (đã fix)

Triệu chứng: tab Quốc tế hiển thị Vàng SJC ~145 triệu VND/lượng thay vì ~86 triệu.

- Nguyên nhân (`backend/api_fetcher.py:80`): regex `<ratiotype="sell"…>` thiếu space giữa `ratio` và `type` → không match XML element thật `<ratio type="sell">` → luôn rơi vào nhánh fallback `int(xau * usd_vnd * 1.205 * 1.03)`.
- Fix: đổi regex thành `<ratio\s+type="sell"…>` để match đúng cấu trúc XML từ `https://sjc.com.vn/xml/tygiavang.xml`.
- Verify sau khi deploy: tab Quốc tế → Vàng SJC phải ~86.000.000 VND/lượng (giá SJC thật, không phải world gold * tỷ giá * 1.03).

## Lưu ý khi đọc báo cáo từ AI khác

Khi nhận được phân tích lỗi từ AI khác, **LUÔN verify trước khi sửa**:

- Mỗi chuỗi kỳ lạ ("103,710", "16.8%", "lặp 4 lần", …) phải tìm được trong code thật bằng `grep`/`rg` trước khi fix.
- Ví dụ đã gặp: AI phân tích bảo "tổng lãi/lỗ 103,710₫ return 16.8%" nhưng `grep` toàn project → **0 match**. Số thật là 10.230.000₫ từ `tinh_return_danh_muc` ở `backend/danh_muc_metrics.py:4`.
- Ví dụ đã gặp: AI bảo "Hội đồng 6 Chuyên gia" lặp 4 lần nhưng `grep "Hội đồng 6"` → **đúng 1 match** ở `app.py:1876`. 6 expert chips riêng là render riêng, không chứa title.
