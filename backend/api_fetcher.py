import requests, re, json, os, sys, io, contextlib, logging, time, random
from datetime import datetime, time as dt_time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# User-Agent rotation để tránh bị Yahoo chặn IP trên shared hosting
_YF_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]
_YF_SESSION = None

def _yf_session():
    global _YF_SESSION
    if _YF_SESSION is None:
        _YF_SESSION = requests.Session()
        _YF_SESSION.headers.update({"User-Agent": random.choice(_YF_USER_AGENTS)})
    return _YF_SESSION

def _yf_retry(ma, period="1y", retries=3, delay=2):
    """Wrapper cho yfinance với retry + User-Agent rotation, tránh IP ban"""
    import yfinance as yf
    for attempt in range(retries):
        try:
            session = _yf_session()
            ticker = yf.Ticker(ma, session=session)
            with contextlib.redirect_stderr(io.StringIO()):
                hist = ticker.history(period=period)
            if not hist.empty:
                return hist
        except Exception as e:
            logger.debug(f"yfinance {ma} attempt {attempt+1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
                # Refresh session + user-agent cho lần retry
                _YF_SESSION = None
    return None

CACHE = {}
CACHE_TTL = {}
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL", "300"))

# Giờ giao dịch VN: 9:00 - 15:00, Thứ 2 - Thứ 6
_TRADING_START = dt_time(9, 0)
_TRADING_END = dt_time(15, 0)

def dang_trong_gio_giao_dich_vn():
    """Kiểm tra có đang trong giờ giao dịch chứng khoán VN không"""
    now = datetime.now()
    if now.weekday() >= 5:  # Thứ 7 (5), CN (6)
        return False
    return _TRADING_START <= now.time() <= _TRADING_END

def gia_dong_cua_gan_nhat(ma, default=None):
    """Lấy giá đóng cửa gần nhất (có thể là phiên trước), có retry"""
    hist = _yf_retry(ma, "5d", retries=2, delay=1)
    if hist is not None and not hist.empty:
        return float(hist['Close'].iloc[-1])
    return default

def _cache_get(key):
    if key in CACHE_TTL and (datetime.now() - CACHE_TTL[key]).seconds < CACHE_TTL_SECONDS:
        return CACHE.get(key)
    return None

def _cache_set(key, value):
    CACHE[key] = value
    CACHE_TTL[key] = datetime.now()
    return value

def lay_gia_vang_sjc():
    cached = _cache_get("vang_sjc")
    if cached: return cached
    try:
        r = requests.get("https://sjc.com.vn/xml/tygiavang.xml", timeout=10)
        r.encoding = 'utf-8'
        match = re.search(r'<ratiotype="sell"[^>]*>([\d,]+)</ratio>', r.text)
        if match:
            return _cache_set("vang_sjc", int(match.group(1).replace(',', '')))
    except Exception as e:
        logger.warning("lay_gia_vang_sjc failed: %s", e)
    # fallback: giá vàng SJC từ API thế giới * tỷ giá
    xau = lay_gia_vang_the_gioi()
    usd_vnd = lay_ty_gia_usd_vnd()
    if xau and usd_vnd:
        gia = int(xau * usd_vnd * (37.5 / 31.1035) * 1.03)  # oz → lượng, premium ~3%
        return _cache_set("vang_sjc", gia)
    return 79800000

def lay_ty_gia_usd_vnd():
    cached = _cache_get("usd_vnd")
    if cached: return cached
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        r = requests.get(url, timeout=10)
        data = r.json()
        if 'rates' in data and 'VND' in data['rates']:
            return _cache_set("usd_vnd", data['rates']['VND'])
    except Exception as e:
        logger.warning("lay_ty_gia_usd_vnd failed: %s", e)
    return 25400

def lay_chi_so_yahoo(ma, ky_han="1y"):
    try:
        hist = _yf_retry(ma, ky_han, retries=2, delay=1)
        if hist is None or hist.empty:
            return None, None, 0
        gia_hien_tai = float(hist['Close'].iloc[-1])
        gia_cu = float(hist['Close'].iloc[0])
        thay_doi = (gia_hien_tai - gia_cu) / gia_cu if gia_cu > 0 else 0
        return gia_hien_tai, thay_doi, hist
    except Exception as e:
        logger.warning("lay_chi_so_yahoo(%s) failed: %s", ma, e)
        return None, None, 0

def lay_gia_vang_the_gioi():
    cached = _cache_get("xau_usd")
    if cached: return cached
    gia, _, _ = lay_chi_so_yahoo("GC=F", "5d")
    if gia: return _cache_set("xau_usd", gia)
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        data = r.json()
        if 'price' in data:
            return _cache_set("xau_usd", data['price'])
    except Exception as e:
        logger.warning("lay_gia_vang_the_gioi (gold-api) failed: %s", e)
    return None

def lay_gia_bitcoin():
    cached = _cache_get("btc_usd")
    if cached: return cached
    gia, _, _ = lay_chi_so_yahoo("BTC-USD", "5d")
    if gia: return _cache_set("btc_usd", gia)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        data = r.json()
        if 'bitcoin' in data:
            return _cache_set("btc_usd", data['bitcoin']['usd'])
    except Exception as e:
        logger.warning("lay_gia_bitcoin (coingecko) failed: %s", e)
    return None

def lay_gia_ethereum():
    cached = _cache_get("eth_usd")
    if cached: return cached
    gia, _, _ = lay_chi_so_yahoo("ETH-USD", "5d")
    if gia: return _cache_set("eth_usd", gia)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10)
        data = r.json()
        if 'ethereum' in data:
            return _cache_set("eth_usd", data['ethereum']['usd'])
    except Exception as e:
        logger.warning("lay_gia_ethereum (coingecko) failed: %s", e)
    return None

