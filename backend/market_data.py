import logging
import threading
from .api_fetcher import (
    lay_du_lieu_thi_truong_that,
    lay_gia_co_phieu,
    lay_gia_co_phieu_hang_loat,
    lay_gia_vang_sjc,
    lay_ty_gia_usd_vnd,
    dang_trong_gio_giao_dich_vn,
    gia_dong_cua_gan_nhat,
)
from .data_loader import DOCS

logger = logging.getLogger(__name__)

# Lock bảo vệ DU_LIEU_THI_TRUONG_VN, DU_LIEU_QUOC_TE, CO_PHIEU_VN khi
# nhiều user cùng gọi cap_nhat_toan_bo() / _build_co_phieu_vn() — tránh
# "nhầm nhà" khi concurrent write.
_DATA_LOCK = threading.RLock()

# 8 mã danh mục mẫu (đồng bộ TONG_HOP_v44 / danh_muc.json)
DANH_SACH_DANH_MUC = ["FPT", "MBB", "VCB", "CTR", "MWG", "HPG", "VNM", "VIX"]

_DON_VI_QUOC_TE = {
    "S&P 500": "điểm",
    "Dow Jones": "điểm",
    "Nasdaq": "điểm",
    "Nikkei 225": "điểm",
    "HSI": "điểm",
    "Vàng/XAU": "USD/oz",
    "Dầu WTI": "USD/thùng",
    "Bitcoin": "USD",
    "Ethereum": "USD",
}

DU_LIEU_THI_TRUONG_VN = {
    "VN-Index": {"mo_ta": "Sàn HOSE - TP.HCM", "gia_hien_tai": 1280, "thay_doi_1nam": 0.118, "bang_xep_hang": "Đang tải...", "don_vi": "điểm"},
    "HNX-Index": {"mo_ta": "Sàn HNX - Hà Nội", "gia_hien_tai": 240, "thay_doi_1nam": 0.075, "bang_xep_hang": "Đang tải...", "don_vi": "điểm"},
    "Vàng SJC": {"mo_ta": "Vàng miếng SJC", "gia_hien_tai": 86000000, "thay_doi_1nam": 0.195, "bang_xep_hang": "Đang tải...", "don_vi": "VND/lượng"},
    "USD/VND": {"mo_ta": "Tỷ giá Đô la Mỹ", "gia_hien_tai": 25400, "thay_doi_1nam": 0.03, "bang_xep_hang": "Đang tải...", "don_vi": "VND"},
    "Lãi suất tiết kiệm": {"mo_ta": "Lãi suất VCB kỳ hạn 12 tháng", "gia_hien_tai": DOCS.get("performance", {}).get("Rf", 0.048), "thay_doi_1nam": -0.02, "bang_xep_hang": "Đang tải...", "don_vi": "%"},
    "Trái phiếu chính phủ": {"mo_ta": "Lợi suất TPCP kỳ hạn 10 năm", "gia_hien_tai": 0.0705, "thay_doi_1nam": 0.005, "bang_xep_hang": "Đang tải...", "don_vi": "%"},
}
def _qt_entry(mieu_ta, gia, thay_doi, ma_yahoo, don_vi):
    return {
        "mieu_ta": mieu_ta,
        "gia_hien_tai": gia,
        "thay_doi_1nam": thay_doi,
        "ma_yahoo": ma_yahoo,
        "don_vi": don_vi,
    }


