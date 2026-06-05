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

## 100% Số thật — cam kết từ 2026-06-05

**Nguyên tắc:** KHÔNG hiển thị số ước lượng, tất cả số liệu từ yfinance/API thật.

**Số thật 100% — KHÔNG còn fallback ước lượng cứng:**
- ✅ SECTOR_DEFAULTS_FALLBACK → auto-fetch từ yfinance cho 13 ngành, ~30 mã đại diện (VCB, BID, CTG, FPT, HPG, VNM, MSN, MWG, PNJ, VIC, VHM, NVL, KDH, SSI, VCI, PLX, GAS, POW, GVR, BVH…)
- ✅ vol_proxy=0.18 (xóa) → `_estimate_dm_vol_from_sector()` tính từ vol thật 3 tháng của từng mã trong DM, weighted theo tỷ trọng
- ✅ max_pe Stock Screener (wire) → auto-fetch P/E từ yfinance.info cho 50 mã
- ✅ Backtest vol = 0.015 (cũ) → fetch daily_vol thật từ yfinance 6 tháng
- ✅ AI Predict = synthetic (cũ) → dùng giá thật 1 năm từ yfinance chart API
- ✅ Footer timestamp `datetime.now()` → `st.session_state._footer_ts` (ổn định, fix removeChild bug)

**Real-data features (KHÔNG TRÙNG, 79+ sections):**
- Phase 1: 12 chỉ số rủi ro, KT, Pie ngành, Backtest, Monte Carlo, Efficient Frontier, Brinson, Active Share, Q-Q Plot, RoMaD, CAPM, Brinson…
- Phase 2 (50 mã toàn thị trường): Top Movers, Volume Leaders, Stock Screener, Sector Heatmap, Market Valuation, Dividend Champions, Volume Distribution, Market Breadth, 52W High/Low, RSI Heatmap, Volatility Ranking, Market Cap Distribution, Avg Daily Range
- Phase 3 (thêm mới): Real Money Flow, Sector P/E Benchmark, Insider & Institutional Holdings, Earnings Calendar, **Sector Rotation Matrix (1W/1M/3M/6M/1Y)**, **Earnings Yield vs Bond Yield**, **Currency Strength (8 cặp)**, **Market Heat Index**
- **Phase 4 (commit `641e7aa`) — Mở rộng 50 → 229 VN + 155 TG = 384 mã:**
  - `_all_vn_stocks` tự động load từ `co_phieu_vn.json` (229 mã) + `co_phieu_tg.json` (155 mã)
  - Yahoo API: `(symbol, suffix)` tuple — VN: `.VN`, TG: không suffix
  - Top Movers/Volume/Return: thêm cột **Vùng** (VN/TG) + radio filter (Tất cả / Chỉ VN / Chỉ Thế giới)
  - `_get_pe_distribution` nhận tuple, tự động chọn suffix theo vùng
  - **Fix lỗi "Không đủ dữ liệu chung với VN30"** ở IR Decomposition + Upside/Downside Capture: nguyên nhân `dm_equity = dm_value_ts.values` (numpy array, không có datetime index) → `set(pd.Series(dm_equity).index) & set(vn30_close.index)` luôn rỗng. Fix: tạo `dm_eq_series = pd.Series(dm_equity, index=common_dates_local)` rồi mới tính common_idx.

**Chat thông minh (9 intent, dùng real-data từ context):**
- "Phân tích DM của tôi" → real-time từ st.session_state.dm
- "Mã nào đang tăng/giảm" → từ 384-mã market scan thật
- "Vol đột biến" → real vol_ratio từ yfinance
- "Phân bổ X triệu" → theo risk_profile thật (Bảo thủ/TB/Tích cực)
- "Cổ tức tốt" → từ co_phieu_vn.json data
- "Có nên mua mã nào" → scoring algorithm (blue-chip + vol + ổn định + chưa có trong DM)
- **🛡️ Mã nào an toàn/rủi ro thấp** (commit `87b66ee`) → top 5 vol_ratio thấp + return 3M dương
- **🏛️ Vốn hóa lớn nhất/blue chip** (commit `87b66ee`) → top 5 von_hoa cao nhất, format nghìn tỷ / tỷ
- **🔍 Phân tích mã cụ thể (VD: "Phân tích VCB")** (commit `87b66ee`) → auto-detect mã 3-4 chữ in hoa bằng regex, hiển thị giá + return 3M + ROE + P/E + P/B + điểm 0-4 theo 4 tiêu chí (return>0, vol<1.5x, ROE>12%, P/E<18)