def lay_gia_dau_tho():
    cached = _cache_get("dau_tho")
    if cached: return cached
    gia, _, _ = lay_chi_so_yahoo("CL=F", "5d")
    if gia: return _cache_set("dau_tho", gia)
    return None

def _lay_vn_index():
    # VN - try without ^ prefix for Yahoo, then fallback
    g, c, _ = lay_chi_so_yahoo("VNINDEX")
    if not g:
        g, c, _ = lay_chi_so_yahoo("^VNINDEX")
    return g, c

def _lay_index(ma):
    g, c, _ = lay_chi_so_yahoo(ma)
    return g, c

def lay_du_lieu_thi_truong_that():
    # Chạy song song tất cả lệnh gọi mạng với deadline tổng để tránh treo UI
    jobs = {
        "VN": _lay_vn_index,
        "HN": lambda: _lay_index("HNXINDEX"),
        "SP": lambda: _lay_index("^GSPC"),
        "DJ": lambda: _lay_index("^DJI"),
        "NAS": lambda: _lay_index("^IXIC"),
        "NK": lambda: _lay_index("^N225"),
        "HSI": lambda: _lay_index("^HSI"),
        "XAU": lay_gia_vang_the_gioi,
        "BTC": lay_gia_bitcoin,
        "ETH": lay_gia_ethereum,
        "OIL": lay_gia_dau_tho,
        "USD": lay_ty_gia_usd_vnd,
    }
    out = {}
    ex = ThreadPoolExecutor(max_workers=12)
    try:
        futs = {ex.submit(fn): key for key, fn in jobs.items()}
        deadline = time.time() + 20  # tối đa 20s cho toàn bộ thị trường
        for fut, key in futs.items():
            try:
                out[key] = fut.result(timeout=max(0.0, deadline - time.time()))
            except Exception as e:
                logger.warning("market fetch %s failed: %s", key, e)
                out[key] = None
    finally:
        ex.shutdown(wait=False, cancel_futures=True)

    vn_gia, vn_change = out.get("VN") or (None, None)
    if not vn_gia:
        vn_gia, vn_change = 1280, 0.118
    hn_gia, hn_change = out.get("HN") or (None, None)
    if not hn_gia:
        hn_gia, hn_change = 240, 0.075
    sp_gia, sp_change = out.get("SP") or (None, None)
    dj_gia, dj_change = out.get("DJ") or (None, None)
    nas_gia, nas_change = out.get("NAS") or (None, None)
    nk_gia, nk_change = out.get("NK") or (None, None)
    hsi_gia, hsi_change = out.get("HSI") or (None, None)
    xau_gia = out.get("XAU")
    btc_gia = out.get("BTC")
    eth_gia = out.get("ETH")
    oil_gia = out.get("OIL")
    usd_vnd = out.get("USD") or 25400

    result = {}

    if vn_gia:
        result["VN-Index"] = {"gia_hien_tai": round(vn_gia, 2), "thay_doi_1nam": round(vn_change, 4), "ma": "^VNINDEX", "mieu_ta": "Sàn HOSE - TP.HCM"}
    if hn_gia:
        result["HNX-Index"] = {"gia_hien_tai": round(hn_gia, 2), "thay_doi_1nam": round(hn_change, 4), "ma": "^HNXINDEX", "mieu_ta": "Sàn HNX - Hà Nội"}

    result.update({
        "S&P 500": {"gia_hien_tai": round(sp_gia, 2) if sp_gia else 5430, "thay_doi_1nam": round(sp_change, 4) if sp_change else 0.12, "mieu_ta": "Chỉ số 500 công ty lớn nhất Mỹ", "ma": "^GSPC"},
        "Dow Jones": {"gia_hien_tai": round(dj_gia, 2) if dj_gia else 38800, "thay_doi_1nam": round(dj_change, 4) if dj_change else 0.08, "mieu_ta": "Chỉ số 30 công ty công nghiệp Mỹ", "ma": "^DJI"},
        "Nasdaq": {"gia_hien_tai": round(nas_gia, 2) if nas_gia else 17600, "thay_doi_1nam": round(nas_change, 4) if nas_change else 0.18, "mieu_ta": "Chỉ số công ty công nghệ Mỹ", "ma": "^IXIC"},
        "Nikkei 225": {"gia_hien_tai": round(nk_gia, 2) if nk_gia else 38500, "thay_doi_1nam": round(nk_change, 4) if nk_change else 0.14, "mieu_ta": "Chỉ số chính của Nhật Bản", "ma": "^N225"},
        "HSI": {"gia_hien_tai": round(hsi_gia, 2) if hsi_gia else 17800, "thay_doi_1nam": round(hsi_change, 4) if hsi_change else -0.05, "mieu_ta": "Hang Seng Index - Hong Kong", "ma": "^HSI"},
        "Vàng/XAU": {"gia_hien_tai": round(xau_gia, 2) if xau_gia else 2350, "thay_doi_1nam": 0.22, "mieu_ta": "Giá vàng thế giới (USD/oz)", "ma": "GC=F"},
        "Dầu WTI": {"gia_hien_tai": round(oil_gia, 2) if oil_gia else 78, "thay_doi_1nam": 0.06, "mieu_ta": "Dầu thô WTI (USD/thùng)", "ma": "CL=F"},
        "Bitcoin": {"gia_hien_tai": btc_gia if btc_gia else 67000, "thay_doi_1nam": 0.85, "mieu_ta": "Tiền điện tử lớn nhất thế giới", "ma": "BTC-USD"},
        "Ethereum": {"gia_hien_tai": eth_gia if eth_gia else 3500, "thay_doi_1nam": 0.65, "mieu_ta": "Tiền điện tử lớn thứ 2 thế giới", "ma": "ETH-USD"},
        "USD/VND": {"gia_hien_tai": usd_vnd, "thay_doi_1nam": 0.03, "mieu_ta": "Tỷ giá Đô la Mỹ - Việt Nam Đồng", "ma": "USDVND=X"},
    })

    return result

