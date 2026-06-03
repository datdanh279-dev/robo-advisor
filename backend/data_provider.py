"""
data_provider.py — Lớp lấy dữ liệu thị trường THẬT từ vnstock.

- Tự sửa lỗi UTF-8 trên console Windows (vnstock in banner có emoji).
- Cache theo ngày trong bộ nhớ process => không gọi API lặp lại mỗi lần Streamlit rerun.
- Luôn có fallback: nếu mạng/vnstock lỗi, trả về None để lớp trên dùng số liệu tĩnh.
"""

import sys
import datetime as dt

# --- Fix UTF-8 để banner emoji của vnstock không làm crash trên Windows (cp1252) ---
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

_VNSTOCK_OK = True
try:
    from vnstock import Vnstock
except Exception:
    _VNSTOCK_OK = False

# Trạng thái nguồn dữ liệu, lớp UI đọc để hiện badge "LIVE" / "Offline"
TRANG_THAI_NGUON = {"live": False, "cap_nhat": None, "loi": None}

# Cache: { key: (ngay_cache, du_lieu) }
_CACHE = {}
_TTL_NGAY = 1  # làm mới mỗi ngày


def _con_han(ngay_cache):
    return (dt.date.today() - ngay_cache).days < _TTL_NGAY


def _lay_cache(key):
    item = _CACHE.get(key)
    if item and _con_han(item[0]):
        return item[1]
    return None


def _luu_cache(key, value):
    _CACHE[key] = (dt.date.today(), value)
    return value


def _khoang_ngay(so_ngay=400):
    den = dt.date.today()
    tu = den - dt.timedelta(days=so_ngay)
    return tu.isoformat(), den.isoformat()


def lay_lich_su(ma, so_ngay=400, source="VCI"):
    """Trả về DataFrame lịch sử giá [time, open, high, low, close, volume] hoặc None."""
    if not _VNSTOCK_OK:
        return None
    key = f"hist::{ma}::{so_ngay}"
    cached = _lay_cache(key)
    if cached is not None:
        return cached
    try:
        tu, den = _khoang_ngay(so_ngay)
        stock = Vnstock().stock(symbol=ma, source=source)
        df = stock.quote.history(start=tu, end=den, interval="1D")
        if df is None or len(df) == 0:
            return None
        TRANG_THAI_NGUON.update(live=True, cap_nhat=dt.datetime.now(), loi=None)
        return _luu_cache(key, df)
    except Exception as e:  # noqa: BLE001 - chủ động nuốt lỗi để fallback
        TRANG_THAI_NGUON.update(live=False, loi=str(e))
        return None


def gia_va_bien_dong(ma, source="VCI"):
    """
    Trả về dict {gia, thay_doi_1nam} theo VND (giá vnstock tính bằng nghìn đồng -> x1000),
    hoặc None nếu không lấy được.
    """
    df = lay_lich_su(ma, so_ngay=400, source=source)
    if df is None or len(df) < 2:
        return None
    try:
        gia_cuoi = float(df["close"].iloc[-1])
        gia_dau = float(df["close"].iloc[0])
        thay_doi = (gia_cuoi / gia_dau - 1) if gia_dau else 0.0
        # Cổ phiếu/giá index vnstock trả theo nghìn đồng; index thì giữ nguyên.
        return {"gia": gia_cuoi, "thay_doi_1nam": thay_doi, "_raw_close": gia_cuoi}
    except Exception:
        return None


def gia_co_phieu(ma, source="VCI"):
    """Giá cổ phiếu theo VND (x1000) + biến động 1 năm; None nếu lỗi."""
    kq = gia_va_bien_dong(ma, source=source)
    if kq is None:
        return None
    return {"gia": kq["gia"] * 1000, "thay_doi_1nam": kq["thay_doi_1nam"]}


def chi_so(ma="VNINDEX", source="VCI"):
    """Chỉ số thị trường (VNINDEX, HNXINDEX...) — trả {gia, thay_doi_1nam} hoặc None."""
    kq = gia_va_bien_dong(ma, source=source)
    if kq is None:
        return None
    return {"gia": kq["gia"], "thay_doi_1nam": kq["thay_doi_1nam"]}