DU_LIEU_QUOC_TE = {
    "S&P 500": _qt_entry("Chỉ số 500 công ty lớn nhất Mỹ", 5430, 0.12, "^GSPC", _DON_VI_QUOC_TE["S&P 500"]),
    "Dow Jones": _qt_entry("Chỉ số 30 công ty công nghiệp Mỹ", 38800, 0.08, "^DJI", _DON_VI_QUOC_TE["Dow Jones"]),
    "Nasdaq": _qt_entry("Chỉ số công ty công nghệ Mỹ", 17600, 0.18, "^IXIC", _DON_VI_QUOC_TE["Nasdaq"]),
    "Nikkei 225": _qt_entry("Chỉ số chính của Nhật Bản", 38500, 0.14, "^N225", _DON_VI_QUOC_TE["Nikkei 225"]),
    "HSI": _qt_entry("Hang Seng Index - Hong Kong", 17800, -0.05, "^HSI", _DON_VI_QUOC_TE["HSI"]),
    "Vàng/XAU": _qt_entry("Giá vàng thế giới (USD/oz)", 2350, 0.22, "GC=F", _DON_VI_QUOC_TE["Vàng/XAU"]),
    "Dầu WTI": _qt_entry("Dầu thô WTI (USD/thùng)", 78, 0.06, "CL=F", _DON_VI_QUOC_TE["Dầu WTI"]),
    "Bitcoin": _qt_entry("Tiền điện tử lớn nhất thế giới", 67000, 0.85, "BTC-USD", _DON_VI_QUOC_TE["Bitcoin"]),
    "Ethereum": _qt_entry("Tiền điện tử lớn thứ 2 thế giới", 3500, 0.65, "ETH-USD", _DON_VI_QUOC_TE["Ethereum"]),
}


def dinh_dang_gia_quoc_te(ten: str, gia) -> str:
    """Hiển thị giá chỉ số quốc tế kèm đơn vị tiền tệ."""
    if not isinstance(gia, (int, float)):
        return str(gia)
    don_vi = _DON_VI_QUOC_TE.get(ten, DU_LIEU_QUOC_TE.get(ten, {}).get("don_vi", ""))
    if don_vi in ("USD", "USD/oz", "USD/thùng"):
        prefix = "$" if don_vi == "USD" else ""
        suffix = {"USD/oz": " USD/oz", "USD/thùng": " USD/thùng"}.get(don_vi, "")
        val = f"{gia:,.2f}" if gia < 10000 else f"{gia:,.0f}"
        return f"{prefix}{val}{suffix}".strip()
    if gia >= 1000:
        return f"{gia:,.0f} điểm"
    return f"{gia:,.2f} điểm"
CO_PHIEU_VN = {}

def _build_co_phieu_vn():
    global CO_PHIEU_VN
    with _DATA_LOCK:
        _build_co_phieu_vn_impl()


def _build_co_phieu_vn_impl():
    global CO_PHIEU_VN
    live = DOCS["live"]
    if not live:
        db_vn = DOCS.get("co_phieu_vn", {})
        if db_vn:
            CO_PHIEU_VN = {}
            for ma, info in db_vn.items():
                CO_PHIEU_VN[ma] = {
                    "ten": info.get("ten", ""),
                    "nganh": info.get("nganh", ""),
                    "gia": info.get("gia", 0),
                    "thay_doi_1nam": info.get("ytd", 0) / 100 if isinstance(info.get("ytd"), (int, float)) else 0,
                    "pe": info.get("pe", 0),
                    "pb": info.get("pb", 0),
                    "eps": info.get("eps", 0),
                    "roe": info.get("roe", 0),
                    "von_hoa": info.get("von_hoa", 0),
                    "tin_hieu": info.get("tin_hieu", ""),
                }
            return
        CO_PHIEU_VN = {
            "VCB": {"ten": "Vietcombank", "nganh": "Ngân hàng", "gia": 95000, "thay_doi_1nam": 0.22, "pe": 15, "pb": 3.2, "tin_hieu": "GIỮ"},
            "VIC": {"ten": "Vingroup", "nganh": "Bất động sản", "gia": 45000, "thay_doi_1nam": -0.05, "pe": 30, "pb": 2.1, "tin_hieu": "TRÁNH"},
            "FPT": {"ten": "FPT Corporation", "nganh": "Công nghệ", "gia": 120000, "thay_doi_1nam": 0.35, "pe": 22, "pb": 5.1, "tin_hieu": "MUA"},
            "VNM": {"ten": "Vinamilk", "nganh": "Sữa & Thực phẩm", "gia": 72000, "thay_doi_1nam": 0.08, "pe": 18, "pb": 3.5, "tin_hieu": "GIỮ"},
            "HPG": {"ten": "Hòa Phát", "nganh": "Thép", "gia": 28000, "thay_doi_1nam": 0.15, "pe": 12, "pb": 1.8, "tin_hieu": "MUA"},
            "MSN": {"ten": "Masan Group", "nganh": "Hàng tiêu dùng", "gia": 85000, "thay_doi_1nam": 0.10, "pe": 25, "pb": 3.0, "tin_hieu": "GIỮ"},
            "SSI": {"ten": "SSI Securities", "nganh": "Chứng khoán", "gia": 38000, "thay_doi_1nam": 0.45, "pe": 20, "pb": 2.8, "tin_hieu": "MUA"},
            "MWG": {"ten": "Thế Giới Di Động", "nganh": "Bán lẻ", "gia": 55000, "thay_doi_1nam": -0.12, "pe": 40, "pb": 4.2, "tin_hieu": "TRÁNH"},
            "ACB": {"ten": "ACB Bank", "nganh": "Ngân hàng", "gia": 25000, "thay_doi_1nam": 0.18, "pe": 8, "pb": 1.5, "tin_hieu": "MUA"},
            "GAS": {"ten": "Petrovietnam Gas", "nganh": "Dầu khí", "gia": 115000, "thay_doi_1nam": 0.20, "pe": 16, "pb": 2.5, "tin_hieu": "GIỮ"},
        }
        return
    db = DOCS["co_phieu_vn"]
    for ma, info in live.items():
        if ma in db:
            db_info = db[ma]
        else:
            db_info = {}
        CO_PHIEU_VN[ma] = {
            "ten": info.get("ten", db_info.get("ten", "")),
            "nganh": info.get("nganh", db_info.get("nganh", "")),
            "gia": info.get("gia", 0),
            "thay_doi_1nam": (db_info.get("ytd", 0) / 100) if isinstance(db_info.get("ytd"), (int, float)) and db_info.get("ytd") else 0,
            "pe": db_info.get("pe", info.get("pe", 0)),
            "pb": db_info.get("pb", info.get("pb", 0)),
            "eps": db_info.get("eps", 0),
            "roe": db_info.get("roe", 0),
            "von_hoa": db_info.get("von_hoa", 0),
            "tin_hieu": db_info.get("tin_hieu", ""),
        }