def lay_gia_co_phieu(ma):
    try:
        hist = _yf_retry(ma + ".VN" if len(ma) <= 4 else ma, "5d", retries=2, delay=1)
        if hist is not None and not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception as e:
        logger.debug("lay_gia_co_phieu yahoo(%s): %s", ma, e)
    try:
        url = f"https://finfo-api.vndirect.com.vn/v4/stock_prices?q=code:{ma}&size=1"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('data') and len(data['data']) > 0:
            return data['data'][0].get('close', 0) * 1000
    except Exception as e:
        logger.debug("lay_gia_co_phieu vndirect(%s): %s", ma, e)
    return None

def lay_gia_co_phieu_hang_loat():
    ds_ma = ["VCB", "VIC", "FPT", "VNM", "HPG", "MSN", "SSI", "MWG", "ACB", "GAS"]
    ket_qua = {}
    ex = ThreadPoolExecutor(max_workers=10)
    try:
        futs = {ex.submit(lay_gia_co_phieu, ma): ma for ma in ds_ma}
        deadline = time.time() + 25  # tối đa 25s cho toàn bộ cổ phiếu
        for fut, ma in futs.items():
            try:
                gia = fut.result(timeout=max(0.0, deadline - time.time()))
                if gia:
                    ket_qua[ma] = gia
            except Exception as e:
                logger.debug("lay_gia_co_phieu_hang_loat(%s): %s", ma, e)
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    return ket_qua
