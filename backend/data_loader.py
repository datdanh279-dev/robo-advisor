import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

_EXCEL_CANDIDATES = [
    os.environ.get("EXCEL_PATH"),
    os.path.join(_PROJECT_DIR, "data", "TONG_HOP_v44_SOI_HOP_NHAT.xlsx"),
    os.path.join(_PROJECT_DIR, "TONG_HOP_v44_SOI_HOP_NHAT.xlsx"),
]

EXCEL_PATH = None
for _p in _EXCEL_CANDIDATES:
    if _p and os.path.exists(_p):
        EXCEL_PATH = _p
        break

if EXCEL_PATH is None:
    EXCEL_PATH = _EXCEL_CANDIDATES[-1]
    logger.warning("Excel file not found — falling back to %s", EXCEL_PATH)

_NGAY_FILE = "29/05/2026"
if EXCEL_PATH and os.path.exists(EXCEL_PATH):
    _mtime = os.path.getmtime(EXCEL_PATH)
    _NGAY_FILE = datetime.fromtimestamp(_mtime).strftime("%d/%m/%Y")

def doc_live_price():
    df = pd.read_excel(EXCEL_PATH, sheet_name="📡 LIVE PRICE FEED", header=None)
    data = {}
    for i in range(2, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            gia = float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0
            thay_doi_pct = float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0
            pe = float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0
            pb = float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0
            kl = float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0
        except:
            continue
        data[ma] = {
            "ten": str(r.iloc[1])[:50] if pd.notna(r.iloc[1]) else "",
            "nganh": str(r.iloc[2])[:30] if pd.notna(r.iloc[2]) else "",
            "gia": gia,
            "thay_doi_pct": thay_doi_pct,
            "pe": pe,
            "pb": pb,
            "khoi_luong": kl,
        }
    return data

def doc_co_phieu_vn():
    df = pd.read_excel(EXCEL_PATH, sheet_name="📈 Cổ Phiếu VN 🔍", header=None)
    data = {}
    for i in range(3, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            entry = {
                "ten": str(r.iloc[1])[:50] if pd.notna(r.iloc[1]) else "",
                "nganh": str(r.iloc[2])[:30] if pd.notna(r.iloc[2]) else "",
                "gia": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                "pe": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                "pb": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                "roe": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                "von_hoa": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                "eps": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                "ytd": float(r.iloc[9]) if pd.notna(r.iloc[9]) else 0,
                "tin_hieu": str(r.iloc[10])[:20] if pd.notna(r.iloc[10]) else "",
                "ghi_chu": str(r.iloc[11])[:100] if pd.notna(r.iloc[11]) else "",
                "von_csh": float(r.iloc[12]) if pd.notna(r.iloc[12]) else 0,
                "no_vay": float(r.iloc[13]) if pd.notna(r.iloc[13]) else 0,
                "ebitda": float(r.iloc[14]) if pd.notna(r.iloc[14]) else 0,
                "dt_2025": float(r.iloc[15]) if pd.notna(r.iloc[15]) else 0,
                "lnst_2025": float(r.iloc[16]) if pd.notna(r.iloc[16]) else 0,
                "bien_ln": float(r.iloc[17]) if pd.notna(r.iloc[17]) else 0,
                "roic": float(r.iloc[18]) if pd.notna(r.iloc[18]) else 0,
                "de_ratio": float(r.iloc[19]) if pd.notna(r.iloc[19]) else 0,
                "co_tuc_pct": float(r.iloc[20]) if pd.notna(r.iloc[20]) else 0,
                "co_tuc_d": float(r.iloc[21]) if pd.notna(r.iloc[21]) else 0,
                "pct_ngoai": float(r.iloc[22]) if pd.notna(r.iloc[22]) else 0,
                "insider_pct": float(r.iloc[23]) if pd.notna(r.iloc[23]) else 0,
                "chu_tich": str(r.iloc[24])[:50] if pd.notna(r.iloc[24]) else "",
                "esg_score": str(r.iloc[25])[:20] if pd.notna(r.iloc[25]) else "",
                "dao_duc": str(r.iloc[26])[:20] if pd.notna(r.iloc[26]) else "",
                "canh_bao": str(r.iloc[27])[:50] if pd.notna(r.iloc[27]) else "",
                "san": str(r.iloc[28])[:10] if pd.notna(r.iloc[28]) else "",
            }
        except:
            continue
        data[ma] = entry
    return data

def doc_co_phieu_tg():
    df = pd.read_excel(EXCEL_PATH, sheet_name="🌐 Cổ Phiếu TG 🔍", header=None)
    data = {}
    for i in range(3, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 10:
            continue
        try:
            data[ma] = {
                "ten": str(r.iloc[1])[:50] if pd.notna(r.iloc[1]) else "",
                "san": str(r.iloc[2])[:10] if pd.notna(r.iloc[2]) else "",
                "gia": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                "pe": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                "pb": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                "roe": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                "von_hoa": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                "ytd": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                "tin_hieu": str(r.iloc[9])[:20] if pd.notna(r.iloc[9]) else "",
                "nganh": str(r.iloc[10])[:30] if pd.notna(r.iloc[10]) else "",
            }
        except:
            continue
    return data

def doc_danh_muc():
    df = pd.read_excel(EXCEL_PATH, sheet_name="HỆ THỐNG QUẢN LÝ ", header=None)
    data = {}
    for i in range(4, len(df)):
        r = df.iloc[i]
        ma = str(r.iloc[0]).strip().upper()
        if not ma or ma == "NAN" or len(ma) > 6:
            continue
        try:
            entry = {
                "nganh": str(r.iloc[1])[:30] if pd.notna(r.iloc[1]) else "",
                "cong_ty": str(r.iloc[2])[:20] if pd.notna(r.iloc[2]) else "",
                "ty_trong_muc_tieu": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                "so_luong": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                "gia_von": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                "gia_thi_truong": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                "von_hoa": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                "no_ky_quy": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
            }
        except:
            continue
        data[ma] = entry
    return data

def doc_kpi():
    df = pd.read_excel(EXCEL_PATH, sheet_name="📈 Dashboard KPI", header=None)
    portfolio = {}
    kpi_header = None
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            kpi_header = i
            break
    if kpi_header is not None:
        for i in range(kpi_header + 1, len(df)):
            r = df.iloc[i]
            ma = str(r.iloc[0]).strip().upper()
            if not ma or ma == "NAN" or len(ma) > 6:
                continue
            try:
                portfolio[ma] = {
                    "nganh": str(r.iloc[1])[:30] if pd.notna(r.iloc[1]) else "",
                    "gia": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                    "lai_lo_pct": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                    "roe": float(r.iloc[4]) if pd.notna(r.iloc[4]) else 0,
                    "pe": float(r.iloc[5]) if pd.notna(r.iloc[5]) else 0,
                    "upside": float(r.iloc[6]) if pd.notna(r.iloc[6]) else 0,
                    "diem_mua": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                    "diem_ban": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                    "ket_luan": str(r.iloc[9])[:30] if pd.notna(r.iloc[9]) else "",
                    "hanh_dong": str(r.iloc[10])[:30] if pd.notna(r.iloc[10]) else "",
                    "ty_trong_ht": float(r.iloc[11]) if pd.notna(r.iloc[11]) else 0,
                    "ty_trong_mt": float(r.iloc[12]) if pd.notna(r.iloc[12]) else 0,
                    "chenh_lech": float(r.iloc[13]) if pd.notna(r.iloc[13]) else 0,
                    "beta": float(r.iloc[14]) if pd.notna(r.iloc[14]) else 0,
                    "var_1": float(r.iloc[15]) if pd.notna(r.iloc[15]) else 0,
                    "co_tuc": float(r.iloc[16]) if pd.notna(r.iloc[16]) else 0,
                    "trang_thai": str(r.iloc[17])[:20] if pd.notna(r.iloc[17]) else "",
                }
            except:
                continue
    return portfolio

def doc_liquid():
    df = pd.read_excel(EXCEL_PATH, sheet_name="💧 Thanh Khoản ADTV", header=None)
    data = {}
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ma = str(r.iloc[0]).strip().upper()
                if not ma or ma == "NAN" or len(ma) > 6:
                    continue
                try:
                    data[ma] = {
                        "adtv": float(r.iloc[1]) if pd.notna(r.iloc[1]) else 0,
                        "gia": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                        "gtgd_ngay": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                    }
                except:
                    continue
            break
    return data

def doc_esg():
    df = pd.read_excel(EXCEL_PATH, sheet_name="🌱 ESG Scoring", header=None)
    data = {}
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Ngành":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ten = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
                if not ten or ten == "nan":
                    continue
                try:
                    e_val = str(r.iloc[1]) if pd.notna(r.iloc[1]) else "0%"
                    s_val = str(r.iloc[2]) if pd.notna(r.iloc[2]) else "0%"
                    g_val = str(r.iloc[3]) if pd.notna(r.iloc[3]) else "0%"
                    data[ten] = {
                        "e": e_val,
                        "s": s_val,
                        "g": g_val,
                        "mo_ta": str(r.iloc[5])[:100] if pd.notna(r.iloc[5]) else "",
                    }
                except:
                    continue
            break
    return data

def doc_stress():
    df = pd.read_excel(EXCEL_PATH, sheet_name="🌪️ Macro Stress", header=None)
    variables = {}
    impact = {}
    for i in range(len(df)):
        r = df.iloc[i]
        v0 = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        if "Lãi suất điều hành" in v0:
            variables["lai_suat"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Tỷ giá" in v0:
            variables["ty_gia"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Lạm phát" in v0:
            variables["lam_phat"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "Giá thép" in v0:
            variables["gia_thep"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
        elif "GDP" in v0:
            variables["gdp"] = str(r.iloc[1]) if pd.notna(r.iloc[1]) else ""
    for i in range(len(df)):
        if str(df.iloc[i].tolist()[0]).strip() == "Mã CP":
            for j in range(i + 1, len(df)):
                r = df.iloc[j]
                ma = str(r.iloc[0]).strip().upper()
                if not ma or ma == "NAN" or len(ma) > 6:
                    continue
                try:
                    impact[ma] = {
                        "nganh": str(r.iloc[1])[:30] if pd.notna(r.iloc[1]) else "",
                        "gia_ht": float(r.iloc[2]) if pd.notna(r.iloc[2]) else 0,
                        "pe_ht": float(r.iloc[3]) if pd.notna(r.iloc[3]) else 0,
                        "tac_dong_ls": str(r.iloc[4])[:20] if pd.notna(r.iloc[4]) else "",
                        "tac_dong_tg": str(r.iloc[5])[:20] if pd.notna(r.iloc[5]) else "",
                        "tac_dong_lp": str(r.iloc[6])[:20] if pd.notna(r.iloc[6]) else "",
                        "pe_stress": float(r.iloc[7]) if pd.notna(r.iloc[7]) else 0,
                        "gia_hop_ly_base": float(r.iloc[8]) if pd.notna(r.iloc[8]) else 0,
                        "gia_hop_ly_stress": float(r.iloc[9]) if pd.notna(r.iloc[9]) else 0,
                        "chenh_lech": str(r.iloc[10])[:20] if pd.notna(r.iloc[10]) else "",
                        "downside": str(r.iloc[11])[:20] if pd.notna(r.iloc[11]) else "",
                        "hanh_dong": str(r.iloc[12])[:50] if pd.notna(r.iloc[12]) else "",
                    }
                except:
                    continue
            break
    return variables, impact

def doc_performance():
    df = pd.read_excel(EXCEL_PATH, sheet_name="📊 Performance", header=None)
    params = {}
    for i in range(len(df)):
        r = df.iloc[i]
        v0 = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        v1 = r.iloc[1] if pd.notna(r.iloc[1]) else None
        v2 = str(r.iloc[2])[:100] if pd.notna(r.iloc[2]) else ""
        if "Lãi suất phi rủi ro" in v0:
            params["Rf"] = float(v1) if v1 else 0.045
        elif "Lợi nhuận VN-Index" in v0:
            params["Rm"] = float(v1) if v1 else 0.082
        elif "Beta danh mục" in v0:
            params["Beta"] = float(v1) if v1 else 1.0
        elif "% Return" in v0:
            params["Rp"] = float(v1) if v1 else 0.168
        elif "Phí giao dịch" in v0:
            params["phi_gd"] = float(v1) if v1 else 0.0015
        elif "Thuế" in v0:
            params["thue"] = float(v1) if v1 else 0.001
    return params

def _safe_load(sheet_name: str, loader, default=None):
    try:
        return loader()
    except Exception as e:
        logger.warning("Sheet '%s' failed to load: %s", sheet_name, e)
        return default if default is not None else {}

DOCS = {
    "live": _safe_load("live", doc_live_price),
    "co_phieu_vn": _safe_load("co_phieu_vn", doc_co_phieu_vn),
    "co_phieu_tg": _safe_load("co_phieu_tg", doc_co_phieu_tg),
    "danh_muc": _safe_load("danh_muc", doc_danh_muc),
    "kpi": _safe_load("kpi", doc_kpi, default={}),
    "liquid": _safe_load("liquid", doc_liquid),
    "esg": _safe_load("esg", doc_esg),
    "performance": _safe_load("performance", doc_performance),
}
_sv, _s = _safe_load("stress", lambda: doc_stress(), default=({}, {}))
DOCS["stress_vars"], DOCS["stress"] = _sv, _s
DOCS["ngay_cap_nhat"] = _NGAY_FILE
_kpi = DOCS.get("kpi", {})
DOCS["danh_sach_portfolio"] = sorted(
    [k for k in _kpi.keys() if k != "NAN"],
    key=lambda x: _kpi[x].get("ty_trong_ht", 0) if x in _kpi else 0,
    reverse=True
) or ["FPT", "MBB", "VCB", "CTR", "MWG", "HPG", "VNM"]

import threading
_DOCS_LOCK = threading.Lock()
def tu_dong_cap_nhat():
    def _reload():
        try:
            with _DOCS_LOCK:
                DOCS["live"] = doc_live_price()
                DOCS["co_phieu_vn"] = doc_co_phieu_vn()
                DOCS["co_phieu_tg"] = doc_co_phieu_tg()
                DOCS["kpi"] = doc_kpi()
                DOCS["liquid"] = doc_liquid()
                DOCS["stress_vars"], DOCS["stress"] = doc_stress()
        except Exception as e:
            logger.warning("Auto-reload failed: %s", e)
    t = threading.Thread(target=_reload, daemon=True)
    t.start()