def cap_nhat_co_phieu_vn():
    _build_co_phieu_vn()

_build_co_phieu_vn()

def cap_nhat_toan_bo():
    with _DATA_LOCK:
        _cap_nhat_toan_bo_impl()


def _cap_nhat_toan_bo_impl():
    # Kiểm tra giờ giao dịch: nếu ngoài giờ VN, bỏ qua cập nhật giá cổ phiếu VN (tránh NaN)
    trong_gio_vn = dang_trong_gio_giao_dich_vn()

    try:
        tt = lay_du_lieu_thi_truong_that()
        if tt:
            vn_keys = ["VN-Index", "HNX-Index"]
            for ten in vn_keys:
                if ten in tt:
                    DU_LIEU_THI_TRUONG_VN[ten] = {
                        "mo_ta": tt[ten].get("mieu_ta", ""),
                        "gia_hien_tai": tt[ten].get("gia_hien_tai", 0),
                        "thay_doi_1nam": tt[ten].get("thay_doi_1nam", 0),
                        "bang_xep_hang": "Trực tuyến",
                        "ma_yahoo": tt[ten].get("ma", ""),
                        "don_vi": "điểm",
                    }
            DU_LIEU_THI_TRUONG_VN["Vàng SJC"] = {
                "mo_ta": "Vàng miếng SJC",
                "gia_hien_tai": lay_gia_vang_sjc(),
                "thay_doi_1nam": 0.195,
                "bang_xep_hang": "Trực tuyến",
                "don_vi": "VND/lượng",
            }
            DU_LIEU_THI_TRUONG_VN["USD/VND"] = {
                "mo_ta": "Tỷ giá Đô la Mỹ",
                "gia_hien_tai": lay_ty_gia_usd_vnd(),
                "thay_doi_1nam": 0.03,
                "bang_xep_hang": "Trực tuyến",
                "don_vi": "VND",
            }
            DU_LIEU_THI_TRUONG_VN["Lãi suất tiết kiệm"] = {
                "mo_ta": "Lãi suất VCB kỳ hạn 12 tháng",
                "gia_hien_tai": DOCS.get("performance", {}).get("Rf", 0.048),
                "thay_doi_1nam": -0.02,
                "bang_xep_hang": "Trực tuyến",
                "don_vi": "%",
            }
            DU_LIEU_THI_TRUONG_VN["Trái phiếu chính phủ"] = {
                "mo_ta": "Lợi suất TPCP kỳ hạn 10 năm",
                "gia_hien_tai": 0.0705,
                "thay_doi_1nam": 0.005,
                "bang_xep_hang": "Trực tuyến",
                "don_vi": "%",
            }

            qt_keys = ["S&P 500", "Dow Jones", "Nasdaq", "Nikkei 225", "HSI", "Vàng/XAU", "Dầu WTI", "Bitcoin", "Ethereum"]
            for ten in qt_keys:
                if ten in tt:
                    DU_LIEU_QUOC_TE[ten] = {
                        "mieu_ta": tt[ten].get("mieu_ta", ""),
                        "gia_hien_tai": tt[ten].get("gia_hien_tai", 0),
                        "thay_doi_1nam": tt[ten].get("thay_doi_1nam", 0),
                        "ma_yahoo": tt[ten].get("ma", ""),
                        "don_vi": _DON_VI_QUOC_TE.get(ten, "điểm"),
                    }
    except Exception as e:
        logger.warning("cap_nhat_toan_bo stock prices failed: %s", e)

    if trong_gio_vn:
        try:
            cp = lay_gia_co_phieu_hang_loat()
            for ma, gia in cp.items():
                if ma in CO_PHIEU_VN and gia and not (gia != gia):
                    CO_PHIEU_VN[ma]["gia"] = int(gia)
        except Exception as e:
            logger.warning("cap_nhat_toan_bo stock prices failed: %s", e)
    else:
        logger.info("Ngoài giờ giao dịch VN — giữ nguyên giá đóng cửa gần nhất.")

