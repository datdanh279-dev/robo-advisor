import logging
from .api_fetcher import (
    lay_du_lieu_thi_truong_that,
    lay_gia_co_phieu,
    lay_gia_co_phieu_hang_loat,
    lay_gia_vang_sjc,
    lay_ty_gia_usd_vnd,
)
from .data_loader import DOCS

logger = logging.getLogger(__name__)

DU_LIEU_THI_TRUONG_VN = {
    "VN-Index": {"mo_ta": "Sàn HOSE - TP.HCM", "gia_hien_tai": 1280, "thay_doi_1nam": 0.118, "bang_xep_hang": "Đang tải...", "don_vi": "điểm"},
    "HNX-Index": {"mo_ta": "Sàn HNX - Hà Nội", "gia_hien_tai": 240, "thay_doi_1nam": 0.075, "bang_xep_hang": "Đang tải...", "don_vi": "điểm"},
    "Vàng SJC": {"mo_ta": "Vàng miếng SJC", "gia_hien_tai": 86000000, "thay_doi_1nam": 0.195, "bang_xep_hang": "Đang tải...", "don_vi": "VND/lượng"},
    "USD/VND": {"mo_ta": "Tỷ giá Đô la Mỹ", "gia_hien_tai": 25400, "thay_doi_1nam": 0.03, "bang_xep_hang": "Đang tải...", "don_vi": "VND"},
    "Lãi suất tiết kiệm": {"mo_ta": "Lãi suất VCB kỳ hạn 12 tháng", "gia_hien_tai": DOCS.get("performance", {}).get("Rf", 0.048), "thay_doi_1nam": -0.02, "bang_xep_hang": "Đang tải...", "don_vi": "%"},
    "Trái phiếu chính phủ": {"mo_ta": "Lợi suất TPCP kỳ hạn 10 năm", "gia_hien_tai": 0.0705, "thay_doi_1nam": 0.005, "bang_xep_hang": "Đang tải...", "don_vi": "%"},
}
DU_LIEU_QUOC_TE = {
    "S&P 500": {"mieu_ta": "Chỉ số 500 công ty lớn nhất Mỹ", "gia_hien_tai": 5430, "thay_doi_1nam": 0.12, "ma_yahoo": "^GSPC"},
    "Dow Jones": {"mieu_ta": "Chỉ số 30 công ty công nghiệp Mỹ", "gia_hien_tai": 38800, "thay_doi_1nam": 0.08, "ma_yahoo": "^DJI"},
    "Nasdaq": {"mieu_ta": "Chỉ số công ty công nghệ Mỹ", "gia_hien_tai": 17600, "thay_doi_1nam": 0.18, "ma_yahoo": "^IXIC"},
    "Nikkei 225": {"mieu_ta": "Chỉ số chính của Nhật Bản", "gia_hien_tai": 38500, "thay_doi_1nam": 0.14, "ma_yahoo": "^N225"},
    "HSI": {"mieu_ta": "Hang Seng Index - Hong Kong", "gia_hien_tai": 17800, "thay_doi_1nam": -0.05, "ma_yahoo": "^HSI"},
    "Vàng/XAU": {"mieu_ta": "Giá vàng thế giới (USD/oz)", "gia_hien_tai": 2350, "thay_doi_1nam": 0.22, "ma_yahoo": "GC=F"},
    "Dầu WTI": {"mieu_ta": "Dầu thô WTI (USD/thùng)", "gia_hien_tai": 78, "thay_doi_1nam": 0.06, "ma_yahoo": "CL=F"},
    "Bitcoin": {"mieu_ta": "Tiền điện tử lớn nhất thế giới", "gia_hien_tai": 67000, "thay_doi_1nam": 0.85, "ma_yahoo": "BTC-USD"},
    "Ethereum": {"mieu_ta": "Tiền điện tử lớn thứ 2 thế giới", "gia_hien_tai": 3500, "thay_doi_1nam": 0.65, "ma_yahoo": "ETH-USD"},
}
CO_PHIEU_VN = {}

def _build_co_phieu_vn():
    global CO_PHIEU_VN
    live = DOCS["live"]
    if not live:
        CO_PHIEU_VN = {
            "VCB": {"ten": "Vietcombank", "nganh": "Ngân hàng", "gia": 95000, "thay_doi_1nam": 0.22},
            "VIC": {"ten": "Vingroup", "nganh": "Bất động sản", "gia": 45000, "thay_doi_1nam": -0.05},
            "FPT": {"ten": "FPT Corporation", "nganh": "Công nghệ", "gia": 120000, "thay_doi_1nam": 0.35},
            "VNM": {"ten": "Vinamilk", "nganh": "Sữa & Thực phẩm", "gia": 72000, "thay_doi_1nam": 0.08},
            "HPG": {"ten": "Hòa Phát", "nganh": "Thép", "gia": 28000, "thay_doi_1nam": 0.15},
            "MSN": {"ten": "Masan Group", "nganh": "Hàng tiêu dùng", "gia": 85000, "thay_doi_1nam": 0.10},
            "SSI": {"ten": "SSI Securities", "nganh": "Chứng khoán", "gia": 38000, "thay_doi_1nam": 0.45},
            "MWG": {"ten": "Thế Giới Di Động", "nganh": "Bán lẻ", "gia": 55000, "thay_doi_1nam": -0.12},
            "ACB": {"ten": "ACB Bank", "nganh": "Ngân hàng", "gia": 25000, "thay_doi_1nam": 0.18},
            "GAS": {"ten": "Petrovietnam Gas", "nganh": "Dầu khí", "gia": 115000, "thay_doi_1nam": 0.20},
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
            "thay_doi_1nam": db_info.get("ytd", info.get("thay_doi_pct", 0)) / 100 if isinstance(info.get("thay_doi_pct", 0), (int, float)) else 0,
            "pe": info.get("pe", db_info.get("pe", 0)),
            "pb": info.get("pb", db_info.get("pb", 0)),
            "eps": db_info.get("eps", 0),
            "roe": db_info.get("roe", 0),
            "von_hoa": db_info.get("von_hoa", 0),
            "tin_hieu": db_info.get("tin_hieu", ""),
        }

_build_co_phieu_vn()

def cap_nhat_toan_bo():
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
                    }
    except Exception as e:
        logger.warning("cap_nhat_toan_bo stock prices failed: %s", e)

    try:
        cp = lay_gia_co_phieu_hang_loat()
        for ma, gia in cp.items():
            if ma in CO_PHIEU_VN and gia and not (gia != gia):
                CO_PHIEU_VN[ma]["gia"] = int(gia)
    except Exception as e:
        logger.warning("cap_nhat_toan_bo stock prices failed: %s", e)

def lay_thong_tin_thi_truong():
    return DU_LIEU_THI_TRUONG_VN

def lay_thong_tin_quoc_te():
    return DU_LIEU_QUOC_TE

DANH_SACH_NGANH = sorted(set(
    info["nganh"] for info in CO_PHIEU_VN.values() if info.get("nganh")
)) or ["Ngân hàng", "Công nghệ", "Thép", "Tiêu dùng", "Bán lẻ", "Chứng khoán", "Bất động sản", "Hạ tầng", "Dầu khí"]

def lay_co_phieu_de_xuat(nganh=None):
    if nganh and nganh != "Tất cả":
        return {ma: info for ma, info in CO_PHIEU_VN.items() if info.get("nganh") == nganh}
    return CO_PHIEU_VN

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