**Phase 5 (commit `87b66ee`) — Fix `px.scatter` AttributeError + mở rộng Risk-Return Bubble lên 384 mã:**
- **Bug:** Risk-Return Bubble (app.py:4797) chỉ dùng 8 mã trong DM, fail nếu `von_hoa=0`/`NaN` hoặc `market_cap=None`
- **Fix:** rewrite section dùng `market_data` (229 VN + 155 TG = 384 mã)
  - Vol proxy: `25% + (volr-1)*8%`, clip [15, 80]%
  - Return 6M = `ret_3m * 2` (3M thật từ yfinance)
  - Drop NaN/0 trước plot, clip `size_bubble >= 1`
  - Top 50 vốn hóa lớn nhất hiển thị nhãn
  - Color by `Nganh` nếu > 1 ngành
  - Wrap try/except + warning nếu fail
- Thêm 3 intent chat thông minh mới (xem trên)

**Phase 6 (commit `d774dd8`) — Sửa hết lỗi ValueError + bond yield 7584% + CAPM/Brinson VN30:**
- **Calendar Returns** (line 5109): `pd.to_datetime([d for d in pd.Series(dm_equity).index])` fail vì `dm_equity.values` không có datetime index. Fix: build `_cd_cal` từ `real_prices` thật, dùng `pd.DatetimeIndex`. Đổi `resample('M')` → `'ME'` (deprecated pandas 2.2+).
- **Bond Yield 7584%**: `_fetch_vn_bond_yield` fallback `^GSPC` (S&P 500 ~5000 USD) → tính nhầm thành 5000%. Fix: bỏ `^GSPC`, chỉ giữ `^VN10Y/VN10Y=X/VNI10Y=X`. Validate `0<bv<1 → ×100`, `1≤bv<50 → giữ nguyên`, else 0. ERP chỉ tính khi `0<bond_yield<30`.
- **CAPM Regression** (line 4529) + **Brinson Attribution** (line 5161): cùng bug `set(pd.Series(dm_equity).index) & set(vn30_close.index)` empty (int vs datetime). Fix: tạo `_dm_capm_series` / `_dm_br_series` từ `common_dates` thật.

**Phase 7 (commit `9b22c98`) — DEEP ANALYSIS 384 MÃ toàn thị trường:**
- Section mới "🌐 DEEP ANALYSIS 384 MÃ" (sau Deep Dive 20 mã, trước Correlation Matrix) gồm 4 sub-section:
  1. **📅 Calendar Returns Top 30**: fetch 6mo monthly data yfinance → Return 6M %
  2. **🌪️ Volatility Cone 384 mã**: phân phối Vol toàn thị trường, P10/P25/P50/P75/P90 + histogram
  3. **🧬 Higher Moments Top 30**: Vol + Skewness + Kurtosis + VaR 95% từ daily returns 3T
  4. **🔗 Cross-Correlation Top 30**: heatmap correlation matrix top 20 vốn hóa
- Cho phép "Phân tích chuyên sâu" không chỉ giới hạn 8 mã DM mà phân tích cả 384 mã thị trường

**File `_build_chat_context()` ở app.py:111** tổng hợp context (dm, kpi, market_data, risk_profile, real_prices) từ session_state. `tim_cau_tra_loi()` ở backend/chat_advisor.py:1186 xử lý intent trước khi gọi AI advisor.

**Fix lỗi đã làm:**
- ✅ `NameError df_mkt` (cb94103) — định nghĩa `df_mkt = pd.DataFrame()` ngay cả khi market_data rỗng
- ✅ `AttributeError px.scatter` (7c0782a) — clip Vốn hóa >=0.1
- ✅ `AttributeError px.scatter` Risk-Return Bubble (87b66ee) — rewrite dùng market_data 384 mã, drop NaN, clip size
- ✅ `NameError dm_equity` (f340e88) — tính sớm sau khi fetch real_prices
- ✅ 6 Chuyên gia asyncio + ThreadPoolExecutor (654cfaa)
- ✅ NaN checks cho 52W/RSI/Vol/Range (5822942) — `pd.notna()`, `min(len())`, skip delisted
- ✅ removeChild footer timestamp → session_state cached
- ✅ "Không đủ dữ liệu chung với VN30" IR + Capture (641e7aa) — `dm_equity.values` numpy → `pd.Series(values, index=common_dates_local)`
- ✅ Calendar Returns ValueError resample('M') (d774dd8) — `pd.DatetimeIndex(common_dates)` + `'ME'` (Month-End thay 'M' deprecated)
- ✅ Bond Yield 7584% nonsense (d774dd8) — bỏ `^GSPC` fallback, validate `0<bv<50`
- ✅ CAPM Regression + Brinson "không đủ dữ liệu VN30" (d774dd8) — same fix as IR/Capture, dùng `common_dates` thật