def lay_thong_tin_thi_truong():
    with _DATA_LOCK:
        return dict(DU_LIEU_THI_TRUONG_VN)

def lay_thong_tin_quoc_te():
    with _DATA_LOCK:
        return dict(DU_LIEU_QUOC_TE)

DANH_SACH_NGANH = sorted(set(
    info["nganh"] for info in CO_PHIEU_VN.values() if info.get("nganh")
)) or ["Ngân hàng", "Công nghệ", "Thép", "Tiêu dùng", "Bán lẻ", "Chứng khoán", "Bất động sản", "Hạ tầng", "Dầu khí"]

def lay_co_phieu_de_xuat(nganh=None):
    with _DATA_LOCK:
        if nganh and nganh != "Tất cả":
            return {ma: dict(info) for ma, info in CO_PHIEU_VN.items() if info.get("nganh") == nganh}
        return {ma: dict(info) for ma, info in CO_PHIEU_VN.items()}

def phan_tich_dau_tu_theo_nganh(so_tien, khau_vi_rui_ro):
    if khau_vi_rui_ro in ["Bảo thủ", "Thận trọng"]:
        nganh_uu_tien = ["Ngân hàng", "Sữa & Thực phẩm", "Hàng tiêu dùng"]
    elif khau_vi_rui_ro in ["Trung dung"]:
        nganh_uu_tien = ["Ngân hàng", "Thép", "Công nghệ", "Dầu khí"]
    else:
        nganh_uu_tien = ["Công nghệ", "Chứng khoán", "Bất động sản", "Bán lẻ"]

    co_phieu_loc = [
        (ma, info)
        for ma, info in CO_PHIEU_VN.items()
        if info["nganh"] in nganh_uu_tien
    ]

    so_tien_moi_co_phieu = so_tien / len(co_phieu_loc) if co_phieu_loc else 0
    de_xuat = []

    for ma, info in co_phieu_loc:
        so_co_phieu = so_tien_moi_co_phieu / info["gia"] if info.get("gia", 0) > 0 else 0
        de_xuat.append({
            "ma": ma,
            "ten": info["ten"],
            "nganh": info["nganh"],
            "gia": info["gia"],
            "so_tien_dau_tu": round(so_tien_moi_co_phieu, -3),
            "so_luong_co_phieu": int(so_co_phieu),
        })

    return de_xuat
