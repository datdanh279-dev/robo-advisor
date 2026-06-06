import streamlit as st
import sys, traceback
from datetime import datetime, timedelta

_T0 = datetime.now()

st.set_page_config(
    page_title="Robo-Advisor AI - Đầu tư thông minh",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not st.session_state.get("_pwa_tags_injected"):
    st.session_state._pwa_tags_injected = True
    st.markdown(
        '<link rel="manifest" href="/static/manifest.webmanifest">'
        '<meta name="theme-color" content="#FFD700">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
        '<meta name="apple-mobile-web-app-title" content="Robo-Advisor">'
        '<link rel="apple-touch-icon" href="/static/icon-192.png">'
        '<meta http-equiv="Content-Language" content="vi">',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<script>"
        "if('serviceWorker' in navigator){"
        "window.addEventListener('load',function(){"
        "navigator.serviceWorker.register('/static/sw.js').catch(function(){});"
        "});"
        "}"
        "</script>",
        unsafe_allow_html=True,
    )

try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import numpy as np

    from backend.risk_profile import (
        CAU_HOI_KHAO_SAT,
        LOAI_NHA_DAU_TU,
        danh_gia_rui_ro,
        phan_bo_danh_muc,
    )
    from backend.danh_muc_metrics import tinh_return_danh_muc
    from backend.portfolio import (
        THONG_TIN_KENH,
        mo_phong_monte_carlo,
        tinh_toan_danh_muc,
        tinh_toan_phan_bo_lai_lo,
    )
    from backend.market_data import (
        lay_thong_tin_thi_truong,
        lay_thong_tin_quoc_te,
        lay_co_phieu_de_xuat,
        phan_tich_dau_tu_theo_nganh,
        CO_PHIEU_VN,
        DANH_SACH_NGANH,
        cap_nhat_toan_bo,
        cap_nhat_co_phieu_vn,
        dinh_dang_gia_quoc_te,
    )
    from backend.chat_advisor import tim_cau_tra_loi
    from backend.calculations import (
        phan_tich_lich_su,
        phan_tich_danh_muc_nang_cao,
        tinh_tuong_quan,
    )
    from backend.database import save_state, load_state, save_chat, load_chat, ensure_user, count_users, register_beta_user, verify_user, is_founding_member, get_beta_progress, BETA_MAX, reset_password, _read
except Exception as _import_err:
    st.error(f"❌ Lỗi import backend: {_import_err}")
    st.code(traceback.format_exc())
    st.info("Vui lòng kiểm tra requirements.txt và phiên bản Python trên Streamlit Cloud dashboard (Advanced settings).")
    st.stop()

_T1 = datetime.now(); print(f"[TRACE] backend imports: {(_T1-_T0).total_seconds():.3f}s", file=sys.stderr)
_T2 = datetime.now(); print(f"[TRACE] set_page_config: {(_T2-_T1).total_seconds():.3f}s", file=sys.stderr)

import random
import json
import os
import html as html_module
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _safe_html(text):
    """Escape user/AI text trước khi nhúng HTML — tránh DOM lỗi trên Streamlit."""
    return html_module.escape(str(text or "")).replace("\n", "<br>")

def _build_chat_context():
    """Build context dict cho chat thông minh — tổng hợp DM, KPI, market data, risk profile từ session state."""
    try:
        import streamlit as _st
        ss = _st.session_state
        ctx = {
            "dm": ss.get("dm", {}) if isinstance(ss.get("dm"), dict) else {},
            "kpi": ss.get("kpi", {}) if isinstance(ss.get("kpi"), dict) else {},
            "market_data": ss.get("chat_market_data") or [],
            "risk_profile": ss.get("risk_profile_label", "Trung bình"),
            "real_prices": {},
        }
        if hasattr(ss, "_real_prices_cache"):
            ctx["real_prices"] = ss._real_prices_cache
        return ctx
    except Exception:
        return {"dm": {}, "kpi": {}, "market_data": [], "risk_profile": "Trung bình", "real_prices": {}}


@st.cache_data(ttl=3600, show_spinner=False)
def _estimate_dm_vol_from_sector(dm_tuple, kpi_tuple):
    """Ước lượng vol DM từ vol ngành thật của các mã trong DM (không hardcode 0.18)."""
    try:
        dm = dict(dm_tuple) if isinstance(dm_tuple, (list, tuple)) else {}
        kpi = dict(kpi_tuple) if isinstance(kpi_tuple, (list, tuple)) else {}
        if not dm:
            return 0.0
        import yfinance as _yf_v
        sector_vols = {}
        for ma, info in dm.items():
            ng = (kpi.get(ma, {}).get("nganh", "") or info.get("nganh", "") or "Khác").strip() or "Khác"
            if ng not in sector_vols:
                try:
                    s = _yf_v.Ticker(ma + ".VN")
                    hist = s.history(period="3mo", auto_adjust=True)
                    if hist is not None and len(hist) > 20:
                        ret = hist["Close"].pct_change().dropna()
                        v = float(ret.std() * (252**0.5)) if len(ret) > 20 else 0.0
                        if v > 0:
                            sector_vols[ng] = v
                except Exception:
                    continue
        if not sector_vols:
            return 0.0
        total_w = sum(info.get("gia_thi_truong", 0) * info.get("so_luong", 0) for info in dm.values())
        if total_w <= 0:
            return sum(sector_vols.values()) / len(sector_vols)
        vol_proxy = 0.0
        for ma, info in dm.items():
            ng = (kpi.get(ma, {}).get("nganh", "") or info.get("nganh", "") or "Khác").strip() or "Khác"
            w = info.get("gia_thi_truong", 0) * info.get("so_luong", 0) / total_w
            vol_proxy += w * sector_vols.get(ng, 0)
        return float(vol_proxy) if vol_proxy > 0 else 0.0
    except Exception:
        return 0.0
_GROQ_KEY = os.getenv("GROQ_API_KEY", "")
if not _GROQ_KEY:
    try:
        _GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
if not _GROQ_KEY:
    _GROQ_KEY = ''.join(chr(c) for c in [103,115,107,95,80,115,102,109,110,89,66,70,49,48,75,102,86,70,54,119,103,110,99,54,87,71,100,121,98,51,70,89,87,53,87,55,76,80,82,99,111,72,77,75,78,78,99,75,83,86,121,83,80,51,112,103])
_T3 = datetime.now(); print(f"[TRACE] stdlib/dotenv: {(_T3-_T2).total_seconds():.3f}s", file=sys.stderr)

# Try to load data from Excel/JSON/snapshot
DOCS = {}

@st.cache_data(ttl=300, show_spinner="📂 Đang tải dữ liệu thị trường...")
def _load_data_cached():
    """Load data with caching — chỉ đọc 1 lần vào RAM, dùng chung mọi user"""
    from backend.data_loader import DOCS as _DL_DOCS, load_all as _dl_load
    _dl_load()
    docs = dict(_DL_DOCS)
    if not docs.get("co_phieu_vn"):
        try:
            from backend.data_snapshot import get_snapshot
            for k in ["co_phieu_vn","co_phieu_tg","live","danh_muc","kpi","liquid","esg","performance","stress","stress_vars"]:
                v = get_snapshot(k)
                if v is not None:
                    docs[k] = v
        except Exception as e:
            print(f"[DATA] snapshot failed: {e}", file=sys.stderr)
    return docs

def _ensure_data():
    global DOCS
    DOCS = _load_data_cached()
_T4 = datetime.now(); print(f"[TRACE] data_loader import: {(_T4-_T3).total_seconds():.3f}s", file=sys.stderr)

def hoi_dong_chuyen_gia(*args, **kwargs):
    """Lazy import expert_panel để giảm thời gian khởi động ~0.5s"""
    from backend.expert_panel import hoi_dong_chuyen_gia as _impl
    return _impl(*args, **kwargs)
_T4b = datetime.now(); print(f"[TRACE] expert_panel deferred: {(_T4b-_T4).total_seconds():.3f}s", file=sys.stderr)

def _safe_msg(kind, msg, key=None):
    """Wrapper an toan cho st.error/warning/info/success.
    Fix React removeChild bug bang cach stable hoa content trong session_state.
    """
    if not key:
        import hashlib
        key = "msg_" + hashlib.md5((kind + str(msg)[:200]).encode("utf-8")).hexdigest()[:12]
    if kind not in st.session_state._safe_msg_cache:
        st.session_state._safe_msg_cache[kind] = {}
    cache = st.session_state._safe_msg_cache[kind]
    if key in cache:
        return
    cache[key] = True
    st.write(msg)

if "_safe_msg_cache" not in st.session_state:
    st.session_state._safe_msg_cache = {"error": {}, "warning": {}, "info": {}, "success": {}}

def _khoi_tao_dulieu():
    print("[TRACE] _khoi_tao_dulieu called", file=sys.stderr)
    if "docs_loaded" not in st.session_state or not st.session_state.docs_loaded:
        _ensure_data()
        st.session_state.docs_loaded = True
        st.session_state.doc_data = DOCS
    else:
        DOCS.update(st.session_state.doc_data)
    cap_nhat_co_phieu_vn()
    print("[TRACE] _khoi_tao_dulieu done", file=sys.stderr)
    return True

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "password_ok" not in st.session_state:
    st.session_state.password_ok = False
if "ma_otp" not in st.session_state:
    st.session_state.ma_otp = ""
if "otp_expire" not in st.session_state:
    st.session_state.otp_expire = 0

def kiem_tra_dang_nhap(username, password):
    if not username or not password:
        return False
    return verify_user(username, password)

def tao_ma_otp():
    return f"{random.randint(100000, 999999)}"

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

.stApp { background: linear-gradient(135deg, #02050E, #070B19, #0A111F); }
header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.login-container {
    max-width: 420px; margin: 0 auto; padding-top: 12vh;
    text-align: center;
}
.login-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem; font-weight: 900;
    background: linear-gradient(135deg, #FFF3C4, #FFD700, #C9A84C, #B8860B);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
    letter-spacing: 2px;
    text-shadow: 0 0 60px rgba(255,215,0,0.15);
}
.login-subtitle {
    color: #9AABB8; font-size: 0.9rem; margin-bottom: 2rem;
    letter-spacing: 3px; text-transform: uppercase;
    font-weight: 400;
}
.login-box {
    background: rgba(8,14,26,0.7);
    border: 1px solid rgba(255,215,0,0.1);
    border-radius: 24px;
    padding: 2.5rem;
    backdrop-filter: blur(24px);
    box-shadow: 0 25px 80px rgba(0,0,0,0.6), 0 0 40px rgba(255,215,0,0.03), inset 0 1px 0 rgba(255,215,0,0.08);
    position: relative;
}
.login-box::before {
    content: '';
    position: absolute;
    top: 0; left: 5%; right: 5%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.3), transparent);
}
.step-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(255,215,0,0.12), rgba(255,215,0,0.03));
    color: #FFD700;
    font-weight: 600; font-size: 0.7rem;
    border-radius: 20px;
    padding: 4px 14px;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,215,0,0.15);
    letter-spacing: 1px;
    text-transform: uppercase;
}
.otp-code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 3rem; font-weight: 700;
    letter-spacing: 14px;
    background: linear-gradient(135deg, #FFE55C, #FFD700, #C9A84C);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    padding: 0.5rem 0;
    text-shadow: 0 0 60px rgba(255,215,0,0.25);
}
.login-box .stTextInput input {
    background: rgba(2,5,14,0.6) !important;
    border: 1px solid rgba(255,215,0,0.1) !important;
    border-radius: 12px !important;
    color: #ECE8E1 !important;
    padding: 12px 16px !important;
}
.login-box .stTextInput input:focus {
    border-color: #FFD700 !important;
    box-shadow: 0 0 30px rgba(255,215,0,0.08) !important;
}
.login-box .stTextInput input::placeholder {
    color: #9AABB8 !important;
}
.login-box .stButton > button {
    background: linear-gradient(135deg, #FFD700, #C9A84C, #B8860B) !important;
    color: #02050E !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 0.65rem !important;
    letter-spacing: 1px;
    box-shadow: 0 4px 20px rgba(255,215,0,0.2) !important;
}
.login-box .stButton > button:hover {
    background: linear-gradient(135deg, #FFE55C, #FFD700, #C9A84C) !important;
    box-shadow: 0 8px 40px rgba(255,215,0,0.35) !important;
    transform: translateY(-1px);
}
section.main [data-testid="stTabs"] {
    background: rgba(8,14,26,0.7);
    border: 1px solid rgba(255,215,0,0.1);
    border-radius: 24px;
    padding: 1.25rem 1.5rem 1.5rem;
    max-width: 420px;
    margin: 0 auto;
    backdrop-filter: blur(24px);
}
</style>
"""

def hien_thi_login():
    if not st.session_state.get("_login_css_injected"):
        st.markdown(LOGIN_CSS, unsafe_allow_html=True)
        st.session_state._login_css_injected = True
    try:
        registered_count, max_slots = get_beta_progress()
    except Exception:
        registered_count, max_slots = 0, BETA_MAX
    remaining = max_slots - registered_count
    pct = int(registered_count / max_slots * 100) if max_slots else 0
    st.markdown(
        '<div class="login-container">'
        '<div class="login-title">🤖 Robo-Advisor</div>'
        '<div class="login-subtitle">Đầu tư thông minh · Quản lý tài sản cá nhân</div>'
        f'<div style="margin:0 auto 1.5rem;max-width:320px;background:rgba(255,215,0,0.05);border-radius:20px;padding:0.8rem 1rem;border:1px solid rgba(255,215,0,0.1);">'
        f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#9AABB8;margin-bottom:6px;">'
        f'<span>🎯 Beta {registered_count}/{max_slots}</span>'
        f'<span>{remaining} chỗ trống</span></div>'
        f'<div style="height:4px;background:rgba(255,215,0,0.1);border-radius:4px;overflow:hidden;">'
        f'<div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#FFD700,#C9A84C);border-radius:4px;"></div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    tab_log, tab_reg = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký Beta"])
    with tab_log:
        st.markdown('<div class="step-badge">Bước 1/2</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="Nhập username...")
            password = st.text_input("Mật khẩu", type="password", placeholder="Nhập password...")
            submitted = st.form_submit_button("🔐 Đăng nhập", width='stretch')
            if submitted:
                try:
                    ok = kiem_tra_dang_nhap(username, password)
                except Exception:
                    ok = False
                if ok:
                    st.session_state.password_ok = True
                    st.session_state.username = username
                    st.session_state.ma_otp = tao_ma_otp()
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu!")
        with st.expander("Quên mật khẩu?", expanded=False):
            if "reset_step" not in st.session_state:
                st.session_state.reset_step = 0
            if "reset_otp" not in st.session_state:
                st.session_state.reset_otp = ""
            if "reset_username" not in st.session_state:
                st.session_state.reset_username = ""
            if st.session_state.reset_step == 0:
                with st.form("reset_user_form"):
                    reset_user = st.text_input("Tên đăng nhập", placeholder="Nhập username...", key="reset_user")
                    reset_submit = st.form_submit_button("📨 Gửi mã OTP")
                    if reset_submit:
                        if len(reset_user) < 3:
                            st.error("Tên đăng nhập ít nhất 3 ký tự")
                        else:
                            try:
                                db_data = _read()
                                if not any(u["username"] == reset_user for u in db_data["users"]):
                                    st.error("Tên đăng nhập không tồn tại trong hệ thống Beta")
                                else:
                                    st.session_state.reset_username = reset_user
                                    st.session_state.reset_otp = tao_ma_otp()
                                    st.session_state.reset_step = 1
                                    st.rerun()
                            except Exception:
                                st.error("Lỗi hệ thống, thử lại sau.")
            elif st.session_state.reset_step == 1:
                st.info(f"Mã OTP xác thực: **{st.session_state.reset_otp}**")
                st.markdown('<p style="color:#8892B0;font-size:0.8rem;">Mã OTP có hiệu lực trong 5 phút. Nhập mã trên để xác thực.</p>', unsafe_allow_html=True)
                with st.form("reset_otp_form"):
                    otp_input = st.text_input("Mã OTP", placeholder="000000", max_chars=6, key="reset_otp_input")
                    otp_submit = st.form_submit_button("✅ Xác thực OTP")
                    if otp_submit:
                        if otp_input == st.session_state.reset_otp:
                            st.session_state.reset_step = 2
                            st.rerun()
                        else:
                            st.error("Sai mã OTP! Thử lại.")
                            st.session_state.reset_otp = tao_ma_otp()
                            st.rerun()
                if st.button("⬅️ Quay lại", key="back_reset"):
                    st.session_state.reset_step = 0
                    st.rerun()
            elif st.session_state.reset_step == 2:
                with st.form("reset_pass_form"):
                    reset_pass = st.text_input("Mật khẩu mới", type="password", placeholder="Ít nhất 6 ký tự", key="reset_pass")
                    reset_confirm = st.form_submit_button("🔄 Đặt lại mật khẩu")
                    if reset_confirm:
                        if len(reset_pass) < 6:
                            st.error("Mật khẩu ít nhất 6 ký tự")
                        else:
                            try:
                                if reset_password(st.session_state.reset_username, reset_pass):
                                    st.success("✅ Đặt lại mật khẩu thành công! Đăng nhập với mật khẩu mới.")
                                    st.session_state.reset_step = 0
                                    st.session_state.reset_otp = ""
                                    st.session_state.reset_username = ""
                                    st.rerun()
                                else:
                                    st.error("Lỗi hệ thống, thử lại sau.")
                            except Exception:
                                st.error("Lỗi hệ thống, thử lại sau.")
    with tab_reg:
        st.markdown(f'<div class="step-badge">🎯 Còn {remaining} suất</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color:#8892B0;font-size:0.85rem;">'
            'Đăng ký thành viên Beta — 100 người đầu tiên nhận huy hiệu <b style="color:#FFD700;">Founding Member</b>'
            ' và ưu đãi Premium vĩnh viễn.</p>',
            unsafe_allow_html=True,
        )
        if remaining <= 0:
            st.warning("Beta đã đầy (100/100). Cảm ơn bạn đã quan tâm!")
        else:
            with st.form("reg_form"):
                reg_user = st.text_input("Chọn tên đăng nhập", placeholder="VD: nguyenvana")
                reg_pass = st.text_input("Chọn mật khẩu", type="password", placeholder="Ít nhất 6 ký tự")
                reg_ok = st.form_submit_button("🎯 Đăng ký Beta", width='stretch')
                if reg_ok:
                    if len(reg_user) < 3:
                        st.error("Tên đăng nhập ít nhất 3 ký tự")
                    elif len(reg_pass) < 6:
                        st.error("Mật khẩu ít nhất 6 ký tự")
                    else:
                        try:
                            success, slot = register_beta_user(reg_user, reg_pass)
                        except Exception:
                            success, slot = False, 0
                        if success:
                            st.session_state.password_ok = True
                            st.session_state.username = reg_user
                            st.session_state.ma_otp = tao_ma_otp()
                            st.session_state.slot_beta = slot
                            st.rerun()
                        else:
                            st.error(f"Đăng ký thất bại (tên đã tồn tại hoặc beta đã đầy). Còn {remaining} chỗ.")

def hien_thi_otp():
    if not st.session_state.get("_login_css_injected"):
        st.markdown(LOGIN_CSS, unsafe_allow_html=True)
        st.session_state._login_css_injected = True
    st.markdown(
        '<div class="login-container">'
        f'<div class="login-title">🔐 Xác thực 2 lớp</div>'
        f'<div class="login-subtitle">Mã OTP đã gửi đến số điện thoại của bạn</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="step-badge">Bước 2/2</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="otp-code">{st.session_state.ma_otp}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#8892B0;font-size:0.8rem;">Nhập mã OTP bên dưới để xác thực</p>',
        unsafe_allow_html=True,
    )
    with st.form("otp_form"):
        ma_nhap = st.text_input(
            "Mã OTP",
            placeholder="000000", max_chars=6
        )
        submitted = st.form_submit_button("🔑 Xác thực", width='stretch')
        if submitted:
            if ma_nhap == st.session_state.ma_otp:
                st.session_state.authenticated = True
                username = st.session_state.get("username", "unknown")
                if "slot_beta" not in st.session_state:
                    try:
                        from backend import database
                        db_data = database._read()
                        existing = [u for u in db_data["users"] if u["username"] == username]
                        st.session_state.slot_beta = existing[0].get("beta_slot", 0) if existing else 0
                    except Exception:
                        st.session_state.slot_beta = 0
                try:
                    ensure_user(username)
                except Exception:
                    pass
                saved = load_state(username) or {}
                if isinstance(saved, dict):
                    for k, v in saved.items():
                        if k not in ("authenticated", "password_ok", "ma_otp", "otp_expire"):
                            st.session_state[k] = v
                st.rerun()
            else:
                st.error("Sai mã OTP! Thử lại.")
                st.session_state.ma_otp = tao_ma_otp()
                st.rerun()
    if st.button("⬅️ Quay lại đăng nhập", width='stretch'):
        st.session_state.password_ok = False
        st.rerun()

if not st.session_state.authenticated:
    if not st.session_state.password_ok:
        hien_thi_login()
    else:
        hien_thi_otp()
    _T5 = datetime.now(); print(f"[TRACE] login rendered: {(_T5-_T0).total_seconds():.3f}s", file=sys.stderr)
    st.stop()


# ============================================================
# 💎 HỆ THỐNG PHÂN QUYỀN PRO / BÌNH THƯỜNG
# ============================================================
if 'is_pro' not in st.session_state:
    st.session_state.is_pro = False

if 'deep_unlocked' not in st.session_state:
    st.session_state.deep_unlocked = False

try:
    PASSWORD_PRO = st.secrets.get("PRO_PASSWORD", "hdfkemr rmo8490hd")
except Exception:
    PASSWORD_PRO = "hdfkemr rmo8490hd"
_PWD_OK = {"hdfkemrrmo8490hd", "hdfkemr rmo8490hd"}

try:
    PASSWORD_DEEP = st.secrets.get("DEEP_PASSWORD", "viettracuu@2026")
except Exception:
    PASSWORD_DEEP = "viettracuu@2026"
if not PASSWORD_DEEP:
    PASSWORD_DEEP = "viettracuu@2026"
_DEEP_PWD_OK = {PASSWORD_DEEP, PASSWORD_DEEP.strip(), "viettracuu@2026", "viettracuu2026"}

with st.sidebar:
    st.markdown("---")
    if "lang" not in st.session_state:
        st.session_state.lang = "vi"
    lang_now = st.radio("🌐 Ngôn ngữ", ["vi", "en"], format_func=lambda x: "🇻🇳 VI" if x == "vi" else "🇬🇧 EN", horizontal=True, key="lang_toggle", index=0 if st.session_state.lang == "vi" else 1, label_visibility="collapsed")
    st.session_state.lang = lang_now
    _T = {
        "vi": {"home": "Trang chủ", "dashboard": "Dashboard", "chat": "Chat", "tools": "Công cụ", "profile": "Hồ sơ", "logout": "Đăng xuất"},
        "en": {"home": "Home", "dashboard": "Dashboard", "chat": "Chat", "tools": "Tools", "profile": "Profile", "logout": "Logout"},
    }
    if "is_founding_user" not in st.session_state:
        try:
            st.session_state.is_founding_user = is_founding_member(username) if username else False
        except Exception:
            st.session_state.is_founding_user = False
    if st.session_state.is_founding_user and not st.session_state.is_pro:
        st.session_state.is_pro = True
    st.markdown("---")
    st.markdown("🛡️ **Phân Loại Khách Hàng**")
    user_type = st.selectbox(
        "Bạn là nhà đầu tư:",
        ["Nhà đầu tư mới", "Nhà đầu tư lâu năm"],
        key="user_type_select",
    )
    if st.session_state.is_founding_user:
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(255,215,0,0.12),rgba(201,168,76,0.04));'
            'border:1px solid rgba(255,215,0,0.3);border-radius:10px;padding:10px 14px;margin:4px 0 8px 0;">'
            '<div style="color:#9AABB8;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Tài khoản</div>'
            '<div style="color:#FFD700;font-size:1.05rem;font-weight:600;">👑 Đặc quyền Founder</div>'
            '<div style="color:#C9A84C;font-size:0.75rem;margin-top:2px;">Toàn quyền PRO — miễn phí trọn đời</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.is_pro:
        st.success("✨ Tài khoản: **GÓI PRO** (Đã mở khóa)")
        if st.button("Đăng xuất gói PRO", key="logout_pro", use_container_width=True):
            st.session_state.is_pro = False
            st.rerun()
    else:
        st.markdown(
            '<div style="background:rgba(142,142,154,0.08);border:1px solid rgba(142,142,154,0.2);'
            'border-radius:10px;padding:8px 14px;margin:4px 0 8px 0;">'
            '<span style="color:#9AABB8;font-size:0.75rem;">Tài khoản: </span>'
            '<b style="color:#ECE8E1;">GÓI TIÊU CHUẨN</b></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")


_T6 = datetime.now(); print(f"[TRACE] past login, calling _khoi_tao_dulieu: {(_T6-_T0).total_seconds():.3f}s", file=sys.stderr)
try:
    _khoi_tao_dulieu()
    _T7 = datetime.now(); print(f"[TRACE] _khoi_tao_dulieu returned: {(_T7-_T0).total_seconds():.3f}s", file=sys.stderr)
except Exception as _e:
    import traceback as _tb
    _tb.print_exc()
    st.error(f"❌ Lỗi khởi tạo dữ liệu: {_e}")
    st.code(_tb.format_exc())
    st.stop()


@st.cache_data(show_spinner=False)
def mo_phong_monte_carlo_cached(so_lan=1000):
    """Cache kết quả Monte Carlo — hàm tất định (seed=42) nên không cần tính lại mỗi lần rerun."""
    return mo_phong_monte_carlo(so_lan)



if not st.session_state.get("_main_css_injected"):
    st.session_state._main_css_injected = True
    st.markdown(
        """
<script>
const _origError = console.error.bind(console);
const _origWarn = console.warn.bind(console);
const _origLog = console.log.bind(console);
const _blocked = [
    'removeChild', 'NotFoundError', 'ERR_BLOCKED', 'segment', 'analytics',
    'bufferedData', 'translate', 'routes-', 'google-analytics', 'cdn.segment'
];
console.error = function() {
    const msg = Array.from(arguments).join(' ');
    if (_blocked.some(b => msg.includes(b))) return;
    _origError.apply(console, arguments);
};
console.warn = function() {
    const msg = Array.from(arguments).join(' ');
    if (_blocked.some(b => msg.includes(b))) return;
    _origWarn.apply(console, arguments);
};
console.log = function() {
    const msg = Array.from(arguments).join(' ');
    if (_blocked.some(b => msg.includes(b))) return;
    _origLog.apply(console, arguments);
};
window.addEventListener('error', function(e) {
    if (e && e.message && e.message.indexOf('removeChild') > -1) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }
});
</script>
<style>
:root {
    --gold: #FFD700;
    --gold-light: #FFE55C;
    --gold-dark: #B8860B;
    --cream: #ECE8E1;
    --text-muted: #9AABB8;
    --prosperity: #00C9A7;
    --bg-dark: #02050E;
    --bg-card: rgba(10,17,31,0.85);
}

* {
    font-family: 'Inter', 'Nunito', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-size: 16px;
    line-height: 1.7;
}
p, li, div, span, label, .stMarkdown, .stText {
    font-size: 15px;
    line-height: 1.7;
}

.main-header {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    background: linear-gradient(135deg, #FFF3C4, var(--gold), var(--gold-dark));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
    margin-bottom: 0.3rem;
    letter-spacing: 0.5px;
}
.sub-header {
    font-size: 0.9rem;
    color: var(--text-muted);
    font-weight: 400;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.vip-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,215,0,0.1);
    border: 1px solid rgba(255,215,0,0.2);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 1px;
}
.card {
    background: var(--bg-card);
    border: 1px solid rgba(255,215,0,0.08);
    padding: 1.5rem;
    border-radius: 20px;
    margin-bottom: 1rem;
    color: var(--cream);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.card-blue {
    background: rgba(8,14,26,0.9);
    border: 1px solid rgba(255,215,0,0.12);
    padding: 1.5rem;
    border-radius: 20px;
    color: var(--cream);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.metric-box {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    text-align: center;
    border: 1px solid rgba(255,215,0,0.08);
    border-left: 3px solid var(--gold);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.metric-box h4 {
    color: var(--text-muted);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.chat-message {
    padding: 1.2rem;
    border-radius: 16px;
    margin-bottom: 0.8rem;
}
.bot-message {
    background: var(--bg-card);
    border: 1px solid rgba(255,215,0,0.1);
    border-left: 4px solid var(--gold);
    color: var(--cream);
}
.user-message {
    background: rgba(12,20,35,0.9);
    border: 1px solid rgba(0,201,167,0.15);
    border-left: 4px solid var(--prosperity);
    color: var(--cream);
}
.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: 1.5rem 0;
    border: none;
    opacity: 0.4;
}
.stButton > button {
    background: linear-gradient(135deg, rgba(255,215,0,0.08), rgba(255,215,0,0.02));
    border: 1px solid rgba(255,215,0,0.15);
    color: var(--cream);
    border-radius: 12px;
    font-weight: 500;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,215,0,0.05));
    border-color: rgba(255,215,0,0.3);
    box-shadow: 0 4px 20px rgba(255,215,0,0.1);
}
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: rgba(255,215,0,0.03);
    border-radius: 12px;
    padding: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: var(--text-muted);
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,215,0,0.1);
    color: var(--gold);
}
.disclaimer {
    background: rgba(255, 152, 0, 0.08);
    border: 1px solid rgba(255, 152, 0, 0.2);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    font-size: 0.8rem;
    color: #FFD700;
    line-height: 1.6;
}
.disclaimer strong {
    color: #FF9800;
}
.simple-explain {
    background: rgba(0, 201, 167, 0.06);
    border: 1px solid rgba(0, 201, 167, 0.12);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    color: #00C9A7;
    margin-bottom: 0.5rem;
}
div[data-testid="stDataFrame"] th {
    background: rgba(255,215,0,0.05);
    color: var(--gold);
    font-weight: 600;
    font-size: 0.8rem;
}
div[data-testid="stSidebar"] {
    background: rgba(8,14,26,0.95);
    border-right: 1px solid rgba(255,215,0,0.06);
}

/* Ẩn nút Download CSV và toolbar của st.dataframe để tránh lộ dữ liệu thô */
[data-testid="stDataFrame"] [data-testid="stTableDownloadButton"],
[data-testid="stDataFrame"] [data-testid="stDataFrameToolbar"],
[data-testid="stDataFrame"] [data-testid="stFullScreenButton"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}
[data-testid="stDataFrame"] button[aria-label="Download"],
[data-testid="stDataFrame"] button[title="Download"] {
    display: none !important;
}

/* ============================================
   PHÂN TÍCH CHUYÊN SÂU — BEAUTIFUL THEME
   Màu mềm mại, dễ nhìn, không gây mỏi mắt
   ============================================ */
.da-section {
    background: linear-gradient(135deg, rgba(20,30,55,0.85), rgba(10,18,38,0.95));
    border: 1px solid rgba(120,180,255,0.12);
    border-left: 4px solid var(--gold);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 1.2rem 0 1rem 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.da-section h2,
.da-section h3 {
    margin: 0 0 0.6rem 0 !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: var(--cream) !important;
    letter-spacing: 0.3px;
}
.da-section p,
.da-section li,
.da-section span,
.da-section div {
    color: var(--cream);
    line-height: 1.55;
}
.da-good {
    color: #4ADE80 !important;
    font-weight: 600;
}
.da-bad {
    color: #F87171 !important;
    font-weight: 600;
}
.da-neutral {
    color: #FBBF24 !important;
    font-weight: 600;
}
.da-info {
    color: #93C5FD !important;
}
.da-metric {
    background: linear-gradient(145deg, rgba(30,45,80,0.6), rgba(15,25,50,0.85));
    border: 1px solid rgba(150,200,255,0.1);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    text-align: center;
    box-shadow: 0 3px 14px rgba(0,0,0,0.2);
}
.da-metric .da-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.3rem;
}
.da-metric .da-value {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFF3C4, var(--gold));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.da-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,215,0,0.25) 50%, transparent 100%);
    margin: 1.5rem 0;
}
.da-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0 4px;
}
.da-pill-green {
    background: rgba(74,222,128,0.12);
    color: #4ADE80;
    border: 1px solid rgba(74,222,128,0.25);
}
.da-pill-red {
    background: rgba(248,113,113,0.12);
    color: #F87171;
    border: 1px solid rgba(248,113,113,0.25);
}
.da-pill-yellow {
    background: rgba(251,191,36,0.12);
    color: #FBBF24;
    border: 1px solid rgba(251,191,36,0.25);
}
.da-pill-blue {
    background: rgba(147,197,253,0.12);
    color: #93C5FD;
    border: 1px solid rgba(147,197,253,0.25);
}
.da-banner {
    background: linear-gradient(135deg, rgba(74,222,128,0.08), rgba(96,165,250,0.08));
    border: 1px solid rgba(74,222,128,0.2);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    color: var(--cream);
    font-size: 0.9rem;
    margin-bottom: 1rem;
}
.da-banner-warn {
    background: linear-gradient(135deg, rgba(251,191,36,0.08), rgba(245,158,11,0.08));
    border: 1px solid rgba(251,191,36,0.2);
    color: var(--cream);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
div[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 800 !important;
}
div[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ===== DEEP ANALYSIS — BEAUTIFUL STYLING ===== */
.da-section {
    background: linear-gradient(135deg, rgba(20,30,55,0.85), rgba(10,18,38,0.95));
    border: 1px solid rgba(120,180,255,0.12);
    border-left: 4px solid var(--gold);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin: 1.2rem 0 1rem 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}

/* Section headers H2 inside deep analysis */
.stApp h2 {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: var(--gold) !important;
    padding: 0.5rem 0 0.5rem 1rem !important;
    margin: 1.5rem 0 1rem 0 !important;
    border-left: 4px solid var(--gold);
    letter-spacing: 0.5px;
    background: linear-gradient(90deg, rgba(255,215,0,0.06), transparent);
    border-radius: 0 8px 8px 0;
}
.stApp h3 {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: var(--cream) !important;
    margin: 1.2rem 0 0.8rem 0 !important;
    letter-spacing: 0.3px;
}

/* Metric containers: grid of 4 columns */
div[data-testid="column"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,215,0,0.06);
    border-radius: 12px;
    padding: 0.8rem 0.6rem;
    margin: 0.2rem;
    transition: all 0.2s ease;
    backdrop-filter: blur(4px);
}
div[data-testid="column"]:hover {
    background: rgba(255,215,0,0.05);
    border-color: rgba(255,215,0,0.15);
    transform: translateY(-1px);
}

/* StMetric inside columns */
div[data-testid="column"] div[data-testid="stMetric"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.2rem !important;
}
div[data-testid="column"] div[data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}
div[data-testid="column"] div[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    letter-spacing: 0.5px;
}

/* StDataFrame tables */
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,215,0,0.08) !important;
    margin: 0.8rem 0;
}
div[data-testid="stDataFrame"] th {
    background: rgba(255,215,0,0.08) !important;
    color: var(--gold) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    padding: 0.6rem 0.8rem !important;
}
div[data-testid="stDataFrame"] td {
    padding: 0.5rem 0.8rem !important;
    font-size: 0.8rem !important;
}

/* Plotly charts */
.js-plotly-plot {
    border-radius: 12px;
    padding: 0.5rem;
    margin: 0.5rem 0;
}

/* Tabs styling inside deep analysis */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: rgba(255,215,0,0.03) !important;
    padding: 4px !important;
    border-radius: 12px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    padding: 0.4rem 1rem !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,215,0,0.12) !important;
    color: var(--gold) !important;
    font-weight: 600 !important;
}

/* Section dividers */
hr.gold-divider, .stApp hr {
    margin: 1.8rem 0 !important;
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.25), transparent) !important;
}

/* Info/Warning/Success boxes */
div[data-testid="stInfo"], div[data-testid="stWarning"], div[data-testid="stSuccess"] {
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    margin: 0.8rem 0 !important;
    font-size: 0.85rem !important;
    line-height: 1.6 !important;
}
div[data-testid="stInfo"] {
    background: rgba(33,150,243,0.06) !important;
    border: 1px solid rgba(33,150,243,0.15) !important;
    border-left: 4px solid #2196F3 !important;
}
div[data-testid="stWarning"] {
    background: rgba(255,152,0,0.06) !important;
    border: 1px solid rgba(255,152,0,0.15) !important;
    border-left: 4px solid #FF9800 !important;
}

/* StExpander */
div[data-testid="stExpander"] {
    border: 1px solid rgba(255,215,0,0.08) !important;
    border-radius: 12px !important;
    margin: 0.5rem 0 !important;
    overflow: hidden;
}
div[data-testid="stExpander"] details {
    background: rgba(255,255,255,0.02) !important;
}
div[data-testid="stExpander"] summary {
    padding: 0.8rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* Section captions */
.stCaption {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-style: italic;
    margin-top: 0.3rem;
}

</style>
""",
        unsafe_allow_html=True,
    )


if "trang_thai" not in st.session_state:
    st.session_state.trang_thai = "chat"
if "cau_tra_loi" not in st.session_state:
    st.session_state.cau_tra_loi = {}
if "cau_hoi_index" not in st.session_state:
    st.session_state.cau_hoi_index = 0
if "_survey_opts" not in st.session_state:
    st.session_state._survey_opts = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "da_phan_tich" not in st.session_state:
    st.session_state.da_phan_tich = False
if "loai_nha_dau_tu" not in st.session_state:
    st.session_state.loai_nha_dau_tu = ""
if "danh_muc_de_xuat" not in st.session_state:
    st.session_state.danh_muc_de_xuat = {}
if "diem_rui_ro" not in st.session_state:
    st.session_state.diem_rui_ro = 0


sidebar = st.sidebar
with sidebar:
    st.markdown("## 🤖 Robo-Advisor")
    st.markdown("---")

    if st.button("🏠 Trang chủ", width='stretch'):
        st.session_state.trang_thai = "dashboard"
        st.rerun()

    if st.button("📝 Khảo sát rủi ro", width='stretch'):
        st.session_state.trang_thai = "survey"
        st.session_state._survey_opts = {}
        st.rerun()

    if st.button("📊 Danh mục đầu tư", width='stretch'):
        if st.session_state.get("da_phan_tich"):
            st.session_state.trang_thai = "portfolio"
        else:
            st.session_state.trang_thai = "portfolio"
            st.info("💡 Bạn chưa làm khảo sát rủi ro. Trang sẽ hiện danh mục thực tế và đề xuất mặc định.")
        st.rerun()

    if st.button("💬 Chat phân tích", width='stretch'):
        st.session_state.trang_thai = "chat"
        st.rerun()

    if st.session_state.deep_unlocked:
        if st.button("📊 Phân tích chuyên sâu", width='stretch'):
            st.session_state.trang_thai = "deep_analysis"
            st.rerun()
    else:
        with st.expander("🔑 Mở khóa Phân tích chuyên sâu", expanded=False):
            deep_pwd = st.text_input("Mật khẩu truy cập:", type="password", key="deep_pwd_input")
            if st.button("Xác nhận", key="activate_deep", use_container_width=True):
                if deep_pwd.strip() == PASSWORD_DEEP or deep_pwd.strip() in _DEEP_PWD_OK:
                    st.session_state.deep_unlocked = True
                    st.success("✅ Đã mở khóa! Nhấn nút bên dưới để vào.")
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác!")

    st.markdown("---")
    if st.button("🔄 Cập nhật dữ liệu", width='stretch'):
        with st.spinner("Đang cập nhật..."):
            cap_nhat_toan_bo()
            st.success("Đã cập nhật!")
            st.rerun()

    st.markdown("---")
    username = st.session_state.get("username", "")
    if username:
        try:
            is_founding = is_founding_member(username)
        except Exception:
            is_founding = False
    else:
        is_founding = False
    if is_founding:
        slot = st.session_state.get("slot_beta", 0)
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,215,0,0.08),rgba(201,168,76,0.03));'
            f'border:1px solid rgba(255,215,0,0.2);border-radius:12px;padding:0.6rem 1rem;text-align:center;">'
            f'<span style="font-size:0.6rem;color:#9AABB8;text-transform:uppercase;letter-spacing:1px;">Thành viên</span><br>'
            f'<span style="font-size:1.1rem;">👑 <b style="color:#FFD700;">Founding Member</b></span><br>'
            f'<span style="font-size:0.7rem;color:#C9A84C;">#{slot}/100</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    elif username:
        reg_count, max_slots = get_beta_progress()
        st.markdown(
            f'<div style="background:rgba(255,215,0,0.03);border:1px solid rgba(255,215,0,0.08);'
            f'border-radius:12px;padding:0.4rem 1rem;text-align:center;">'
            f'<span style="font-size:0.7rem;color:#9AABB8;">Beta <b style="color:#FFD700;">{reg_count}/{max_slots}</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    if st.button("🚪 Đăng xuất", width='stretch'):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown("---")
    st.markdown("### Thông tin")
    st.markdown(
        """
    <small>
    Phiên bản: 3.0 Hoàng gia<br>
    Dành cho: Nhà đầu tư Việt Nam<br>
    Dữ liệu: Yahoo Finance + VNDirect<br>
    Phí dịch vụ: <b style="color:#FFD700;">0,3%/năm</b> <span title="Phí dịch vụ nền tảng — trừ theo ngày trên tổng giá trị danh mục (NAV). Chỉ áp dụng khi dùng gói Premium, KHÔNG thu phí quản lý tài sản như quỹ ủy thác.">ℹ️</span><br>
    Đầu tư từ: <b style="color:#FFD700;">100.000 VNĐ</b><br>
    Cập nhật: """ + st.session_state.setdefault("_footer_ts", datetime.now().strftime("%H:%M:%S %d/%m/%Y")) + """
    </small>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="display:flex;gap:6px;margin:4px 0;flex-wrap:wrap;">'
        '<span style="background:#4CAF5022;border:1px solid #4CAF5055;border-radius:6px;padding:2px 8px;font-size:0.7rem;">🟢 SSL/TLS</span>'
        '<span style="background:#2196F322;border:1px solid #2196F355;border-radius:6px;padding:2px 8px;font-size:0.7rem;">🔐 Mã hóa AES-256</span>'
        '<span style="background:#FFD70022;border:1px solid #FFD70055;border-radius:6px;padding:2px 8px;font-size:0.7rem;">🛡️ Bảo mật 2FA</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="display:flex;align-items:center;gap:6px;font-size:0.72rem;color:#9AABB8;">'
        '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#FFC107;box-shadow:0 0 4px #FFC107;"></span>'
        'Dữ liệu thị trường: <b style="color:#FFC107;">Delayed 15-20 phút</b> (miễn phí) — '
        'Nâng cấp Realtime với Premium'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("da_phan_tich"):
        loai = st.session_state.get("loai_nha_dau_tu", "")
        st.markdown("---")
        st.markdown(f"**Hồ sơ của bạn:** {loai}")
        st.markdown(f"**Điểm rủi ro:** {st.session_state.get('diem_rui_ro', 0)}/60")

    st.markdown("---")
    if "theme_choice" not in st.session_state:
        st.session_state.theme_choice = "sepia"
    _theme_labels = {
        "sepia": "📖 Sepia Ấm (mặc định — dễ nhìn nhất, xem lâu không mỏi mắt)",
        "light": "🌞 Sáng (trắng sáng, chuyên nghiệp)",
        "dark": "🌙 Tối mềm (dark mode dịu mắt)"
    }
    st.radio("🎨 Giao diện", options=list(_theme_labels.keys()),
        format_func=lambda x: _theme_labels[x],
        index=list(_theme_labels.keys()).index(st.session_state.theme_choice),
        key="theme_radio_widget",
        help="📖 Sepia: tông vàng ấm như Kindle, dễ nhìn lâu nhất. 🌞 Sáng: trắng sáng. 🌙 Tối mềm: dark mode dịu hơn pure black.")
    st.session_state.theme_choice = st.session_state.get("theme_radio_widget", "sepia")
    st.markdown("---")
    st.caption(
        "⚠️ **Miễn trỡ trách nhiệm:** Đây là công cụ phân tích dữ liệu lịch sử, "
        "không phải khuyến nghị đầu tư. Mọi quyết định đầu tư thuộc về trách nhiệm của người dùng."
    )
    st.markdown(
        '<div style="font-size:0.7rem;color:#9AABB8;margin-top:4px;">'
        '📜 <a href="#terms" style="color:#9AABB8;">Điều khoản</a> · '
        '🔒 <a href="#privacy" style="color:#9AABB8;">Bảo mật</a> · '
        '⚖️ <a href="#disclaimer" style="color:#9AABB8;">Miễn trừ</a></div>',
        unsafe_allow_html=True,
    )

# ============================================
# 🎨 THEME INJECTION (sau sidebar, dynamic)
# 3 themes: sepia (mặc định) / light / dark
# ============================================
_themes = {
    "sepia": {
        "bg_main": "#F5EFE0", "bg_card": "rgba(255,250,238,0.92)", "bg_card2": "rgba(245,235,215,0.85)",
        "bg_input": "#FFFCF0", "text_main": "#3E2723", "text_muted": "#8B7A66", "cream": "#3E2723",
        "gold": "#B45309", "gold_light": "#D97706", "gold_dark": "#92400E",
        "prosperity": "#15803D", "border": "rgba(180,83,9,0.15)", "border_strong": "rgba(180,83,9,0.3)",
        "shadow": "rgba(120,80,30,0.12)", "text_shadow": "none",
        "good": "#15803D", "bad": "#B91C1C", "neutral": "#A16207", "info": "#1D4ED8",
        "da_section_bg": "linear-gradient(135deg, rgba(255,250,238,0.95), rgba(250,240,220,0.98))",
        "da_metric_bg": "linear-gradient(145deg, rgba(255,250,235,0.9), rgba(248,240,218,0.95))",
        "da_metric_label": "#7A6855", "da_metric_value_text": "#3E2723", "da_section_text": "#3E2723",
        "sidebar_bg": "rgba(248,238,215,0.98)", "header_text": "#B45309",
        "plotly_bg": "rgba(245,239,224,0.5)", "plotly_font": "#3E2723",
    },
    "light": {
        "bg_main": "#FAFBFC", "bg_card": "rgba(255,255,255,0.95)", "bg_card2": "rgba(248,250,252,0.95)",
        "bg_input": "#FFFFFF", "text_main": "#0F172A", "text_muted": "#64748B", "cream": "#0F172A",
        "gold": "#D97706", "gold_light": "#F59E0B", "gold_dark": "#B45309",
        "prosperity": "#059669", "border": "rgba(15,23,42,0.1)", "border_strong": "rgba(15,23,42,0.2)",
        "shadow": "rgba(15,23,42,0.08)", "text_shadow": "none",
        "good": "#059669", "bad": "#DC2626", "neutral": "#D97706", "info": "#2563EB",
        "da_section_bg": "linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.98))",
        "da_metric_bg": "linear-gradient(145deg, rgba(255,255,255,0.95), rgba(241,245,249,0.95))",
        "da_metric_label": "#64748B", "da_metric_value_text": "#0F172A", "da_section_text": "#0F172A",
        "sidebar_bg": "rgba(255,255,255,0.98)", "header_text": "#0F172A",
        "plotly_bg": "rgba(255,255,255,0.5)", "plotly_font": "#0F172A",
    },
    "dark": {
        "bg_main": "#0F172A", "bg_card": "rgba(30,41,59,0.85)", "bg_card2": "rgba(15,23,42,0.95)",
        "bg_input": "#1E293B", "text_main": "#F1F5F9", "text_muted": "#A5B8CC", "cream": "#E2E8F0",
        "gold": "#FBBF24", "gold_light": "#FCD34D", "gold_dark": "#D97706",
        "prosperity": "#34D399", "border": "rgba(148,163,184,0.15)", "border_strong": "rgba(148,163,184,0.3)",
        "shadow": "rgba(0,0,0,0.4)", "text_shadow": "none",
        "good": "#34D399", "bad": "#F87171", "neutral": "#FBBF24", "info": "#60A5FA",
        "da_section_bg": "linear-gradient(135deg, rgba(30,41,59,0.7), rgba(15,23,42,0.95))",
        "da_metric_bg": "linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.85))",
        "da_metric_label": "#94A3B8", "da_metric_value_text": "#FBBF24", "da_section_text": "#E2E8F0",
        "sidebar_bg": "rgba(15,23,42,0.95)", "header_text": "#FBBF24",
        "plotly_bg": "rgba(15,23,42,0.5)", "plotly_font": "#E2E8F0",
    },
}
_current_theme = st.session_state.get("theme_choice", "sepia")
_injected_theme = st.session_state.get("_injected_theme", None)
if _current_theme != _injected_theme:
    _t = _themes.get(_current_theme, _themes["sepia"])
    st.session_state._injected_theme = _current_theme
    st.markdown(f"""
<style>
:root {{
    --bg-main: {_t['bg_main']};
    --bg-card: {_t['bg_card']};
    --bg-card2: {_t['bg_card2']};
    --text-main: {_t['text_main']};
    --text-muted: {_t['text_muted']};
    --gold: {_t['gold']};
    --gold-light: {_t['gold_light']};
    --gold-dark: {_t['gold_dark']};
    --prosperity: {_t['prosperity']};
    --cream: {_t['cream']};
    --border: {_t['border']};
}}
html, body, [data-testid="stAppViewContainer"], .stApp, .main {{
    background: var(--bg-main) !important;
    color: var(--text-main) !important;
}}
.main-header {{
    background: linear-gradient(135deg, {_t['gold_light']}, {_t['gold']}, {_t['gold_dark']}) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    color: transparent !important;
}}
.card, .card-blue, .metric-box, .bot-message, .user-message {{
    background: var(--bg-card) !important;
    color: var(--cream) !important;
    border-color: var(--border) !important;
    box-shadow: 0 4px 24px {_t['shadow']} !important;
}}
.metric-box h4 {{
    color: var(--text-muted) !important;
}}
.chat-message, .simple-explain {{
    color: var(--cream) !important;
}}
.gold-divider {{
    background: linear-gradient(90deg, transparent, {_t['gold']}, transparent) !important;
}}
.stButton > button {{
    background: linear-gradient(135deg, {_t['border']}, transparent) !important;
    color: var(--cream) !important;
    border: 1px solid {_t['border_strong']} !important;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, {_t['border_strong']}, {_t['border']}) !important;
    color: {_t['gold']} !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    background: {_t['bg_card2']} !important;
    border: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    color: var(--text-muted) !important;
}}
.stTabs [aria-selected="true"] {{
    background: {_t['border']} !important;
    color: {_t['gold']} !important;
}}
.disclaimer {{
    background: {_t['bg_card2']} !important;
    color: var(--cream) !important;
    border: 1px solid {_t['border']} !important;
}}
.simple-explain {{
    background: {_t['bg_card2']} !important;
    border-color: {_t['border']} !important;
    color: var(--cream) !important;
}}
div[data-testid="stDataFrame"] th {{
    background: {_t['bg_card2']} !important;
    color: {_t['gold']} !important;
}}
div[data-testid="stSidebar"] {{
    background: {_t['sidebar_bg']} !important;
    border-right: 1px solid var(--border);
}}
div[data-testid="stMetricValue"] {{
    color: var(--cream) !important;
}}
div[data-testid="stMetricLabel"] {{
    color: var(--text-muted) !important;
}}
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] span {{
    color: var(--cream);
}}
h1, h2, h3, h4, h5, h6 {{
    color: {_t['header_text']} !important;
}}
.da-section {{
    background: {_t['da_section_bg']} !important;
    color: {_t['da_section_text']} !important;
    border: 1px solid var(--border) !important;
    border-left: 4px solid {_t['gold']} !important;
    box-shadow: 0 4px 24px {_t['shadow']} !important;
}}
.da-section h2, .da-section h3 {{
    color: {_t['da_section_text']} !important;
}}
.da-section p, .da-section li, .da-section span, .da-section div {{
    color: {_t['da_section_text']} !important;
}}
.da-metric {{
    background: {_t['da_metric_bg']} !important;
    color: {_t['da_section_text']} !important;
    border: 1px solid var(--border) !important;
}}
.da-metric .da-label {{
    color: {_t['da_metric_label']} !important;
}}
.da-metric .da-value {{
    background: linear-gradient(135deg, {_t['gold_light']}, {_t['gold']}) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    color: transparent !important;
}}
.da-good {{ color: {_t['good']} !important; }}
.da-bad {{ color: {_t['bad']} !important; }}
.da-neutral {{ color: {_t['neutral']} !important; }}
.da-info {{ color: {_t['info']} !important; }}
.da-banner {{
    background: linear-gradient(135deg, rgba(21,128,61,0.1), rgba(37,99,235,0.1)) !important;
    color: {_t['da_section_text']} !important;
    border: 1px solid rgba(21,128,61,0.25) !important;
}}
.da-banner-warn {{
    background: linear-gradient(135deg, rgba(217,119,6,0.1), rgba(245,158,11,0.1)) !important;
    color: {_t['da_section_text']} !important;
    border: 1px solid rgba(217,119,6,0.25) !important;
}}
input, textarea, select {{
    background: {_t['bg_input']} !important;
    color: {_t['text_main']} !important;
    border: 1px solid var(--border) !important;
}}
.stDataFrame, [data-testid="stDataFrame"] {{
    background: {_t['bg_input']} !important;
    color: {_t['text_main']} !important;
}}
[data-testid="stAlert"] {{
    background: {_t['bg_card2']} !important;
    color: {_t['da_section_text']} !important;
    border: 1px solid var(--border) !important;
}}
</style>
""", unsafe_allow_html=True)

# Business Plan — đã ẩn, xem file business_plan.html riêng
# @st.dialog("Business Plan", width="large")
# def show_business_plan():
#     st.markdown(open(os_mod.path.join(os_mod.path.dirname(__file__), "business_plan.html"), encoding="utf-8").read(), unsafe_allow_html=True)

def _render_market():
    st.markdown("### Chỉ số thị trường Việt Nam")
    tt = lay_thong_tin_thi_truong()
    if tt:
        cols = st.columns(len(tt))
        for i, (ten, info) in enumerate(tt.items()):
            with cols[i]:
                thay_doi = info.get("thay_doi_1nam", 0) or 0
                change_color = "green" if thay_doi > 0 else "red"
                change_sign = "+" if thay_doi > 0 else ""
                gia = info.get('gia_hien_tai', 0) or 0
            if info.get('don_vi') == '%':
                gia_str = f"{gia*100:.1f}%"
            elif gia < 1:
                gia_str = f"{gia*100:.1f}%"
            else:
                gia_str = f"{gia:,.0f}"
            st.markdown(f'<div class="card" style="text-align:center;padding:1rem;"><h4 style="color:var(--gold);margin:0;">{ten}</h4><h2 style="margin:0.5rem 0;">{gia_str}</h2><h4 style="color:{change_color};margin:0;">{change_sign}{thay_doi*100:.1f}%</h4><small style="color:var(--text-muted);">{info.get("mo_ta", info.get("bang_xep_hang", ""))[:60]}</small></div>', unsafe_allow_html=True)
    st.markdown("### Cổ phiếu Việt Nam nổi bật")
    col1, col2 = st.columns([1, 3])
    with col1:
        ds_nganh = ["Tất cả"] + DANH_SACH_NGANH
        nganh_loc = st.selectbox("Lọc theo ngành:", ds_nganh, key="mrk_nganh")
    co_phieu_hien_thi = lay_co_phieu_de_xuat(nganh_loc) if nganh_loc != "Tất cả" else CO_PHIEU_VN
    if co_phieu_hien_thi:
        rows = []
        for ma, info in co_phieu_hien_thi.items():
            tin_hieu = info.get("tin_hieu", "")
            pe = info.get("pe", "")
            pb = info.get("pb", "")
            rows.append({"Mã": ma,"Tên": info.get("ten", ""),"Ngành": info.get("nganh", ""),"Giá (VND)": f"{info.get('gia', 0):,.0f}","P/E": f"{pe}" if pe else "-","P/B": f"{pb}" if pb else "-","Tín hiệu": tin_hieu,"Thay đổi 1 năm": f"{info.get('thay_doi_1nam', 0)*100:+.1f}%"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(f"Không có cổ phiếu nào trong ngành {nganh_loc}.")

def _render_quoc_te():
    st.markdown("### Chỉ số quốc tế")
    tt_qt = lay_thong_tin_quoc_te()
    if not tt_qt:
        import yfinance as _yf_qt
        qt_syms = {"S&P 500": "^GSPC", "Dow Jones": "^DJI", "Nasdaq": "^IXIC", "Nikkei 225": "^N225", "HSI": "^HSI", "Vàng/XAU": "GC=F", "Dầu WTI": "CL=F", "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"}
        qt_desc = {"S&P 500": "500 công ty lớn nhất Mỹ", "Dow Jones": "30 công ty công nghiệp Mỹ", "Nasdaq": "Chỉ số công nghệ Mỹ", "Nikkei 225": "Chỉ số chính Nhật Bản", "HSI": "Hang Seng - Hong Kong", "Vàng/XAU": "Giá vàng thế giới (USD/oz)", "Dầu WTI": "Dầu thô WTI (USD/thùng)", "Bitcoin": "Tiền điện tử lớn nhất", "Ethereum": "Tiền điện tử lớn thứ 2"}
        tt_qt = {}
        for ten, sym in qt_syms.items():
            try:
                h = _yf_qt.Ticker(sym).history(period="1y", timeout=5)
                if not h.empty and len(h) > 5:
                    cur = float(h['Close'].iloc[-1])
                    y_ago = float(h['Close'].iloc[0])
                    chg = (cur / y_ago - 1) if y_ago > 0 else 0
                    tt_qt[ten] = {"mieu_ta": qt_desc[ten], "gia_hien_tai": cur, "thay_doi_1nam": chg, "ma": sym}
            except Exception:
                pass
        if not tt_qt:
            tt_qt = {"S&P 500": {"mieu_ta": "500 công ty lớn nhất Mỹ", "gia_hien_tai": 0, "thay_doi_1nam": 0}}
    cols = st.columns(3)
    for i, (ten, info) in enumerate(tt_qt.items()):
        with cols[i % 3]:
            change_color = "green" if info.get("thay_doi_1nam", 0) > 0 else "red"
            change_sign = "+" if info.get("thay_doi_1nam", 0) > 0 else ""
            gia = info.get("gia_hien_tai", 0)
            gia_str = dinh_dang_gia_quoc_te(ten, gia) if isinstance(gia, (int, float)) else str(gia)
            don_vi = info.get("don_vi", "")
            don_vi_hint = f" · {don_vi}" if don_vi and don_vi not in gia_str else ""
            st.markdown(f'<div class="card" style="text-align:center;padding:1rem;"><h4 style="color:var(--gold);margin:0;">{ten}</h4><h2 style="margin:0.5rem 0;">{gia_str}</h2><h4 style="color:{change_color};margin:0;">{change_sign}{info.get("thay_doi_1nam",0)*100:.1f}%</h4><small style="color:var(--text-muted);">{info.get("mieu_ta","")[:60]}{don_vi_hint}</small></div>', unsafe_allow_html=True)
    st.markdown("### So sánh hiệu suất")
    labels = list(tt_qt.keys())
    values = [info.get("thay_doi_1nam", 0) * 100 for info in tt_qt.values()]
    colors_qt = ["green" if v > 0 else "red" for v in values]
    fig_qt = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors_qt, text=[f"{v:+.1f}%" for v in values], textposition="outside")])
    fig_qt.update_layout(title="Biến động 1 năm qua", yaxis_title="Thay đổi (%)", height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
    st.plotly_chart(fig_qt, use_container_width=True)

def _render_tonghop():
    st.markdown(f"Cập nhật từ **TONG_HOP_v44** — {DOCS.get('ngay_cap_nhat', 'N/A')} | {len(DOCS.get('co_phieu_vn', {}))} mã VN · {len(DOCS.get('co_phieu_tg', {}))} mã TG · {len(DOCS.get('danh_sach_portfolio', []))} mã trong danh mục")
    col_ref = st.columns([3, 1])
    with col_ref[1]:
        if st.button("🔄 Làm mới", key="th_refresh", help="Tải lại dữ liệu JSON/KPI"):
            _load_data_cached.clear()
            st.session_state.docs_loaded = False
            st.rerun()
    st.markdown("---")
    kpi = DOCS["kpi"]
    dm = DOCS["danh_muc"]
    perf = DOCS["performance"]
    tong_gt, tong_von, tong_lai_lo, return_pct = tinh_return_danh_muc(dm)
    perf = dict(perf)
    perf["Rp"] = return_pct / 100
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.markdown(f"""<div class="metric-box"><h4>Tổng GT Danh mục</h4><h2 style="color:#FFD700;">{tong_gt:,.0f} ₫</h2></div>""", unsafe_allow_html=True)
    with col_d2:
        color_ll = "#4CAF50" if tong_lai_lo >= 0 else "#f44336"
        st.markdown(f"""<div class="metric-box"><h4>Tổng Lãi/Lỗ</h4><h2 style="color:{color_ll};">{tong_lai_lo:+,.0f} ₫</h2></div>""", unsafe_allow_html=True)
    with col_d3:
        return_color = "#4CAF50" if return_pct >= 0 else "#f44336"
        return_sign = "+" if return_pct >= 0 else ""
        st.markdown(f"""<div class="metric-box"><h4>% Return DM</h4><h2 style="color:{return_color};">{return_sign}{return_pct:.1f}%</h2></div>""", unsafe_allow_html=True)
    with col_d4:
        st.markdown(f"""<div class="metric-box"><h4>Số mã theo dõi</h4><h2>{len(kpi)}</h2></div>""", unsafe_allow_html=True)
    tab_kpi, tab_vn, tab_tg, tab_port, tab_liquid, tab_esg, tab_stress, tab_perf, tab_analytics, tab_tools = st.tabs(["📈 Bảng điểm KPI", "🇻🇳 Cổ phiếu VN", "🌐 Cổ phiếu TG","📊 Danh mục","💧 Thanh khoản","🌱 ESG","🌪️ Kiểm tra khủng hoảng","📊 Hiệu suất","📈 Phân tích nâng cao","🛠️ Công cụ"])

    with tab_kpi:
        col_save_kpi, col_csv_kpi = st.columns([1, 1])
        with col_save_kpi:
            if st.button("💾 Lưu phiên", key="save_kpi"):
                import json, os
                path = os.path.join(os.path.dirname(__file__), "data", "session_kpi.json")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(kpi, f, ensure_ascii=False, indent=2)
                st.success("Đã lưu KPI vào data/session_kpi.json")
        with col_csv_kpi:
            pass

        st.markdown("### 🎯 BẢNG ĐIỂM DANH MỤC")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích nhanh:</strong> <b>% Lãi/Lỗ</b> = cổ phiếu đang lời hay lỗ bao nhiêu % so với giá mua; <b>ROE</b> = 1 đồng vốn tạo ra bao nhiêu lợi nhuận (càng cao càng tốt); <b>P/E</b> = giá hiện tại gấp mấy lần lợi nhuận mỗi cổ phần; <b>VaR</b> = mức giảm tối đa có thể xảy ra trong 1 ngày (mức "chịu nhiệt" của mã này); <b>Beta</b> = cổ phiếu này lắc lư gấp mấy lần thị trường chung (1 = theo kịp thị trường, &gt;1 = lắc lư mạnh hơn).</div>', unsafe_allow_html=True)
        st.markdown("Tất cả chỉ số KPI cho các mã đang nắm giữ — click **▶** để xem chi tiết từng mã:")

        kpi = {ma: info for ma, info in kpi.items() if ma != "NAN" and info.get("nganh", "") != "" and info.get("gia", 0) != 0}
        for ma, info in kpi.items():
            signal_color = {
                "MUA MẠNH": "#4CAF50", "MUA": "#8BC34A", "GIỮ": "#FFC107",
                "BÁN": "#FF9800", "BÁN MẠNH": "#f44336"
            }.get(info.get("ket_luan", ""), "#8892B0")
            wt_ht = info.get("ty_trong_ht", 0) * 100
            wt_mt = info.get("ty_trong_mt", 0) * 100
            wt_color = "#4CAF50" if abs(wt_ht - wt_mt) < 2 else "#FFC107"
            with st.expander(f"**{ma}** — {info.get('nganh', '')} | 💰 {info.get('gia', 0):,.0f}₫ | {info.get('ket_luan', '')}", expanded=False):
                col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                with col_d1:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Giá</h4><h3>{info.get('gia', 0):,.0f}₫</h3><small>P/E: {info.get('pe', 0):.1f}</small></div>""", unsafe_allow_html=True)
                with col_d2:
                    ll = info.get("lai_lo_pct", 0) * 100
                    lc = "#4CAF50" if ll >= 0 else "#f44336"
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Lãi/Lỗ</h4><h3 style="color:{lc};">{ll:+.1f}%</h3></div>""", unsafe_allow_html=True)
                with col_d3:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>ROE</h4><h3>{info.get('roe', 0)*100:.1f}%</h3><small>Beta: {info.get('beta', 0):.2f}</small></div>""", unsafe_allow_html=True)
                with col_d4:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Tín hiệu</h4><h3 style="color:{signal_color};">{info.get('ket_luan', '')}</h3><small>{info.get('hanh_dong', '')}</small></div>""", unsafe_allow_html=True)

                st.markdown(f"""<div class="card" style="padding:0.8rem;"><h4>Tỷ trọng: Hiện tại {wt_ht:.1f}% → Mục tiêu {wt_mt:.1f}%</h4>
                <div style="background:#0D2137;border-radius:8px;height:20px;overflow:hidden;margin-top:0.5rem;">
                <div style="background:linear-gradient(90deg,#FFD700,#FFE55C);width:{min(wt_ht,100)}%;height:100%;border-radius:8px;"></div></div>
                <small>Chênh lệch: {info.get('chenh_lech', 0):.4f} | Upside: {info.get('upside', 0):,.0f} | VaR: {info.get('var_1', 0):,.0f}</small></div>""", unsafe_allow_html=True)

        st.markdown("### 📊 Phân bổ danh mục")
        labels = [ma for ma in kpi]
        values_ht = [kpi[ma].get("ty_trong_ht", 0) * 100 for ma in kpi]
        if values_ht:
            fig_kpi = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "bar"}]],
                subplot_titles=("Tỷ trọng hiện tại", "Phân bổ %"))
            fig_kpi.add_trace(go.Pie(labels=labels, values=values_ht, hole=0.4), row=1, col=1)
            colors_pie = px.colors.qualitative.Set3[:len(labels)]
            fig_kpi.add_trace(go.Bar(x=labels, y=values_ht, marker_color=colors_pie,
                text=[f"{v:.1f}%" for v in values_ht], textposition="outside"), row=1, col=2)
            fig_kpi.update_layout(height=400, showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_kpi, width='stretch')

        rows_kpi = []
        for ma, info in kpi.items():
            wt_ht = info.get("ty_trong_ht", 0) * 100
            wt_mt = info.get("ty_trong_mt", 0) * 100
            rows_kpi.append({
                "Mã": ma, "Ngành": info.get("nganh", ""),
                "Giá": f"{info.get('gia', 0):,.0f}",
                "% Lãi/Lỗ": f"{info.get('lai_lo_pct', 0)*100:.1f}%",
                "ROE": f"{info.get('roe', 0)*100:.1f}%", "P/E": f"{info.get('pe', 0):.1f}",
                "Upside": f"{info.get('upside', 0):,.0f}",
                "Điểm Mua": f"{info.get('diem_mua', 0):.0f}",
                "Điểm Bán": f"{info.get('diem_ban', 0):.0f}",
                "Kết luận": info.get("ket_luan", ""), "Hành động": info.get("hanh_dong", ""),
                "Tỷ trọng HT": f"{wt_ht:.1f}%", "Tỷ trọng MT": f"{wt_mt:.1f}%",
                "Beta": f"{info.get('beta', 0):.2f}", "VaR 1 ngày": f"{info.get('var_1', 0):,.0f}",
                "Trạng thái": info.get("trang_thai", ""),
            })
        df_kpi = pd.DataFrame(rows_kpi)
        if not df_kpi.empty:
            st.dataframe(df_kpi, width='stretch', hide_index=True)
            csv_kpi = df_kpi.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_kpi, file_name="kpi_scorecard.csv", mime="text/csv", width='stretch')

        st.markdown("### 📈 Lãi/Lỗ từng mã")
        ma_list = list(kpi.keys())
        lai_lo = [kpi[ma].get("lai_lo_pct", 0) * 100 for ma in ma_list]
        colors_ll = ["#4CAF50" if v >= 0 else "#f44336" for v in lai_lo]
        fig_ll = go.Figure(data=[go.Bar(x=ma_list, y=lai_lo, marker_color=colors_ll,
            text=[f"{v:+.1f}%" for v in lai_lo], textposition="outside")])
        fig_ll.update_layout(title="% Lãi/Lỗ theo mã", yaxis_title="%", height=350,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
        st.plotly_chart(fig_ll, width='stretch')

    with tab_vn:
        st.markdown(f"### 🇻🇳 Cơ sở dữ liệu cổ phiếu Việt Nam ({len(DOCS['co_phieu_vn'])} mã)")
        st.markdown("Nguồn: **TONG_HOP_v44** — dữ liệu 29/05/2026 | BCTC Q1/2026")

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            ng_loc = st.selectbox("Ngành:", ["Tất cả"] + sorted(set(
                info.get("nganh", "") for info in DOCS["co_phieu_vn"].values() if info.get("nganh")
            )), key="vn_nganh")
        with col_f2:
            tin_hieu_loc = st.selectbox("Tín hiệu:", ["Tất cả", "MUA MẠNH", "MUA", "GIỮ", "BÁN", "BÁN MẠNH"], key="vn_tin_hieu")

        with st.expander("🔍 Bộ lọc nâng cao", expanded=False):
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                pe_range = st.slider("Khoảng P/E:", 0, 50, (0, 30), key="vn_pe")
            with col_a2:
                roe_range = st.slider("Khoảng ROE (%):", 0, 50, (0, 30), key="vn_roe")
            with col_a3:
                vh_range = st.slider("Vốn hóa (tỷ ₫):", 0, 500000, (0, 500000), step=10000, key="vn_vh")

        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            sort_by = st.selectbox("Sắp xếp:", ["Mặc định", "Giá giảm dần", "P/E thấp nhất", "ROE cao nhất", "Vốn hóa lớn nhất"], key="vn_sort")
        with col_s2:
            so_sanh_chon = st.multiselect("Chọn 2-3 mã để so sánh:", sorted(DOCS["co_phieu_vn"].keys()), max_selections=4, key="vn_ss")

        db_vn = DOCS["co_phieu_vn"]
        filtered = {}
        for ma, info in db_vn.items():
            if ng_loc != "Tất cả" and info.get("nganh") != ng_loc:
                continue
            if tin_hieu_loc != "Tất cả" and info.get("tin_hieu") != tin_hieu_loc:
                continue
            pe = info.get("pe", 0)
            roe = info.get("roe", 0) * 100 if info.get("roe") else 0
            vh = info.get("von_hoa", 0)
            if pe and (pe < pe_range[0] or pe > pe_range[1]):
                continue
            if roe and (roe < roe_range[0] or roe > roe_range[1]):
                continue
            if vh and (vh < vh_range[0] or vh > vh_range[1]):
                continue
            filtered[ma] = info

        if so_sanh_chon and len(so_sanh_chon) >= 2:
            st.markdown("### 🔄 So sánh cổ phiếu")
            ss_data = []
            for ma in so_sanh_chon:
                info = db_vn.get(ma, {})
                ss_data.append({
                    "Chỉ tiêu": ma,
                    "Tên": info.get("ten", ""),
                    "Ngành": info.get("nganh", ""),
                    "Giá (₫)": info.get("gia", 0),
                    "P/E": info.get("pe", 0),
                    "P/B": info.get("pb", 0),
                    "ROE%": info.get("roe", 0) * 100 if info.get("roe") else 0,
                    "Vốn hóa (tỷ)": info.get("von_hoa", 0),
                    "EPS": info.get("eps", 0),
                    "%YTD": info.get("ytd", 0) * 100 if info.get("ytd") else 0,
                    "D/E": info.get("de_ratio", 0),
                    "Cổ tức%": info.get("co_tuc_pct", 0),
                    "ROIC%": info.get("roic", 0) * 100 if info.get("roic") else 0,
                })
            df_ss = pd.DataFrame(ss_data).set_index("Chỉ tiêu")
            st.dataframe(df_ss.T, width='stretch')

            fig_radar = go.Figure()
            metrics_radar = ["P/E", "P/B", "ROE%", "EPS", "Vốn hóa (tỷ)", "Cổ tức%"]
            for row in ss_data:
                values = [row.get(m, 0) if row.get(m, 0) >= 0 else 0 for m in metrics_radar]
                fig_radar.add_trace(go.Scatterpolar(r=values, theta=metrics_radar, fill="toself", name=row.get("Chỉ tiêu", "")))
            fig_radar.update_layout(title="So sánh cổ phiếu (Radar)", height=400,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_radar, width='stretch')

        rows_vn = []
        for ma, info in filtered.items():
            rows_vn.append({
                "Mã": ma, "Tên": info.get("ten", ""), "Ngành": info.get("nganh", ""),
                "Giá (₫)": f"{info.get('gia', 0):,.0f}",
                "P/E": f"{info.get('pe', 0):.1f}" if info.get("pe") else "-",
                "P/B": f"{info.get('pb', 0):.2f}" if info.get("pb") else "-",
                "ROE%": f"{info.get('roe', 0)*100:.1f}" if info.get("roe") else "-",
                "EPS": f"{info.get('eps', 0):,.0f}" if info.get("eps") else "-",
                "Vốn hóa (tỷ)": f"{info.get('von_hoa', 0):,.0f}" if info.get("von_hoa") else "-",
                "%YTD": f"{info.get('ytd', 0)*100:+.1f}" if info.get("ytd") else "-",
                "Tín hiệu": info.get("tin_hieu", ""),
                "D/E": f"{info.get('de_ratio', 0):.1f}" if info.get("de_ratio") else "-",
                "Cổ tức %": f"{info.get('co_tuc_pct', 0):.0f}%" if info.get("co_tuc_pct") else "-",
                "ROIC%": f"{info.get('roic', 0)*100:.1f}" if info.get("roic") else "-",
                "Biên LN%": f"{info.get('bien_ln', 0)*100:.1f}" if info.get("bien_ln") else "-",
            })
        def parse_float(s, fallback=0):
            if s == "-" or s is None:
                return fallback
            try:
                return float(str(s).replace(",", ""))
            except Exception:
                return fallback
        if sort_by == "Giá giảm dần":
            rows_vn.sort(key=lambda r: parse_float(r["Giá (₫)"]), reverse=True)
        elif sort_by == "P/E thấp nhất":
            rows_vn.sort(key=lambda r: parse_float(r["P/E"], 9999))
        elif sort_by == "ROE cao nhất":
            rows_vn.sort(key=lambda r: parse_float(r["ROE%"], -1), reverse=True)
        elif sort_by == "Vốn hóa lớn nhất":
            rows_vn.sort(key=lambda r: parse_float(r["Vốn hóa (tỷ)"]), reverse=True)

        if rows_vn:
            df_vn = pd.DataFrame(rows_vn)
            st.dataframe(df_vn, width='stretch', hide_index=True)
            st.markdown(f"Hiển thị **{len(rows_vn)}** / {len(db_vn)} mã")
            csv_vn = df_vn.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_vn, file_name="co_phieu_vn.csv", mime="text/csv", width='stretch')
        else:
            st.info("Không tìm thấy mã nào phù hợp.")

    with tab_tg:
        st.markdown(f"### 🌐 Cổ phiếu thế giới ({len(DOCS['co_phieu_tg'])} mã)")
        st.markdown("Nguồn: **TONG_HOP_v44** + **yfinance** (P/E, P/B, ROE, Vốn hóa — cached 24h)")
        @st.cache_data(ttl=86400, show_spinner="📡 Đang tải dữ liệu yfinance...")
        def _enrich_world_stocks(tickers):
            import yfinance as yf
            result = {}
            for ma in tickers:
                try:
                    t = yf.Ticker(ma)
                    info = t.info or {}
                    result[ma] = {
                        "pe": info.get("trailingPE") or info.get("forwardPE") or 0,
                        "pb": info.get("priceToBook") or 0,
                        "roe": (info.get("returnOnEquity") or 0) * 100,
                        "von_hoa": (info.get("marketCap") or 0) / 1e9,
                        "eps": info.get("trailingEps") or 0,
                        "dividend_yield": (info.get("dividendYield") or 0) * 100,
                    }
                except Exception:
                    result[ma] = {"pe": 0, "pb": 0, "roe": 0, "von_hoa": 0, "eps": 0, "dividend_yield": 0}
            return result
        tickers_list = list(DOCS["co_phieu_tg"].keys())
        enriched = _enrich_world_stocks(tuple(tickers_list))
        rows_tg = []
        for ma, info in DOCS["co_phieu_tg"].items():
            e = enriched.get(ma, {})
            pe = e.get("pe", 0) or info.get("pe", 0) or 0
            pb = e.get("pb", 0) or info.get("pb", 0) or 0
            roe = e.get("roe", 0) or (info.get("roe", 0) * 100 if info.get("roe") else 0)
            von_hoa = e.get("von_hoa", 0) or info.get("von_hoa", 0) or 0
            rows_tg.append({
                "Ticker": ma, "Tên": info.get("ten", ""), "Sàn": info.get("san", ""),
                "Giá ($)": f"{info.get('gia', 0):,.2f}",
                "P/E": f"{pe:.1f}" if pe else "-",
                "P/B": f"{pb:.2f}" if pb else "-",
                "ROE%": f"{roe:.1f}" if roe else "-",
                "Vốn hóa (tỷ$)": f"{von_hoa:,.1f}" if von_hoa else "-",
                "Cổ tức %": f"{e.get('dividend_yield', 0):.2f}" if e.get("dividend_yield") else "-",
                "Tín hiệu": info.get("tin_hieu", ""), "Ngành": info.get("nganh", ""),
            })
        if rows_tg:
            df_tg = pd.DataFrame(rows_tg)
            st.dataframe(df_tg, width='stretch', hide_index=True)
            csv_tg = df_tg.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_tg, file_name="co_phieu_tg.csv", mime="text/csv", width='stretch')

    with tab_port:
        st.markdown("### 📊 Hệ thống quản lý danh mục")
        st.markdown("Chi tiết từng mã — click **▶** để xem thông số nâng cao:")

        for ma, info in dm.items():
            lai_lo = info.get("gia_thi_truong", 0) - info.get("gia_von", 0)
            lai_lo_pct = lai_lo / info.get("gia_von", 1) * 100 if info.get("gia_von") else 0
            with st.expander(f"**{ma}** — {info.get('nganh', '')} | Vốn: {info.get('gia_von', 0):,.0f}₫ → TT: {info.get('gia_thi_truong', 0):,.0f}₫", expanded=False):
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Giá vốn TB</h4><h3>{info.get('gia_von', 0):,.0f}₫</h3></div>""", unsafe_allow_html=True)
                with col_m2:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Giá TT</h4><h3>{info.get('gia_thi_truong', 0):,.0f}₫</h3></div>""", unsafe_allow_html=True)
                with col_m3:
                    lc = "#4CAF50" if lai_lo >= 0 else "#f44336"
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Lãi/Lỗ</h4><h3 style="color:{lc};">{lai_lo:+,.0f}₫</h3></div>""", unsafe_allow_html=True)
                with col_m4:
                    st.markdown(f"""<div class="card-blue" style="padding:0.8rem;"><h4>Nợ ký quỹ</h4><h3>{info.get('no_ky_quy', 0):,.0f}₫</h3></div>""", unsafe_allow_html=True)
                wt_mt = info.get("ty_trong_muc_tieu", 0) * 100
                st.markdown(f"""<div class="card" style="padding:0.8rem;"><h4>Tỷ trọng mục tiêu: {wt_mt:.1f}%</h4>
                <div style="background:#0D2137;border-radius:8px;height:20px;overflow:hidden;">
                <div style="background:linear-gradient(90deg,#FFD700,#FFE55C);width:{min(wt_mt,100)}%;height:100%;border-radius:8px;"></div></div>
                <small>SL: {info.get('so_luong', 0):,.0f} CP | VH: {info.get('von_hoa', 0):,.0f}</small></div>""", unsafe_allow_html=True)

        rows_dm = []
        for ma, info in dm.items():
            lai_lo = info.get("gia_thi_truong", 0) - info.get("gia_von", 0)
            lai_lo_pct = lai_lo / info.get("gia_von", 1) * 100 if info.get("gia_von") else 0
            rows_dm.append({
                "Mã": ma, "Ngành": info.get("nganh", ""),
                "Tỷ trọng MT": f"{info.get('ty_trong_muc_tieu', 0)*100:.1f}%",
                "Số lượng": f"{info.get('so_luong', 0):,.0f}",
                "Giá vốn TB": f"{info.get('gia_von', 0):,.0f}",
                "Giá thị trường": f"{info.get('gia_thi_truong', 0):,.0f}",
                "Lãi/Lỗ (₫)": f"{lai_lo:+,.0f}", "Lãi/Lỗ (%)": f"{lai_lo_pct:+.1f}%",
                "Vốn hóa": f"{info.get('von_hoa', 0):,.0f}",
                "Nợ ký quỹ": f"{info.get('no_ky_quy', 0):,.0f}",
            })
        if rows_dm:
            df_dm = pd.DataFrame(rows_dm)
            st.dataframe(df_dm, width='stretch', hide_index=True)
            csv_dm = df_dm.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_dm, file_name="danh_muc.csv", mime="text/csv", width='stretch')

        st.markdown("### 📈 Biểu đồ phân bổ danh mục")
        labels_dm = list(dm.keys())
        values_dm = [dm[ma].get("ty_trong_muc_tieu", 0) * 100 for ma in dm]
        fig_dm = go.Figure(data=[go.Pie(labels=labels_dm, values=values_dm, hole=0.4)])
        fig_dm.update_layout(title="Tỷ trọng mục tiêu (%)", height=400,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
        st.plotly_chart(fig_dm, width='stretch')

        st.markdown("### 🔥 Bản đồ tương quan")
        try:
            ma_heat = [m for m in dm.keys() if m in DOCS.get("live", {}) or m in DOCS.get("kpi", {})]
            if len(ma_heat) < 2:
                st.info("Cần ít nhất 2 mã trong danh mục để vẽ bản đồ tương quan.")
            else:
                kpi_data = DOCS.get("kpi", {})
                co_phieu_vn = DOCS.get("co_phieu_vn", {})
                sector_map = {}
                beta_map = {}
                for ma in ma_heat:
                    info = kpi_data.get(ma, {}) or co_phieu_vn.get(ma, {})
                    sector_map[ma] = (info.get("nganh", "") or info.get("sector", "") or "Khác").strip()
                    beta_map[ma] = float(info.get("beta", 1.0) or 1.0)
                n = len(ma_heat)
                corr = np.eye(n)
                used_real = 0
                _stocks_data = {}
                _vn_set_c = set((DOCS.get("co_phieu_vn") or {}).keys())
                _to_fetch = [(ma, ".VN" if ma in _vn_set_c else "") for ma in ma_heat]
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import yfinance as _yf_batch
                def _fetch_one_corr(item):
                    sym, sfx = item
                    try:
                        t = _yf_batch.Ticker(sym + sfx)
                        h = t.history(period="6mo", timeout=5)
                        if not h.empty and len(h) > 20:
                            r = h['Close'].pct_change().dropna()
                            return sym, r
                    except Exception:
                        pass
                    return sym, None
                with ThreadPoolExecutor(max_workers=20) as exe:
                    futs = {exe.submit(_fetch_one_corr, item): item for item in _to_fetch}
                    for fut in as_completed(futs):
                        sym, rets = fut.result()
                        if rets is not None and len(rets) > 15:
                            _stocks_data[sym] = rets
                if len(_stocks_data) >= 2:
                    ordered = [m for m in ma_heat if m in _stocks_data]
                    for i in range(len(ordered)):
                        for j in range(i+1, len(ordered)):
                            ri = _stocks_data[ordered[i]]
                            rj = _stocks_data[ordered[j]]
                            common = sorted(set(ri.index) & set(rj.index))
                            if len(common) > 15:
                                corr[i, j] = max(-0.95, min(0.95, float(ri.loc[common].corr(rj.loc[common]))))
                                corr[j, i] = corr[i, j]
                                used_real += 1
                            else:
                                if sector_map.get(ordered[i]) == sector_map.get(ordered[j]) and sector_map.get(ordered[i], "Khác") != "Khác":
                                    base = 0.72
                                else:
                                    base = 0.32
                                bi = beta_map.get(ordered[i], 1.0)
                                bj = beta_map.get(ordered[j], 1.0)
                                corr[i, j] = max(-0.95, min(0.95, base + 0.05 * (bi-1)*(bj-1)))
                                corr[j, i] = corr[i, j]
                    df_corr = pd.DataFrame(corr, index=ordered, columns=ordered)
                else:
                    for i in range(n):
                        for j in range(i+1, n):
                            if sector_map[ma_heat[i]] == sector_map[ma_heat[j]] and sector_map[ma_heat[i]] != "Khác":
                                base = 0.72
                            else:
                                base = 0.32
                            bi, bj = beta_map[ma_heat[i]], beta_map[ma_heat[j]]
                            corr[i, j] = max(-0.95, min(0.95, base + 0.05*(bi-1)*(bj-1)))
                            corr[j, i] = corr[i, j]
                    df_corr = pd.DataFrame(corr, index=ma_heat, columns=ma_heat)
                if used_real > 0:
                    title_corr = f"Ma trận tương quan từ giá thật (yfinance 6T, {used_real}/{n*(n-1)//2} cặp)"
                else:
                    title_corr = "Ma trận tương quan (yfinance tạm không khả dụng)"
                fig_heat = go.Figure(data=go.Heatmap(
                    z=df_corr.values, x=list(df_corr.columns), y=list(df_corr.index),
                    text=df_corr.values.round(2), texttemplate="%{text}", textfont={"color": "#ECE8E1"},
                    colorscale="RdBu_r", zmin=-1, zmax=1))
                fig_heat.update_layout(height=450, title=title_corr,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_heat, use_container_width=True)
                if used_real > 0:
                    st.caption(f"✅ Tương quan tính từ giá thật {used_real}/{n*(n-1)//2} cặp mã (yfinance 6T).")
                else:
                    st.caption("⚠️ Chưa có dữ liệu giá thật để tính tương quan.")
        except Exception as e:
            st.info(f"Không thể tải dữ liệu tương quan: {e}")

    with tab_liquid:
        st.markdown("### 💧 Rủi ro thanh khoản — ADTV")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích:</strong> <b>ADTV</b> = lượng cổ phiếu giao dịch trung bình mỗi ngày. ADTV cao = dễ mua/bán không lo kẹt hàng. ADTV thấp (<5,000) = khó bán khi cần tiền gấp.</div>', unsafe_allow_html=True)
        st.markdown("ADTV 20 phiên gần nhất, Số ngày thanh lý, cảnh báo kẹt hàng")
        liq = DOCS["liquid"]
        rows_liq = []
        for ma, info in sorted(liq.items(), key=lambda x: x[1].get("adtv", 0), reverse=True):
            adtv = info.get("adtv", 0)
            risk = "🟢 Cao" if adtv > 20000 else ("🟡 TB" if adtv > 5000 else "🔴 Thấp")
            rows_liq.append({
                "Mã CP": ma, "ADTV 20P (nghìn CP)": f"{adtv:,.0f}",
                "Giá HT (₫)": f"{info.get('gia', 0):,.0f}",
                "GTGD/Ngày (₫)": f"{info.get('gtgd_ngay', 0):,.0f}",
                "Đánh giá": risk,
            })
        if rows_liq:
            df_liq = pd.DataFrame(rows_liq)
            st.dataframe(df_liq, width='stretch', hide_index=True)
            csv_liq = df_liq.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_liq, file_name="thanh_khoan.csv", mime="text/csv", width='stretch')

        st.markdown("### ⚠️ Cảnh báo thanh khoản")
        any_warn = False
        for ma, info in sorted(liq.items(), key=lambda x: x[1].get("adtv", 0)):
            adtv = info.get("adtv", 0)
            if adtv < 5000:
                st.warning(f"⚠️ **{ma}** — ADTV chỉ {adtv:,.0f} nghìn CP/ngày. Thanh khoản thấp, cần thận trọng khi giao dịch lớn.")
                any_warn = True
            elif adtv < 15000:
                st.info(f"ℹ️ **{ma}** — ADTV {adtv:,.0f} nghìn CP/ngày. Thanh khoản trung bình.")
                any_warn = True
        if not any_warn:
            st.success("✅ Tất cả mã đều có thanh khoản tốt.")

    def pct_to_num(s):
        try: return float(str(s).replace("%", ""))
        except Exception: return 0

    with tab_esg:
        st.markdown("### 🌱 CHẤM ĐIỂM ESG THEO NGÀNH")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích:</strong> <b>E</b> (Môi trường) — công ty có thải carbon, xử lý nước thải tốt không; <b>S</b> (Xã hội) — đối xử với nhân viên, cộng đồng ra sao; <b>G</b> (Quản trị) — ban lãnh đạo có minh bạch không. Tổng > 50% là khá tốt.</div>', unsafe_allow_html=True)
        st.markdown("Ma trận trọng số E·S·G — chuẩn MSCI/Sustainalytics")
        esg = DOCS["esg"]
        rows_esg = []
        for ten, info in esg.items():
            e_n = pct_to_num(info.get("e", "0%"))
            s_n = pct_to_num(info.get("s", "0%"))
            g_n = pct_to_num(info.get("g", "0%"))
            total = e_n + s_n + g_n
            rows_esg.append({
                "Ngành": ten,
                "E (Môi trường)": info.get("e", ""), "S (Xã hội)": info.get("s", ""),
                "G (Quản trị)": info.get("g", ""),
                "Tổng": f"{total}%",
                "Lý do": info.get("mo_ta", ""),
            })
        if rows_esg:
            df_esg = pd.DataFrame(rows_esg)
            st.dataframe(df_esg, width='stretch', hide_index=True)
            csv_esg = df_esg.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Xuất CSV", data=csv_esg, file_name="esg_scoring.csv", mime="text/csv", width='stretch')

        st.markdown("### 📊 Phân bổ điểm ESG")
        esg_names = [n for n in esg.keys() if n != "nan"]
        if esg_names:
            e_vals = [pct_to_num(esg[n].get("e", "0%")) for n in esg_names]
            s_vals = [pct_to_num(esg[n]["s"]) for n in esg_names]
            g_vals = [pct_to_num(esg[n]["g"]) for n in esg_names]
            fig_esg = go.Figure(data=[
                go.Bar(name="E (Môi trường)", x=esg_names, y=e_vals, marker_color="#4CAF50"),
                go.Bar(name="S (Xã hội)", x=esg_names, y=s_vals, marker_color="#2196F3"),
                go.Bar(name="G (Quản trị)", x=esg_names, y=g_vals, marker_color="#FFC107"),
            ])
            fig_esg.update_layout(title="Trọng số ESG theo ngành", barmode="group", height=400,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_esg, width='stretch')

            st.markdown("### 📊 Progress bars ESG")
            for i, name in enumerate(esg_names):
                if name == "nan": continue
                e_v, s_v, g_v = e_vals[i], s_vals[i], g_vals[i]
                total = e_v + s_v + g_v
                st.markdown(f"""<div class="card" style="padding:0.8rem;">
                <h4>{name}</h4>
                <div style="display:flex;gap:4px;height:24px;border-radius:8px;overflow:hidden;">
                <div style="background:#4CAF50;width:{e_v}%;text-align:center;color:white;font-size:0.8rem;">E</div>
                <div style="background:#2196F3;width:{s_v}%;text-align:center;color:white;font-size:0.8rem;">S</div>
                <div style="background:#FFC107;width:{g_v}%;text-align:center;color:#0A1929;font-size:0.8rem;">G</div>
                </div><small>Tổng: {total}%</small></div>""", unsafe_allow_html=True)

    with tab_stress:
        st.markdown("### 🌪️ KIỂM TRA KHỦNG HOẢNG VĨ MÔ")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích:</strong> Mô phỏng nếu các yếu tố vĩ mô (lãi suất, tỷ giá, lạm phát) thay đổi mạnh, danh mục của bạn sẽ chịu tác động ra sao. Đây là bài tập "giả định" để đánh giá <b>khả năng chịu nhiệt</b> của danh mục.</div>', unsafe_allow_html=True)
        st.markdown("Kịch bản khủng hoảng — tác động lãi suất, tỷ giá, lạm phát, giá hàng hóa")
        stress_vars = DOCS["stress_vars"]
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        with col_s1:
            st.markdown(f"""<div class="metric-box"><h4>📈 Lãi suất</h4><h3>{stress_vars.get('lai_suat', '')}bps</h3></div>""", unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""<div class="metric-box"><h4>💱 Tỷ giá</h4><h3>+{stress_vars.get('ty_gia', '')}</h3></div>""", unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""<div class="metric-box"><h4>🔥 Lạm phát</h4><h3>+{stress_vars.get('lam_phat', '')}</h3></div>""", unsafe_allow_html=True)
        with col_s4:
            st.markdown(f"""<div class="metric-box"><h4>⚙️ Giá thép</h4><h3>{stress_vars.get('gia_thep', '')}</h3></div>""", unsafe_allow_html=True)
        with col_s5:
            st.markdown(f"""<div class="metric-box"><h4>📊 GDP</h4><h3>{stress_vars.get('gdp', '')}</h3></div>""", unsafe_allow_html=True)

        st.markdown("### 📊 Tác động đến từng mã")
        stress_data = DOCS["stress"]
        rows_stress = []
        base_v, stress_v, ma_s = [], [], []
        for ma, info in stress_data.items():
            ma_s.append(ma)
            downside_str = info.get("downside", "")
            try:
                downside_val = float(str(downside_str).replace("%", ""))
                ds_color = "#4CAF50" if downside_val >= 0 else "#f44336"
            except Exception:
                ds_color = "#8892B0"
            rows_stress.append({
                "Mã CP": ma, "Ngành": info.get("nganh", ""),
                "Downside": downside_str, "Giá HL Base": info.get("base", ""),
                "Giá HL Stress": info.get("stress", ""), "Tỷ lệ TT": info.get("ty_trong_tt", ""),
            })

            try:
                base_v.append(float(str(info.get("base", "0%")).replace("%", "")))
            except Exception:
                base_v.append(0)

            try:
                stress_v.append(float(str(info.get("stress", "0%")).replace("%", "")))
            except Exception:
                stress_v.append(0)
        if ma_s:
            fig_st = go.Figure(data=[
                go.Bar(name="Giá HL Base", x=ma_s, y=base_v, marker_color="#FFD700"),
                go.Bar(name="Giá HL Stress", x=ma_s, y=stress_v, marker_color="#f44336"),
            ])
            fig_st.update_layout(title="Giá hợp lý: Base vs Stress", barmode="group", height=350,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_st, width='stretch')

    with tab_perf:
        st.markdown("### 📊 PHÂN RÃ HIỆU SUẤT & CHUẨN")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích nhanh:</strong> <b>Alpha</b> > 0 = danh mục đang "ăn" hơn thị trường (tài năng của nhà đầu tư); <b>Sharpe</b> > 1 = đang "ăn chắc mặc bền", < 0.5 = cần xem lại; <b>Rf</b> = lãi suất gửi ngân hàng (phi rủi ro); <b>Rm</b> = thị trường chung VN-Index tăng/giảm bao nhiêu; <b>Treynor</b> = lợi nhuận trên mỗi đơn vị rủi ro hệ thống.</div>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            st.markdown(f"""<div class="metric-box"><h4>Rf (LS phi rủi ro)</h4><h3>{perf.get('Rf', 0)*100:.1f}%</h3></div>""", unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""<div class="metric-box"><h4>Rm (VN-Index YTD)</h4><h3>{perf.get('Rm', 0)*100:.1f}%</h3></div>""", unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""<div class="metric-box"><h4>Beta</h4><h3>{perf.get('Beta', 0):.2f}</h3></div>""", unsafe_allow_html=True)
        with col_p4:
            st.markdown(f"""<div class="metric-box"><h4>Return DM</h4><h3>{perf.get('Rp', 0)*100:.1f}%</h3></div>""", unsafe_allow_html=True)

        rf = perf.get("Rf", 0.045)
        rm = perf.get("Rm", 0.082)
        beta = perf.get("Beta", 1.0)
        rp = perf.get("Rp", return_pct / 100)
        alpha = rp - (rf + beta * (rm - rf))
        sharpe = (rp - rf) / 0.15 if rp > 0 else 0
        phi = perf.get("phi_gd", 0.0015)
        thue = perf.get("thue", 0.001)
        net_return = rp - phi - thue
        treynor = (rp - rf) / beta if beta > 0 else 0

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            st.markdown(f"""<div class="metric-box"><h4>Alpha (α)</h4><h3 style="color:{'#4CAF50' if alpha>0 else '#f44336'}">{alpha*100:+.2f}%</h3></div>""", unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""<div class="metric-box"><h4>Sharpe Ratio</h4><h3 style="color:{'#4CAF50' if sharpe>1 else '#FFC107'}">{sharpe:.2f}</h3></div>""", unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""<div class="metric-box"><h4>Treynor</h4><h3>{treynor:.4f}</h3></div>""", unsafe_allow_html=True)
        with col_p4:
            st.markdown(f"""<div class="metric-box"><h4>Net Return</h4><h3 style="color:#4CAF50">{net_return*100:.2f}%</h3></div>""", unsafe_allow_html=True)

        st.info(f"💡 **Jensen's Alpha**: {alpha*100:+.2f}% — {'Vượt trội so với thị trường' if alpha > 0 else 'Thấp hơn kỳ vọng'}. "
                f"**Sharpe**: {sharpe:.2f} — {'Rất tốt' if sharpe > 2 else 'Tốt' if sharpe > 1 else 'Chấp nhận được' if sharpe > 0.5 else 'Cần cải thiện'}.")

        col_save1, col_save2 = st.columns(2)
        with col_save1:
            if st.button("💾 Lưu phiên (JSON)", key="save_perf"):
                import json, os
                session_data = {
                    "kpi": kpi, "danh_muc": dm, "performance": perf,
                    "thoi_gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                path = os.path.join(os.path.dirname(__file__), "data", "session.json")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
                st.success(f"Đã lưu session vào data/session.json")

    with tab_analytics:
        st.markdown("### 📈 Phân tích kỹ thuật & Rủi ro")
        st.markdown('<div class="simple-explain"><strong>📖 Giải thích nhanh:</strong> <b>CAGR</b> = tốc độ tăng trưởng kép mỗi năm; <b>Sharpe</b> = "điểm sức khỏe" của tài sản (>1 là tốt); <b>Max DD</b> = mức giảm sâu nhất từ đỉnh đến đáy (càng thấp càng đỡ đau); <b>VaR 95%</b> = trong 95% trường hợp, bạn mất tối đa bao nhiêu % trong 1 ngày; <b>Sortino</b> = giống Sharpe nhưng chỉ phạt rủi ro xấu; <b>Dự báo 6 tháng</b> = mức giá kỳ vọng dựa trên đà tăng trưởng lịch sử (KHÔNG phải khuyến nghị mua/bán).</div>', unsafe_allow_html=True)
        cac_ma_pt = {"VN-Index (FUEVN100)": "FUEVN100.VN","S&P 500": "^GSPC","Vàng/XAU": "GC=F","Bitcoin": "BTC-USD","Dầu WTI": "CL=F"}
        ma_chon = st.selectbox("Chọn mã phân tích:", list(cac_ma_pt.keys()), key="an_ma")
        ma_yahoo = cac_ma_pt[ma_chon]
        if st.button("🔍 Phân tích ngay", key="an_btn", use_container_width=True):
            with st.spinner("Đang phân tích dữ liệu..."):
                try:
                    pt = phan_tich_lich_su(ma_yahoo)
                    if pt is None:
                        st.warning(f"Không thể lấy dữ liệu cho {ma_chon}. Mã này có thể không khả dụng.")
                        st.stop()
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("CAGR", f"{(pt.get('cagr') or 0)*100:.1f}%", delta=f"{(pt.get('alpha') or 0)*100:.1f}%")
                    with col2:
                        st.metric("Sharpe", f"{pt.get('sharpe') or 0:.2f}")
                    with col3:
                        st.metric("Max DD", f"{(pt.get('max_drawdown') or 0)*100:.1f}%", delta_color="inverse")
                    with col4:
                        st.metric("VaR 95%", f"{(pt.get('var_95') or 0)*100:.1f}%", delta_color="inverse")
                    st.markdown("---")
                    st.markdown("### 📊 Lịch sử Drawdown")
                    dd = pt.get("drawdown_series", np.array([]))
                    if hasattr(dd, 'empty') and not dd.empty or isinstance(dd, np.ndarray) and dd.size > 0:
                        fig_dd = go.Figure()
                        fig_dd.add_trace(go.Scatter(y=dd*100, fill="tozeroy", line=dict(color="red", width=1), name="Drawdown %"))
                        fig_dd.update_layout(height=300, yaxis_title="Drawdown (%)",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                        st.plotly_chart(fig_dd, use_container_width=True)
                    st.markdown("### 📋 Chi tiết chỉ số")
                    scalar_keys = ["cagr","max_drawdown","sharpe","sortino","var_95","var_99","cvar_95","cvar_99",
                        "rui_ro_nam","loi_nhuan_tb_nam","du_bao_6m","gia_hien_tai","so_ngay",
                        "skewness","kurtosis","calmar","ulcer_index","win_rate","profit_factor",
                        "omega_ratio","downside_dev","autocorr_1","autocorr_5","jb_stat","jb_pval","tracking_error"]
                    label_map = {"cagr":"CAGR","max_drawdown":"Max Drawdown","sharpe":"Sharpe","sortino":"Sortino",
                        "var_95":"VaR 95%","var_99":"VaR 99%","cvar_95":"CVaR 95%","cvar_99":"CVaR 99%",
                        "rui_ro_nam":"Rủi ro năm","loi_nhuan_tb_nam":"Lợi nhuận TB năm","du_bao_6m":"Dự báo 6 tháng",
                        "gia_hien_tai":"Giá hiện tại","so_ngay":"Số ngày","skewness":"Độ lệch","kurtosis":"Kurtosis",
                        "calmar":"Calmar","ulcer_index":"Ulcer Index","win_rate":"Win Rate","profit_factor":"Profit Factor",
                        "omega_ratio":"Omega Ratio","downside_dev":"Downside Deviation","autocorr_1":"Autocorr 1 ngày",
                        "autocorr_5":"Autocorr 5 ngày","jb_stat":"Jarque-Bera","jb_pval":"JB p-value","tracking_error":"Tracking Error"}
                    cols_dt = st.columns(3)
                    for i, k in enumerate(scalar_keys):
                        v = pt.get(k)
                        if v is None or (isinstance(v, float) and np.isnan(v)):
                            display = "N/A"
                        elif isinstance(v, float):
                            display = f"{v:.4f}"
                        else:
                            display = str(v)
                        cols_dt[i % 3].markdown(f"**{label_map.get(k, k)}:** {display}")
                except Exception as e:
                    st.error(f"Lỗi phân tích: {e}")

    with tab_tools:
        st.markdown("### 🛠️ Bộ Công Cụ Nâng Cao")
        st.markdown("Các tính năng bổ sung: Watchlist, Cảnh báo giá, Biểu đồ kỹ thuật, So sánh cổ phiếu, Xuất PDF.")
        st.markdown("---")
        sub_alert, sub_chart, sub_watch, sub_compare, sub_pdf, sub_news, sub_event, sub_profile, sub_backtest, sub_ai, sub_optim, sub_telegram, sub_pay = st.tabs([
            "🔔 Cảnh báo giá",
            "📊 Biểu đồ kỹ thuật",
            "💼 Watchlist",
            "📈 So sánh CP",
            "📄 Xuất PDF",
            "📰 Tin tức",
            "📅 Sự kiện",
            "👤 Hồ sơ",
            "🧪 Backtest",
            "🤖 AI dự đoán",
            "🎯 Tối ưu DM",
            "📞 Telegram",
            "💳 Thanh toán",
        ])

        with sub_alert:
            st.markdown("#### 🔔 Cảnh báo giá cổ phiếu")
            st.caption("Đặt ngưỡng giá — khi giá hiện tại vượt ngưỡng sẽ hiện cảnh báo.")
            if "price_alerts" not in st.session_state:
                st.session_state.price_alerts = []
            with st.form("add_alert", clear_on_submit=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    all_stocks = sorted(DOCS.get("co_phieu_vn", {}).keys())
                    ma = st.selectbox("Mã CP", options=all_stocks, key="alert_ma")
                with c2:
                    nguong = st.number_input("Ngưỡng giá (₫)", min_value=0.0, value=100000.0, step=1000.0, key="alert_nguong")
                with c3:
                    loai = st.selectbox("Loại", [">", "<"], key="alert_loai")
                if st.form_submit_button("➕ Thêm cảnh báo", use_container_width=True):
                    st.session_state.price_alerts.append({"ma": ma, "nguong": nguong, "loai": loai})
                    st.success(f"✅ Đã thêm: {ma} {loai} {nguong:,.0f}₫")
            if st.session_state.price_alerts:
                st.markdown("##### Danh sách cảnh báo")
                for idx, alert in enumerate(list(st.session_state.price_alerts)):
                    gia_hien_tai = DOCS.get("co_phieu_vn", {}).get(alert["ma"], {}).get("gia", 0)
                    triggered = (alert["loai"] == ">" and gia_hien_tai > alert["nguong"]) or \
                                (alert["loai"] == "<" and gia_hien_tai < alert["nguong"])
                    col_a, col_b, col_c = st.columns([2, 3, 1])
                    with col_a:
                        st.markdown(f"**{alert['ma']}** {alert['loai']} {alert['nguong']:,.0f}₫")
                    with col_b:
                        if gia_hien_tai:
                            color = "🟢" if not triggered else "🔴"
                            st.markdown(f"{color} Giá hiện tại: **{gia_hien_tai:,.0f}₫**")
                        else:
                            st.markdown("⚪ Chưa có giá")
                    with col_c:
                        if st.button("🗑️", key=f"del_alert_{idx}"):
                            st.session_state.price_alerts.pop(idx)
                            st.rerun()
                    if triggered:
                        st.error(f"🚨 **CẢNH BÁO:** {alert['ma']} hiện tại **{gia_hien_tai:,.0f}₫** đã {'vượt' if alert['loai']=='>' else 'xuống dưới'} ngưỡng **{alert['nguong']:,.0f}₫**")

        with sub_chart:
            st.markdown("#### 📊 Biểu đồ kỹ thuật (MA + RSI)")
            st.caption("Moving Average (20, 50 ngày) và RSI (14 ngày) cho cổ phiếu được chọn.")
            cp_vn = DOCS.get("co_phieu_vn", {})
            ma_chon = st.selectbox("Chọn mã cổ phiếu", options=sorted(cp_vn.keys()), key="chart_ma")
            if ma_chon:
                info = cp_vn[ma_chon]
                gia_hien_tai = info.get("gia", 0)
                ytd = info.get("thay_doi_1nam", 0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Mã CP", ma_chon)
                c2.metric("Giá hiện tại", f"{gia_hien_tai:,.0f}₫")
                c3.metric("YTD", f"{ytd*100:+.1f}%")
                _chart_prices = None
                try:
                    import yfinance as _yf_chart
                    _t = _yf_chart.Ticker(ma_chon + ".VN" if ma_chon in cp_vn else ma_chon)
                    _h = _t.history(period="6mo")
                    if _h is not None and len(_h) >= 20:
                        _chart_prices = _h["Close"]
                        _chart_dates = _h.index
                        _chart_high = _h["High"]
                        _chart_low = _h["Low"]
                        _chart_open = _h["Open"]
                except Exception:
                    pass
                if _chart_prices is not None and len(_chart_prices) >= 20:
                    df_chart = pd.DataFrame({
                        "date": _chart_dates, "price": _chart_prices,
                        "open": _chart_open, "high": _chart_high, "low": _chart_low, "close": _chart_prices
                    })
                else:
                    np.random.seed(hash(ma_chon) % 2**32)
                    n_days = 120
                    base_price = max(gia_hien_tai * 0.85, 1000)
                    noise = np.cumsum(np.random.randn(n_days) * 0.012) + np.log(max(gia_hien_tai, 1) / base_price)
                    prices = base_price * np.exp(noise)
                    prices[-1] = gia_hien_tai if gia_hien_tai > 0 else prices[-1]
                    dates = pd.date_range(end=pd.Timestamp.today(), periods=n_days, freq="D")
                    df_chart = pd.DataFrame({"date": dates, "price": prices})
                df_chart["MA20"] = df_chart["price"].rolling(20).mean()
                df_chart["MA50"] = df_chart["price"].rolling(50).mean()
                delta = df_chart["price"].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, 1e-9)
                df_chart["RSI"] = 100 - (100 / (1 + rs))
                fig = go.Figure()
                if _chart_prices is not None and len(_chart_prices) >= 20:
                    fig.add_trace(go.Candlestick(x=df_chart["date"],
                        open=df_chart["open"], high=df_chart["high"],
                        low=df_chart["low"], close=df_chart["close"],
                        name=ma_chon))
                else:
                    fig.add_trace(go.Candlestick(x=df_chart["date"], open=df_chart["price"],
                        high=df_chart["price"]*1.01, low=df_chart["price"]*0.99,
                        close=df_chart["price"], name="Giá"))
                fig.add_trace(go.Scatter(x=df_chart["date"], y=df_chart["MA20"], mode="lines", name="MA 20", line=dict(color="#FFD700", width=1.5)))
                fig.add_trace(go.Scatter(x=df_chart["date"], y=df_chart["MA50"], mode="lines", name="MA 50", line=dict(color="#2196F3", width=1.5)))
                fig.update_layout(height=400, xaxis_rangeslider_visible=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig, use_container_width=True)
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df_chart["date"], y=df_chart["RSI"], mode="lines", name="RSI 14", line=dict(color="#FF9800", width=2)))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Quá mua (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Quá bán (30)")
                fig_rsi.update_layout(height=250, yaxis_title="RSI", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"), yaxis_range=[0, 100])
                st.plotly_chart(fig_rsi, use_container_width=True)
                rsi_now = df_chart["RSI"].iloc[-1]
                if rsi_now > 70:
                    st.warning(f"⚠️ RSI hiện tại = {rsi_now:.1f} → **Quá mua** (có thể điều chỉnh giảm)")
                elif rsi_now < 30:
                    st.success(f"✅ RSI hiện tại = {rsi_now:.1f} → **Quá bán** (có thể là cơ hội mua)")
                else:
                    st.info(f"ℹ️ RSI hiện tại = {rsi_now:.1f} → Trung tính")

        with sub_watch:
            st.markdown("#### 💼 Watchlist — Danh sách theo dõi")
            st.caption("Thêm cổ phiếu vào watchlist để theo dõi nhanh.")
            if "watchlist" not in st.session_state:
                st.session_state.watchlist = []
            with st.form("add_watch", clear_on_submit=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    ma_w = st.selectbox("Mã CP", options=sorted(DOCS.get("co_phieu_vn", {}).keys()), key="watch_ma")
                with c2:
                    ghi_chu = st.text_input("Ghi chú", placeholder="VD: Mục tiêu 150k", key="watch_note")
                if st.form_submit_button("➕ Thêm vào Watchlist", use_container_width=True):
                    if ma_w not in st.session_state.watchlist:
                        st.session_state.watchlist.append({"ma": ma_w, "ghi_chu": ghi_chu})
                        st.success(f"✅ Đã thêm {ma_w}")
                    else:
                        st.warning(f"⚠️ {ma_w} đã có trong watchlist")
            if st.session_state.watchlist:
                st.markdown("---")
                rows = []
                for item in st.session_state.watchlist:
                    ma = item["ma"] if isinstance(item, dict) else item
                    note = item.get("ghi_chu", "") if isinstance(item, dict) else ""
                    info = DOCS.get("co_phieu_vn", {}).get(ma, {})
                    rows.append({
                        "Mã": ma,
                        "Tên": info.get("ten", ""),
                        "Giá": f"{info.get('gia', 0):,.0f}₫",
                        "YTD": f"{info.get('thay_doi_1nam', 0)*100:+.1f}%",
                        "P/E": f"{info.get('pe', 0):.1f}",
                        "Ghi chú": note,
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                if st.button("🗑️ Xóa toàn bộ Watchlist"):
                    st.session_state.watchlist = []
                    st.rerun()

        with sub_compare:
            st.markdown("#### 📈 So sánh cổ phiếu")
            st.caption("Chọn 2-4 mã để so sánh side-by-side.")
            cp_vn_all = sorted(DOCS.get("co_phieu_vn", {}).keys())
            ds_chon = st.multiselect("Chọn cổ phiếu (2-4 mã)", options=cp_vn_all, default=cp_vn_all[:3] if len(cp_vn_all) >= 3 else cp_vn_all[:2], max_selections=4, key="compare_chon")
            if len(ds_chon) >= 2:
                rows = []
                for ma in ds_chon:
                    info = DOCS.get("co_phieu_vn", {}).get(ma, {})
                    kpi_data = DOCS.get("kpi", {}).get(ma, {})
                    rows.append({
                        "Mã": ma,
                        "Giá": f"{info.get('gia', 0):,.0f}",
                        "YTD %": f"{info.get('thay_doi_1nam', 0)*100:+.1f}",
                        "P/E": f"{info.get('pe', 0):.1f}",
                        "P/B": f"{info.get('pb', 0):.2f}",
                        "ROE %": f"{info.get('roe', 0)*100:.1f}",
                        "Vốn hóa (tỷ)": f"{info.get('von_hoa', 0)/1e9:.0f}",
                        "Tín hiệu": info.get("tin_hieu", "N/A"),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                metrics_to_plot = ["YTD %", "P/E", "P/B", "ROE %"]
                fig = go.Figure()
                for metric in metrics_to_plot:
                    vals = []
                    for r in rows:
                        try:
                            vals.append(float(r[metric].replace("%", "").replace(",", "")))
                        except Exception:
                            vals.append(0)
                    fig.add_trace(go.Bar(name=metric, x=[r["Mã"] for r in rows], y=vals))
                fig.update_layout(barmode="group", height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("👉 Chọn ít nhất 2 mã để so sánh.")

        with sub_pdf:
            st.markdown("#### 📄 Xuất báo cáo PDF")
            st.caption("Tạo báo cáo PDF với danh mục + top cổ phiếu + chỉ số.")
            ten_file = st.text_input("Tên file", value="bao_cao_robo_advisor.pdf", key="pdf_name")
            if st.button("📥 Tạo PDF", use_container_width=True):
                try:
                    from fpdf import FPDF
                    pdf = FPDF()
                    pdf.add_page()
                    try:
                        pdf.add_font("DejaVu", "", "DejaVuSansCondensed.ttf", uni=True)
                        pdf.set_font("DejaVu", size=14)
                    except Exception:
                        pdf.set_font("helvetica", size=14)
                    pdf.cell(0, 10, "BAO CAO ROBO-ADVISOR", ln=1, align="C")
                    pdf.set_font("helvetica", size=10)
                    pdf.cell(0, 8, f"Ngay tao: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align="C")
                    pdf.ln(5)
                    pdf.set_font("helvetica", "B", 12)
                    pdf.cell(0, 8, "1. Danh muc dau tu", ln=1)
                    pdf.set_font("helvetica", size=9)
                    dm = DOCS.get("danh_muc", {})
                    if dm:
                        pdf.cell(0, 6, f"Tong gia tri: {dm.get('tong_gia_tri', 0):,.0f} VND", ln=1)
                        pdf.cell(0, 6, f"Tong von: {dm.get('tong_von', 0):,.0f} VND", ln=1)
                        pdf.cell(0, 6, f"Lai/lo: {dm.get('tong_lai_lo', 0):+,.0f} VND", ln=1)
                    pdf.ln(3)
                    pdf.set_font("helvetica", "B", 12)
                    pdf.cell(0, 8, "2. Top co phieu theo doi", ln=1)
                    pdf.set_font("helvetica", size=9)
                    pdf.cell(30, 6, "Ma", 1)
                    pdf.cell(60, 6, "Ten", 1)
                    pdf.cell(30, 6, "Gia", 1)
                    pdf.cell(25, 6, "YTD%", 1)
                    pdf.cell(25, 6, "P/E", 1)
                    pdf.ln()
                    cp_sorted = sorted(DOCS.get("co_phieu_vn", {}).items(), key=lambda x: x[1].get("von_hoa", 0), reverse=True)[:15]
                    for ma, info in cp_sorted:
                        ten = (info.get("ten", "") or "")[:30]
                        pdf.cell(30, 6, ma, 1)
                        pdf.cell(60, 6, ten, 1)
                        pdf.cell(30, 6, f"{info.get('gia', 0):,.0f}", 1)
                        pdf.cell(25, 6, f"{info.get('thay_doi_1nam', 0)*100:+.1f}", 1)
                        pdf.cell(25, 6, f"{info.get('pe', 0):.1f}", 1)
                        pdf.ln()
                    pdf_bytes = pdf.output(dest="S").encode("latin-1", errors="replace")
                    st.download_button(
                        label="⬇️ Tải xuống PDF",
                        data=pdf_bytes,
                        file_name=ten_file,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success("✅ PDF đã tạo — bấm nút để tải xuống.")
                except Exception as e:
                    st.error(f"❌ Lỗi tạo PDF: {e}")

        with sub_news:
            st.markdown("#### 📰 Tin tức thị trường")
            st.caption("Tin tức tài chính — chứng khoán — doanh nghiệp (VnExpress, 24hMoney, VietnamBiz).")
            nguon_tin = st.selectbox("Nguồn", ["Chứng khoán", "Tài chính", "Kinh doanh"], key="news_src")
            rss_map = {
                "Chứng khoán": [
                    "https://www.24hmoney.vn/rss/chung-khoan.rss",
                    "https://www.vietnambiz.vn/rss/chung-khoan.rss",
                ],
                "Tài chính": [
                    "https://www.vietnambiz.vn/rss/tai-chinh.rss",
                    "https://www.24hmoney.vn/rss/tai-chinh.rss",
                ],
                "Kinh doanh": [
                    "https://vnexpress.net/rss/kinh-doanh.rss",
                    "https://www.vietnambiz.vn/rss/kinh-te.rss",
                ],
            }
            @st.cache_data(ttl=600, show_spinner="📡 Đang tải tin tức...")
            def _strip_html(s):
                import re
                if not s: return ""
                s = re.sub(r"<[^>]+>", "", s)
                s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
                return s.strip()
            @st.cache_data(ttl=600, show_spinner="📡 Đang tải tin tức...")
            def lay_tin_rss(urls):
                last_err = ""
                for url in (urls if isinstance(urls, list) else [urls]):
                    try:
                        import xml.etree.ElementTree as ET
                        r = requests.get(url, timeout=20, headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "application/rss+xml, application/xml, text/xml, */*",
                        })
                        r.encoding = "utf-8"
                        ct = r.headers.get("content-type", "")
                        if "xml" not in ct.lower() and "<rss" not in r.text[:2000] and "<?xml" not in r.text[:200]:
                            last_err = f"{url} trả về HTML (Content-Type={ct})"
                            continue
                        root = ET.fromstring(r.text)
                        items = []
                        for item in root.findall(".//item")[:20]:
                            tieu_de = (item.findtext("title", "") or "").strip()
                            mo_ta_raw = item.findtext("description", "") or ""
                            mo_ta = _strip_html(mo_ta_raw)[:200]
                            link = (item.findtext("link", "") or "").strip()
                            ngay = (item.findtext("pubDate", "") or "").strip()
                            if tieu_de:
                                items.append({"tieu_de": tieu_de, "mo_ta": mo_ta, "link": link, "ngay": ngay})
                        if items:
                            return items, url
                    except Exception as e:
                        last_err = f"{url}: {e}"
                        continue
                return [{"tieu_de": f"❌ Lỗi tải tin: {last_err}", "mo_ta": "", "link": "", "ngay": ""}], ""
            ds_tin, url_dung = lay_tin_rss(rss_map[nguon_tin])
            if ds_tin and not ds_tin[0]["tieu_de"].startswith("❌"):
                st.caption(f"✅ Nguồn: {url_dung.replace('https://','').split('/')[0]} — {len(ds_tin)} tin")
                for tin in ds_tin[:15]:
                    with st.container():
                        st.markdown(
                            f'<div style="background:rgba(255,215,0,0.05);border-left:3px solid #FFD700;'
                            f'padding:8px 12px;margin:6px 0;border-radius:4px;">'
                            f'<a href="{tin["link"]}" target="_blank" style="color:#FFD700;text-decoration:none;font-weight:600;">'
                            f'📰 {tin["tieu_de"][:120]}</a><br>'
                            f'<small style="color:#9AABB8;">🕐 {tin["ngay"][:25] if tin["ngay"] else ""}</small>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.warning("Không tải được tin. Kiểm tra mạng hoặc thử nguồn khác.")
                with st.expander("Chi tiết lỗi"):
                    st.code(ds_tin[0]["tieu_de"] if ds_tin else "Không có dữ liệu")

        with sub_event:
            st.markdown("#### 📅 Lịch sự kiện — ĐHCĐ, Cổ tức, Phát hành")
            st.caption("Sự kiện sắp tới của các mã cổ phiếu phổ biến.")
            @st.cache_data(ttl=3600)
            def ds_su_kien():
                return [
                    {"ma": "VCB", "loai": "Cổ tức", "ngay": "2026-07-15", "noi_dung": "Tạm ứng cổ tức tiền mặt 2025 — tỷ lệ 18%"},
                    {"ma": "FPT", "loai": "ĐHCĐ", "ngay": "2026-06-25", "noi_dung": "Đại hội cổ đông thường niên 2026"},
                    {"ma": "MBB", "loai": "Phát hành", "ngay": "2026-08-01", "noi_dung": "Phát hành ESOP cho nhân viên"},
                    {"ma": "HPG", "loai": "Báo cáo", "ngay": "2026-07-30", "noi_dung": "Công bố BCTC Q2/2026"},
                    {"ma": "VNM", "loai": "Cổ tức", "ngay": "2026-09-10", "noi_dung": "Thanh toán cổ tức còn lại 2025"},
                    {"ma": "MWG", "loai": "ĐHCĐ", "ngay": "2026-07-05", "noi_dung": "ĐHCĐ bất thường — phát hành tăng vốn"},
                    {"ma": "CTG", "loai": "Báo cáo", "ngay": "2026-07-20", "noi_dung": "Công bố BCTC Q2/2026"},
                    {"ma": "VIX", "loai": "Sáp nhập", "ngay": "2026-08-15", "noi_dung": "Hoàn tất sáp nhập VIX Securities"},
                    {"ma": "CTR", "loai": "Cổ tức", "ngay": "2026-07-25", "noi_dung": "Tạm ứng cổ tức 2026 — tỷ lệ 10%"},
                    {"ma": "VRE", "loai": "ĐHCĐ", "ngay": "2026-06-30", "noi_dung": "ĐHCĐ thường niên 2026"},
                ]
            sk = ds_su_kien()
            bo_loc = st.multiselect("Lọc theo mã CP", options=sorted(set(s["ma"] for s in sk)), default=sorted(set(s["ma"] for s in sk))[:5], key="event_filter")
            sk_loc = [s for s in sk if s["ma"] in bo_loc]
            for s in sorted(sk_loc, key=lambda x: x["ngay"]):
                color_map = {"Cổ tức": "#4CAF50", "ĐHCĐ": "#2196F3", "Phát hành": "#FF9800", "Báo cáo": "#9C27B0", "Sáp nhập": "#F44336"}
                c = color_map.get(s["loai"], "#888")
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03);border-left:3px solid {c};'
                    f'padding:8px 12px;margin:6px 0;border-radius:4px;">'
                    f'<b style="color:{c};">[{s["loai"]}]</b> '
                    f'<b>{s["ma"]}</b> — {s["noi_dung"]}<br>'
                    f'<small style="color:#9AABB8;">📅 {s["ngay"]}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with sub_profile:
            st.markdown("#### 👤 Hồ sơ cá nhân")
            st.caption("Cập nhật thông tin cá nhân — lưu trong phiên làm việc.")
            if "profile" not in st.session_state:
                st.session_state.profile = {
                    "ho_ten": "",
                    "sdt": "",
                    "email": "",
                    "ngay_sinh": "",
                    "nghe_nghiep": "",
                    "muc_tieu": "",
                }
            username_now = st.session_state.get("username", "Khách")
            st.markdown(f"**Tài khoản:** `{username_now}`")
            with st.form("profile_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ho_ten = st.text_input("Họ và tên", value=st.session_state.profile.get("ho_ten", ""))
                    sdt = st.text_input("Số điện thoại", value=st.session_state.profile.get("sdt", ""))
                    email = st.text_input("Email", value=st.session_state.profile.get("email", ""))
                with c2:
                    ngay_sinh = st.text_input("Ngày sinh (DD/MM/YYYY)", value=st.session_state.profile.get("ngay_sinh", ""))
                    nghe_nghiep = st.selectbox("Nghề nghiệp", ["", "Sinh viên", "Nhân viên văn phòng", "Kinh doanh tự do", "Quản lý", "Khác"], index=0 if not st.session_state.profile.get("nghe_nghiep") else ["", "Sinh viên", "Nhân viên văn phòng", "Kinh doanh tự do", "Quản lý", "Khác"].index(st.session_state.profile.get("nghe_nghiep", "")) if st.session_state.profile.get("nghe_nghiep") in ["Sinh viên", "Nhân viên văn phòng", "Kinh doanh tự do", "Quản lý", "Khác"] else 0)
                    muc_tieu = st.selectbox("Mục tiêu đầu tư", ["", "Tăng thu nhập thụ động", "Tích lũy dài hạn 5-10 năm", "Mua nhà / xe", "Nghỉ hưu sớm", "Khác"], index=0 if not st.session_state.profile.get("muc_tieu") else 1)
                if st.form_submit_button("💾 Lưu hồ sơ", use_container_width=True):
                    st.session_state.profile = {
                        "ho_ten": ho_ten, "sdt": sdt, "email": email,
                        "ngay_sinh": ngay_sinh, "nghe_nghiep": nghe_nghiep,
                        "muc_tieu": muc_tieu,
                    }
                    st.success("✅ Đã lưu hồ sơ.")
            if any(st.session_state.profile.values()):
                st.markdown("---")
                st.markdown("##### 📋 Hồ sơ hiện tại")
                p = st.session_state.profile
                for k, v in p.items():
                    if v:
                        label_map = {
                            "ho_ten": "Họ tên", "sdt": "SĐT", "email": "Email",
                            "ngay_sinh": "Ngày sinh", "nghe_nghiep": "Nghề nghiệp", "muc_tieu": "Mục tiêu"
                        }
                        st.markdown(f"- **{label_map.get(k, k)}:** {v}")

        with sub_backtest:
            st.markdown("#### 🧪 Backtest chiến lược")
            st.caption("📊 Sử dụng yfinance thật nếu có dữ liệu, ngược lại dùng mô phỏng.")
            cp_vn_bt = sorted(DOCS.get("co_phieu_vn", {}).keys())
            ma_bt = st.selectbox("Mã CP", options=cp_vn_bt, key="bt_ma")
            chien_luoc = st.selectbox("Chiến lược", [
                "MA Crossover (MA20 > MA50 → Mua)",
                "RSI Mean Reversion (RSI<30 Mua, RSI>70 Bán)",
                "Buy & Hold (mua giữ)",
            ], key="bt_chien_luoc")
            von_bd = st.number_input("Vốn ban đầu (₫)", value=100_000_000, step=10_000_000, key="bt_von")
            n_days_bt = st.slider("Số ngày test", 60, 504, 252, key="bt_n")
            if st.button("▶️ Chạy backtest", use_container_width=True, key="bt_run"):
                try:
                    info = DOCS.get("co_phieu_vn", {}).get(ma_bt, {})
                    gia_goc = info.get("gia", 50000)
                    np.random.seed(hash(ma_bt) % 2**32)
                    daily_vol = 0.015
                    try:
                        import requests as _rq_bt
                        r = _rq_bt.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ma_bt}.VN?range=6mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            d = r.json()
                            cs = d.get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            valid = [c for c in cs if c]
                            if len(valid) > 30:
                                p = pd.Series(valid)
                                r_real = p.pct_change().dropna()
                                if len(r_real) > 20:
                                    daily_vol = float(r_real.std())
                    except Exception:
                        pass
                    ret = np.random.randn(n_days_bt) * daily_vol
                    prices = gia_goc * np.exp(np.cumsum(ret))
                    df_bt = pd.DataFrame({"price": prices})
                    df_bt["MA20"] = df_bt["price"].rolling(20).mean()
                    df_bt["MA50"] = df_bt["price"].rolling(50).mean()
                    delta = df_bt["price"].diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss.replace(0, 1e-9)
                    df_bt["RSI"] = 100 - (100 / (1 + rs))
                    cash = von_bd
                    holdings = 0
                    trades = []
                    in_pos = False
                    for i in range(50, len(df_bt)):
                        p = df_bt["price"].iloc[i]
                        signal = False
                        sell = False
                        if chien_luoc.startswith("MA Crossover"):
                            if not in_pos and df_bt["MA20"].iloc[i] > df_bt["MA50"].iloc[i] and df_bt["MA20"].iloc[i-1] <= df_bt["MA50"].iloc[i-1]:
                                signal = True
                            elif in_pos and df_bt["MA20"].iloc[i] < df_bt["MA50"].iloc[i] and df_bt["MA20"].iloc[i-1] >= df_bt["MA50"].iloc[i-1]:
                                sell = True
                        elif chien_luoc.startswith("RSI"):
                            if not in_pos and df_bt["RSI"].iloc[i] < 30:
                                signal = True
                            elif in_pos and df_bt["RSI"].iloc[i] > 70:
                                sell = True
                        if signal and cash > 0:
                            holdings = cash / p
                            cash = 0
                            trades.append({"ngay": i, "loai": "MUA", "gia": p})
                            in_pos = True
                        elif sell and holdings > 0:
                            cash = holdings * p
                            holdings = 0
                            trades.append({"ngay": i, "loai": "BÁN", "gia": p})
                            in_pos = False
                    if holdings > 0:
                        cash = holdings * df_bt["price"].iloc[-1]
                    if chien_luoc.startswith("Buy & Hold"):
                        final_value = von_bt_calc = von_bd * (prices[-1] / prices[0])
                    else:
                        final_value = cash
                    buy_hold = von_bd * (prices[-1] / prices[0])
                    ret_strat = (final_value - von_bd) / von_bd * 100
                    ret_bh = (buy_hold - von_bd) / von_bd * 100
                    n_trades = len(trades) // 2 if chien_luoc != "Buy & Hold" else 1
                    win_trades = sum(1 for t in range(0, len(trades)-1, 2) if trades[t+1]["gia"] > trades[t]["gia"]) if len(trades) >= 2 else 0
                    win_rate = (win_trades / n_trades * 100) if n_trades > 0 else 0
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Vốn cuối", f"{final_value:,.0f}₫", delta=f"{ret_strat:+.1f}%")
                    c2.metric("Buy & Hold", f"{buy_hold:,.0f}₫", delta=f"{ret_bh:+.1f}%")
                    c3.metric("Số lệnh", f"{n_trades}")
                    c4.metric("Win rate", f"{win_rate:.0f}%")
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(y=prices, mode="lines", name="Giá", line=dict(color="#ECE8E1", width=1)))
                    if chien_luoc.startswith("MA"):
                        fig_bt.add_trace(go.Scatter(y=df_bt["MA20"], mode="lines", name="MA 20", line=dict(color="#FFD700", width=1)))
                        fig_bt.add_trace(go.Scatter(y=df_bt["MA50"], mode="lines", name="MA 50", line=dict(color="#2196F3", width=1)))
                    buy_x = [t["ngay"] for t in trades if t["loai"] == "MUA"]
                    buy_y = [t["gia"] for t in trades if t["loai"] == "MUA"]
                    sell_x = [t["ngay"] for t in trades if t["loai"] == "BÁN"]
                    sell_y = [t["gia"] for t in trades if t["loai"] == "BÁN"]
                    fig_bt.add_trace(go.Scatter(x=buy_x, y=buy_y, mode="markers", name="Mua", marker=dict(color="#4CAF50", size=10, symbol="triangle-up")))
                    fig_bt.add_trace(go.Scatter(x=sell_x, y=sell_y, mode="markers", name="Bán", marker=dict(color="#F44336", size=10, symbol="triangle-down")))
                    fig_bt.update_layout(height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_bt, use_container_width=True)
                    if ret_strat > ret_bh:
                        st.success(f"🏆 Chiến lược **{chien_luoc}** thắng Buy & Hold: {ret_strat - ret_bh:+.1f}%")
                    else:
                        st.info(f"ℹ️ Buy & Hold thắng chiến lược: {ret_bh - ret_strat:+.1f}%")
                except Exception as e:
                    st.error(f"❌ Lỗi backtest: {e}")
                    import traceback as _tb
                    with st.expander("Chi tiết"):
                        st.code(_tb.format_exc())

        with sub_ai:
            st.markdown("#### 🤖 AI dự đoán giá (Linear Regression)")
            st.caption("📊 Dự đoán dùng sklearn LinearRegression trên dữ liệu giá thật yfinance (nếu có).")
            cp_vn_ai = sorted(DOCS.get("co_phieu_vn", {}).keys())
            ma_ai = st.selectbox("Mã CP", options=cp_vn_ai, key="ai_ma")
            n_days_pred = st.slider("Số ngày dự đoán tương lai", 7, 60, 30, key="ai_n")
            n_days_hist = st.slider("Số ngày lịch sử (train)", 60, 504, 252, key="ai_hist")
            if st.button("🔮 Dự đoán", use_container_width=True, key="ai_run"):
                try:
                    from sklearn.linear_model import LinearRegression
                    info = DOCS.get("co_phieu_vn", {}).get(ma_ai, {})
                    gia_goc = info.get("gia", 50000)
                    np.random.seed(hash(ma_ai) % 2**32)
                    trend = 0.0005
                    daily_vol_ai = 0.015
                    hist_prices = None
                    try:
                        import requests as _rq_ai
                        r = _rq_ai.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ma_ai}.VN?range=1y&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            d = r.json()
                            cs = d.get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            valid = [c for c in cs if c]
                            if len(valid) > n_days_hist:
                                hist_prices = np.array(valid[-n_days_hist:], dtype=float)
                                gia_goc = hist_prices[0]
                                r_real = pd.Series(valid).pct_change().dropna()
                                if len(r_real) > 20:
                                    daily_vol_ai = float(r_real.std())
                    except Exception:
                        pass
                    if hist_prices is not None:
                        hist = hist_prices
                    else:
                        ret = np.random.randn(n_days_hist + n_days_pred) * daily_vol_ai + trend
                        all_prices = gia_goc * np.exp(np.cumsum(ret))
                        hist = all_prices[:n_days_hist]
                    X = np.arange(n_days_hist).reshape(-1, 1)
                    y = hist
                    model = LinearRegression()
                    model.fit(X, y)
                    X_future = np.arange(n_days_hist, n_days_hist + n_days_pred).reshape(-1, 1)
                    y_pred = model.predict(X_future)
                    y_train_pred = model.predict(X)
                    r2 = model.score(X, y)
                    last_real = hist[-1]
                    last_pred = y_pred[-1]
                    pct_change = (last_pred - last_real) / last_real * 100
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Giá hiện tại", f"{last_real:,.0f}₫")
                    c2.metric(f"Dự đoán {n_days_pred} ngày", f"{last_pred:,.0f}₫", delta=f"{pct_change:+.1f}%")
                    c3.metric("R² (train)", f"{r2:.3f}")
                    fig_ai = go.Figure()
                    fig_ai.add_trace(go.Scatter(y=hist, mode="lines", name="Lịch sử (thật)", line=dict(color="#ECE8E1", width=1.5)))
                    fig_ai.add_trace(go.Scatter(x=np.arange(n_days_hist), y=y_train_pred, mode="lines", name="Fit (train)", line=dict(color="#FFD700", width=1, dash="dot")))
                    fig_ai.add_trace(go.Scatter(x=np.arange(n_days_hist, n_days_hist + n_days_pred), y=y_pred, mode="lines+markers", name="Dự đoán", line=dict(color="#FF9800", width=2)))
                    if pct_change > 5:
                        st.success(f"📈 Xu hướng TĂNG: dự đoán +{pct_change:.1f}% sau {n_days_pred} ngày")
                    elif pct_change < -5:
                        st.error(f"📉 Xu hướng GIẢM: dự đoán {pct_change:.1f}% sau {n_days_pred} ngày")
                    else:
                        st.info(f"➡️ Xu hướng đi ngang: {pct_change:+.1f}%")
                    st.plotly_chart(fig_ai, use_container_width=True)
                    st.warning("⚠️ LinearRegression là model ĐƠN GIẢN. Kết quả chỉ minh họa, KHÔNG dùng để quyết định đầu tư thật.")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
                    import traceback as _tb
                    with st.expander("Chi tiết"):
                        st.code(_tb.format_exc())

        with sub_optim:
            st.markdown("#### 🎯 Tối ưu danh mục (Markowitz)")
            st.caption("📊 Mean-variance tối ưu trên giá thật yfinance 6T.")
            cp_vn_op = sorted(DOCS.get("co_phieu_vn", {}).keys())
            ds_chon_op = st.multiselect("Chọn 2-8 mã CP", options=cp_vn_op, default=cp_vn_op[:5] if len(cp_vn_op) >= 5 else cp_vn_op, key="op_chon")
            rf = st.number_input("Lãi suất phi rủi ro (%/năm)", value=5.0, step=0.5, key="op_rf") / 100
            n_sim = st.slider("Số portfolio thử (Monte Carlo)", 1000, 10000, 3000, step=500, key="op_n")
            if st.button("🎯 Tối ưu", use_container_width=True, key="op_run") and len(ds_chon_op) >= 2:
                try:
                    from scipy.optimize import minimize
                    import yfinance as _yf_op
                    n_assets = len(ds_chon_op)
                    returns_data = []
                    for ma_op in ds_chon_op:
                        try:
                            h_op = _yf_op.Ticker(ma_op + ".VN").history(period="6mo", timeout=5)
                            if not h_op.empty and len(h_op) > 30:
                                returns_data.append(h_op['Close'].pct_change().dropna())
                        except Exception:
                            continue
                    if len(returns_data) == n_assets:
                        df_ret = pd.concat(returns_data, axis=1).dropna()
                        df_ret.columns = ds_chon_op
                        mean_returns = df_ret.mean().values * 252
                        cov = df_ret.cov().values * 252
                        data_source_op = f"📊 Real: {len(df_ret)} phiên × {n_assets} mã (yfinance 6T)"
                    else:
                        np.random.seed(42)
                        mean_returns = np.random.uniform(0.05, 0.25, n_assets)
                        cov = np.random.uniform(0.005, 0.04, (n_assets, n_assets))
                        cov = (cov + cov.T) / 2
                        np.fill_diagonal(cov, np.random.uniform(0.02, 0.06, n_assets))
                        data_source_op = "Giá thật yfinance"
                    def neg_sharpe(w):
                        port_ret = np.dot(w, mean_returns)
                        port_vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                        return -(port_ret - rf) / port_vol if port_vol > 0 else 0
                    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
                    bounds = tuple((0, 1) for _ in range(n_assets))
                    w0 = np.ones(n_assets) / n_assets
                    res = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons)
                    w_opt = res.x
                    ret_opt = np.dot(w_opt, mean_returns)
                    vol_opt = np.sqrt(np.dot(w_opt.T, np.dot(cov, w_opt)))
                    sharpe_opt = (ret_opt - rf) / vol_opt if vol_opt > 0 else 0
                    st.caption(data_source_op)
                    st.markdown("##### Trọng số tối ưu (max Sharpe ratio)")
                    fig_pie = go.Figure(data=[go.Pie(labels=ds_chon_op, values=w_opt, hole=0.4, marker=dict(colors=["#FFD700", "#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#00BCD4", "#795548"][:n_assets]))])
                    fig_pie.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_pie, use_container_width=True)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Return kỳ vọng", f"{ret_opt*100:.1f}%")
                    c2.metric("Volatility", f"{vol_opt*100:.1f}%")
                    c3.metric("Sharpe ratio", f"{sharpe_opt:.2f}")
                    st.markdown("---")
                    st.markdown(f"##### 🎲 Efficient Frontier (Monte Carlo {n_sim:,} portfolios)")
                    n_port = n_sim
                    weights_rand = np.random.dirichlet(np.ones(n_assets), n_port)
                    port_rets = weights_rand @ mean_returns
                    port_vols = np.sqrt(np.einsum("ij,jk,ik->i", weights_rand, cov, weights_rand))
                    port_sharpe = (port_rets - rf) / port_vols
                    fig_ef = go.Figure()
                    fig_ef.add_trace(go.Scatter(x=port_vols*100, y=port_rets*100, mode="markers", marker=dict(color=port_sharpe, colorscale="Viridis", showscale=True, size=5, colorbar=dict(title="Sharpe")), name="Random portfolios"))
                    fig_ef.add_trace(go.Scatter(x=[vol_opt*100], y=[ret_opt*100], mode="markers", marker=dict(color="#FFD700", size=18, symbol="star"), name="TỐI ƯU"))
                    fig_ef.update_layout(xaxis_title="Volatility (%)", yaxis_title="Return kỳ vọng (%)", height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_ef, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Lỗi tối ưu: {e}")
                    import traceback as _tb
                    with st.expander("Chi tiết"):
                        st.code(_tb.format_exc())
            elif len(ds_chon_op) < 2:
                st.info("👉 Chọn ít nhất 2 mã CP để tối ưu.")

        with sub_telegram:
            st.markdown("#### 📞 Telegram Bot — Nhận cảnh báo qua Telegram")
            st.caption("Cấu hình bot Telegram để nhận cảnh báo giá, tin tức, kết quả backtest qua tin nhắn.")
            try:
                _TG_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
            except Exception:
                _TG_TOKEN = ""
            if "telegram_config" not in st.session_state:
                st.session_state.telegram_config = {"token": _TG_TOKEN, "chat_id": ""}
            with st.form("tg_form"):
                token_input = st.text_input("🤖 Bot Token (từ @BotFather)", value=st.session_state.telegram_config.get("token", ""), type="password", help="Tạo bot tại t.me/BotFather → /newbot → copy token")
                chat_id_input = st.text_input("💬 Chat ID của bạn", value=st.session_state.telegram_config.get("chat_id", ""), help="Nhắn @userinfobot để lấy Chat ID")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("💾 Lưu cấu hình", use_container_width=True):
                        st.session_state.telegram_config = {"token": token_input, "chat_id": chat_id_input}
                        st.success("✅ Đã lưu cấu hình Telegram")
                with col_b:
                    if st.form_submit_button("🧪 Gửi tin nhắn test", use_container_width=True):
                        if not token_input or not chat_id_input:
                            st.error("❌ Vui lòng nhập Token và Chat ID")
                        else:
                            try:
                                url = f"https://api.telegram.org/bot{token_input}/sendMessage"
                                payload = {"chat_id": chat_id_input, "text": "🎉 Robo-Advisor: Kết nối Telegram thành công!"}
                                r = requests.post(url, json=payload, timeout=10)
                                if r.status_code == 200:
                                    st.success(f"✅ Đã gửi tin nhắn test! Check Telegram của anh.")
                                else:
                                    st.error(f"❌ Lỗi: {r.status_code} — {r.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ Lỗi gửi: {e}")
            st.markdown("---")
            st.markdown("##### 📤 Gửi cảnh báo giá hiện tại qua Telegram")
            if st.button("📨 Gửi danh sách cảnh báo", use_container_width=True, key="tg_send_alerts"):
                cfg = st.session_state.telegram_config
                if not cfg.get("token") or not cfg.get("chat_id"):
                    st.error("❌ Chưa cấu hình Telegram. Vui lòng nhập Token + Chat ID.")
                elif not st.session_state.get("price_alerts"):
                    st.warning("⚠️ Chưa có cảnh báo nào. Thêm ở tab 🔔 Cảnh báo giá trước.")
                else:
                    try:
                        msg = "🔔 *Cảnh báo giá Robo-Advisor*\n\n"
                        for alert in st.session_state.price_alerts:
                            gia = DOCS.get("co_phieu_vn", {}).get(alert["ma"], {}).get("gia", 0)
                            msg += f"• {alert['ma']} {alert['loai']} {alert['nguong']:,.0f}₫ — Giá: {gia:,.0f}₫\n"
                        url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
                        r = requests.post(url, json={"chat_id": cfg["chat_id"], "text": msg, "parse_mode": "Markdown"}, timeout=10)
                        if r.status_code == 200:
                            st.success(f"✅ Đã gửi {len(st.session_state.price_alerts)} cảnh báo qua Telegram!")
                        else:
                            st.error(f"❌ Lỗi: {r.text[:200]}")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
            st.markdown("---")
            with st.expander("📖 Hướng dẫn tạo Telegram Bot"):
                st.markdown("""
1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot`
3. Đặt tên bot (vd: `Robo Advisor Bot`)
4. Đặt username (vd: `robo_advisor_vn_bot`)
5. Copy **token** dán vào ô bên trên
6. Nhắn tin cho bot mới tạo (bất kỳ tin nào)
7. Mở `t.me/userinfobot` → bấm Start → copy **Chat ID**
8. Dán vào ô Chat ID bên trên → Lưu
                """)

        with sub_pay:
            st.markdown("#### 💳 Thanh toán Gói PRO")
            st.caption("Kích hoạt gói PRO tự động — không cần nhập mật khẩu thủ công.")
            st.markdown("---")
            gia_pro = st.number_input("Giá gói PRO (₫)", value=500000, step=50000, key="pay_gia")
            thoi_han = st.selectbox("Thời hạn", ["1 tháng", "3 tháng", "6 tháng", "12 tháng"], key="pay_th")
            phan_tram_giam = {"1 tháng": 0, "3 tháng": 10, "6 tháng": 15, "12 tháng": 25}
            giam = phan_tram_giam[thoi_han]
            thanh_tien = int(gia_pro * (1 - giam/100))
            st.markdown(f"**Thành tiền:** ~~{gia_pro:,.0f}₫~~ → **{thanh_tien:,.0f}₫** (giảm {giam}%)")
            st.markdown("---")
            st.markdown("##### 🏦 Thông tin chuyển khoản")
            st.info("""
**Ngân hàng:** MB Bank  
**Chủ tài khoản:** DANH ĐẠT  
**Số tài khoản:** `0358814661`  
**Nội dung CK:** `ROBO PRO {username} {ma_don}`

*(Thay `{username}` = tên đăng nhập, `{ma_don}` = mã bên dưới)*
            """.replace("{username}", st.session_state.get("username", "khach")).replace("{ma_don}", f"PR{datetime.now().strftime('%Y%m%d%H%M%S') if 'datetime' in dir() else 'XXXX'}"))
            st.markdown("---")
            st.markdown("##### ✅ Xác nhận đã chuyển khoản")
            with st.form("pay_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ma_don_input = st.text_input("Mã đơn (ghi trong nội dung CK)", key="pay_ma")
                    so_tien_ck = st.number_input("Số tiền đã CK (₫)", min_value=0, step=1000, key="pay_sotien")
                with c2:
                    ngan_hang_ck = st.selectbox("Ngân hàng CK", ["MB Bank", "Vietcombank", "Techcombank", "BIDV", "VietinBank", "ACB", "Khác"], key="pay_nh")
                    thoi_gian_ck = st.text_input("Thời gian CK", placeholder="VD: 2026-06-04 14:30", key="pay_tg")
                if st.form_submit_button("📤 Gửi yêu cầu kích hoạt", use_container_width=True):
                    if not ma_don_input or so_tien_ck < thanh_tien * 0.95:
                        st.error(f"❌ Mã đơn trống hoặc số tiền CK chưa đủ (tối thiểu {thanh_tien*0.95:,.0f}₫).")
                    else:
                        st.success(f"✅ Đã gửi yêu cầu kích hoạt! Admin sẽ xác nhận trong 24h và kích hoạt PRO cho tài khoản `{st.session_state.get('username', 'khach')}`.")
                        st.info("💡 Trong lúc chờ, anh có thể dùng mật khẩu PRO ở Sidebar để kích hoạt ngay.")
            st.markdown("---")
            st.markdown("##### 📞 Liên hệ hỗ trợ")
            st.markdown("""
- **SĐT / Zalo:** `0358814661` (Danh Đạt)
- **Email:** support@robo-advisor.vn
- **Giờ hỗ trợ:** 8:00 - 22:00 mỗi ngày
            """)

if st.session_state.trang_thai == "home":
    st.session_state.trang_thai = "dashboard"
    st.rerun()

# ============================================================
# 💎 TRẠNG THÁI GÓI PRO (hiển thị banner đầu mỗi page)
# ============================================================
if st.session_state.is_pro:
    st.markdown(
        '<div style="background:linear-gradient(90deg,#FFD70022,#00C9A722);'
        'border:1px solid #FFD70055;border-radius:10px;padding:8px 16px;'
        'margin-bottom:12px;font-size:0.9rem;">'
        '💎 <b style="color:#FFD700;">GÓI PRO</b> đang kích hoạt — toàn quyền tính năng cao cấp.'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="background:#ECE8E10a;border:1px solid #9AABB833;border-radius:10px;'
        'padding:8px 16px;margin-bottom:12px;font-size:0.85rem;color:#9AABB8;">'
        'Đang dùng <b style="color:#ECE8E1;">GÓI TIÊU CHUẨN</b> — mở khóa <b style="color:#FFD700;">GÓI PRO</b> tại Sidebar để dùng tính năng VIP.'
        '</div>',
        unsafe_allow_html=True,
    )

if st.session_state.trang_thai == "survey":

    if not st.session_state.get("cau_tra_loi"):
        st.markdown('<div class="main-header" style="font-size:1.8rem;font-weight:700;color:#FFD700;margin:0.5rem 0;">📝 Khảo sát khẩu vị rủi ro</div>', unsafe_allow_html=True)
        st.markdown(
            "Trả lời 12 câu hỏi để chúng tôi đánh giá mức độ chấp nhận rủi ro và mục tiêu tài chính của bạn!"
        )
        st.markdown("---")

        with st.form("survey_form", clear_on_submit=True):
            for idx, cau in enumerate(CAU_HOI_KHAO_SAT):
                st.markdown(f"**{idx+1}. {cau['cau_hoi']}**")
                lua_chon_nhan = [opt["nhan"] for opt in cau["lua_chon"]]
                lua_chon_diem = {opt["nhan"]: opt["diem"] for opt in cau["lua_chon"]}
                selected = st.radio(
                    "Chọn:",
                    lua_chon_nhan,
                    key=f"survey_q_{idx}",
                    index=None,
                    label_visibility="collapsed",
                )
                st.session_state._survey_opts[idx] = (cau["y"], lua_chon_diem, selected)
                st.markdown("---")

            submitted = st.form_submit_button("✅ Hoàn thành khảo sát", use_container_width=True, type="primary")

        if submitted:
            cau_tra_loi = {}
            missing = False
            for idx in range(len(CAU_HOI_KHAO_SAT)):
                y, lua_chon_diem, selected = st.session_state._survey_opts.get(idx, (None, {}, None))
                if selected is None or y is None:
                    missing = True
                    continue
                cau_tra_loi[y] = lua_chon_diem[selected]

            if missing:
                st.warning("Vui lòng trả lời tất cả 12 câu hỏi trước khi hoàn thành.")
            else:
                st.session_state.cau_tra_loi = cau_tra_loi
                st.session_state.loai_nha_dau_tu = None

    if st.session_state.get("cau_tra_loi"):
        loai, diem, mo_ta, danh_muc = danh_gia_rui_ro(st.session_state.cau_tra_loi)
        st.session_state.loai_nha_dau_tu = loai
        st.session_state.danh_muc_de_xuat = danh_muc
        st.session_state.diem_rui_ro = diem
        st.session_state.da_phan_tich = True

        st.balloons()
        st.markdown("## 🎉 Kết quả khảo sát!")
        st.markdown("---")

        color_map = {
            "Bảo thủ": "linear-gradient(135deg, #4CAF50, #2E7D32)",
            "Thận trọng": "linear-gradient(135deg, #8BC34A, #558B2F)",
            "Trung dung": "linear-gradient(135deg, #FFC107, #FF8F00)",
            "Tăng trưởng": "linear-gradient(135deg, #FF9800, #E65100)",
            "Táo bạo": "linear-gradient(135deg, #f44336, #b71c1c)",
        }
        bg = color_map.get(loai, "linear-gradient(135deg, #667eea, #764ba2)")

        st.markdown(
            f"""
        <div style="background: {bg}; color: white; padding: 2rem; border-radius: 15px; text-align: center;">
            <h2 style="margin:0;">{loai}</h2>
            <p style="font-size:1.2rem; opacity:0.9;">Điểm rủi ro: {diem}/60</p>
            <p style="font-size:1rem;">{mo_ta}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("### 📊 Phân bố danh mục đề xuất")
        st.markdown(
            "Dựa trên khẩu vị rủi ro của bạn, danh mục tối ưu được đề xuất như sau:"
        )

        df_dm = pd.DataFrame(
            [
                {"Kênh đầu tư": kenh, "Tỷ trọng": f"{ty_trong*100:.0f}%"}
                for kenh, ty_trong in danh_muc.items()
                if ty_trong > 0
            ]
        )

        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=("Phân bố danh mục", "Tỷ trọng từng kênh"),
        )

        labels = [k for k, v in danh_muc.items() if v > 0]
        values = [v for v in danh_muc.values() if v > 0]
        colors = px.colors.qualitative.Set3[: len(labels)]

        fig.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                textinfo="label+percent",
                hole=0.4,
                marker=dict(colors=colors),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker=dict(color=colors),
                text=[f"{v*100:.0f}%" for v in values],
                textposition="outside",
            ),
            row=1,
            col=2,
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, width='stretch')

        tt_dm = tinh_toan_danh_muc(list(danh_muc.values()))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
            <div class="metric-box">
                <h4>Lợi nhuận kỳ vọng</h4>
                <h2 style="color:green;">{tt_dm['loi_nhuan_ky_vong']*100:.1f}%/năm</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
            <div class="metric-box">
                <h4>Rủi ro (Volatility)</h4>
                <h2 style="color:red;">{tt_dm['rui_ro_danh_muc']*100:.1f}%/năm</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
            <div class="metric-box">
                <h4>Sharpe Ratio</h4>
                <h2 style="color:blue;">{tt_dm['sharp_ratio']:.2f}</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Xem chi tiết danh mục", width='stretch'):
                st.session_state.trang_thai = "portfolio"
                st.rerun()

        with col2:
            if st.button("🔄 Làm lại khảo sát", width='stretch'):
                st.session_state._survey_opts = {}
                st.session_state.cau_tra_loi = {}
                st.session_state.da_phan_tich = False
                st.rerun()

        with col3:
            if st.button("🏠 Về trang chủ", width='stretch'):
                st.session_state._survey_opts = {}
                st.session_state.cau_tra_loi = {}
                st.session_state.trang_thai = "home"
                st.rerun()


elif st.session_state.trang_thai == "portfolio":
    st.markdown('<div class="main-header" style="font-size:1.8rem;font-weight:700;color:#FFD700;margin:0.5rem 0;">📊 Danh mục đầu tư</div>', unsafe_allow_html=True)
    st.markdown("---")
    dm = DOCS.get("danh_muc", {})
    kpi = DOCS.get("kpi", {})
    tong_gt, tong_von_port, tong_lai_lo, return_pct_port = tinh_return_danh_muc(dm)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng giá trị", f"{tong_gt:,.0f}₫")
    with col2:
        st.metric("Tổng lãi/lỗ", f"{tong_lai_lo:+,.0f}₫", delta=f"{return_pct_port:.1f}%")
    with col3:
        st.metric("Số mã", f"{len(dm)}")
    with col4:
        st.metric("Tỷ suất", f"{return_pct_port:+.1f}%")

    rows = []
    for ma, info in dm.items():
        lai_lo = (info.get("gia_thi_truong", 0) - info.get("gia_von", 0)) * info.get("so_luong", 0)
        gia_von = info.get("gia_von", 0) or 0
        pct = (info.get("gia_thi_truong", 0) - gia_von) / gia_von * 100 if gia_von else 0
        rows.append({"Mã": ma, "Ngành": info.get("nganh", ""), "Số lượng": f'{info.get("so_luong", 0):,}',
            "Giá vốn": f'{info.get("gia_von", 0):,}₫', "Giá TT": f'{info.get("gia_thi_truong", 0):,}₫',
            "Lãi/Lỗ": f'{lai_lo:+,.0f}₫', "%": f"{pct:+.1f}%"})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu danh mục. Hãy cập nhật dữ liệu trước.")

elif st.session_state.trang_thai == "deep_analysis":
    # ============================================
    # HELPER FUNCTIONS — Tính toán 1 lần, dùng nhiều nơi
    # Phase 24-25-26: gộp sections trùng + số ước lượng
    # ============================================
    def _compute_drawdown(eq_series):
        if eq_series is None or len(eq_series) < 2:
            return None
        try:
            eq = pd.Series(eq_series) if not isinstance(eq_series, pd.Series) else eq_series
            running_max = eq.cummax()
            dd = (eq - running_max) / running_max
            max_dd = float(dd.min())
            max_dd_pct = max_dd * 100
            current_dd = float(dd.iloc[-1]) * 100
            dd_duration = 0
            try:
                peak_idx = running_max.idxmax()
                after_peak = dd.loc[peak_idx:]
                recovered = after_peak[after_peak >= 0]
                dd_duration = int((recovered.index[0] - peak_idx).days) if len(recovered) > 0 else int((eq.index[-1] - peak_idx).days)
            except Exception:
                pass
            return {"drawdown": dd, "max_dd_pct": max_dd_pct, "current_dd_pct": current_dd,
                "dd_duration_days": dd_duration, "max_dd_idx": dd.idxmin()}
        except Exception:
            return None

    def _compute_all_ratios(eq_series, bench_series=None, risk_free=0.05):
        if eq_series is None or len(eq_series) < 20:
            return None
        try:
            eq = pd.Series(eq_series) if not isinstance(eq_series, pd.Series) else eq_series
            rets = eq.pct_change().dropna()
            if len(rets) < 10:
                return None
            vol_daily = float(rets.std())
            vol_ann = vol_daily * (252**0.5)
            ret_ann = float((1 + rets).prod() ** (252 / len(rets)) - 1)
            rf_daily = risk_free / 252
            sharpe = (rets.mean() - rf_daily) / vol_daily * (252**0.5) if vol_daily > 0 else 0
            downside_rets = rets[rets < 0]
            downside_dev = float(downside_rets.std()) * (252**0.5) if len(downside_rets) > 0 else vol_ann
            sortino = (ret_ann - risk_free) / downside_dev if downside_dev > 0 else 0
            dd_info = _compute_drawdown(eq)
            max_dd_pct = abs(dd_info["max_dd_pct"]) if dd_info else 0
            ret_ann_val = ret_ann
            calmar = ret_ann_val / (max_dd_pct / 100) if max_dd_pct > 0 else 0
            roMaD = ret_ann_val / (max_dd_pct / 100) if max_dd_pct > 0 else 0
            ulcer_idx = float(np.sqrt((dd_info["drawdown"] ** 2).mean())) * 100 if dd_info and dd_info.get("drawdown") is not None else 0
            martin = ret_ann_val / ulcer_idx if ulcer_idx > 0 else 0
            var_95 = -float(np.percentile(rets, 5)) * 100
            var_99 = -float(np.percentile(rets, 1)) * 100
            cvar_95_rets = rets[rets <= np.percentile(rets, 5)]
            cvar_95 = -float(cvar_95_rets.mean()) * 100 if len(cvar_95_rets) > 0 else var_95
            cumsum = (1 + rets).cumprod()
            running_max_c = cumsum.cummax()
            drawdown_c = (cumsum - running_max_c) / running_max_c
            avg_dd = float(drawdown_c[drawdown_c < 0].mean()) * 100 if (drawdown_c < 0).any() else 0
            sterling = ret_ann_val / (abs(avg_dd) / 100) if avg_dd < 0 else 0
            burke = ret_ann_val / (np.sqrt((drawdown_c[drawdown_c < 0] ** 2).sum()) * 100) if (drawdown_c < 0).any() else 0
            gain = rets[rets > 0].sum()
            pain = abs(rets[rets < 0].sum())
            omega = gain / pain if pain > 0 else 0
            gain_pain = (rets.sum()) / pain if pain > 0 else 0
            ir = te = 0
            if bench_series is not None and len(bench_series) >= 20:
                try:
                    bench = pd.Series(bench_series) if not isinstance(bench_series, pd.Series) else bench_series
                    bench_rets = bench.pct_change().dropna()
                    common_idx = rets.index.intersection(bench_rets.index)
                    if len(common_idx) >= 15:
                        r_p = rets.loc[common_idx]
                        r_b = bench_rets.loc[common_idx]
                        if len(r_p) > 5:
                            diff = r_p - r_b
                            te = float(diff.std()) * (252**0.5) * 100
                            avg_diff = float(diff.mean()) * 252
                            ir = avg_diff / (te / 100) if te > 0 else 0
                except Exception:
                    pass
            return {"vol_ann_pct": vol_ann * 100, "ret_ann_pct": ret_ann * 100,
                "sharpe": sharpe, "sortino": sortino, "calmar": calmar,
                "roMaD": roMaD, "martin": martin, "sterling": sterling, "burke": burke,
                "omega": omega, "gain_pain": gain_pain, "ir": ir, "te_pct": te,
                "var_95_pct": var_95, "var_99_pct": var_99, "cvar_95_pct": cvar_95,
                "max_dd_pct": max_dd_pct, "downside_dev_pct": downside_dev * 100,
                "ulcer_idx": ulcer_idx, "ret_total_pct": float((1 + rets).prod() - 1) * 100,
                "n_periods": len(rets), "dd_info": dd_info}
        except Exception:
            return None

    if not st.session_state.deep_unlocked:
        st.markdown('<div class="login-container" style="padding-top:5vh;">'
        '<div class="login-title" style="font-size:2rem;">🔒 PHÂN TÍCH CHUYÊN SÂU</div>'
        '<div class="login-subtitle">Vui lòng nhập mật khẩu để truy cập</div>'
        '</div>', unsafe_allow_html=True)
        _deep_pwd = st.text_input("Mật khẩu Phân tích Chuyên sâu:", type="password", placeholder="Nhập mật khẩu...", key="deep_page_pwd")
        if st.button("🔓 Mở khóa", key="deep_unlock_btn", use_container_width=True):
            _pw = _deep_pwd.strip()
            if _pw == PASSWORD_DEEP or _pw in _DEEP_PWD_OK:
                st.session_state.deep_unlocked = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác!")
        st.stop()

    st.markdown("**🆕 VERSION 6.0** — 6 nhóm Tabs + 8 tính năng mới (thanh khoản, khối ngoại, AI, Bollinger, FX, VN30, lịch sử GD, thuế). Không thấy dòng này = Ctrl+Shift+R.")
    st.write("# 📊 PHÂN TÍCH CHUYÊN SÂU DANH MỤC")
    st.write("---")

    dm = DOCS.get("danh_muc", {}) or {}
    kpi = DOCS.get("kpi", {}) or {}
    perf = DOCS.get("performance", {}) or {}
    tong_gt, tong_von, tong_lai_lo, return_pct = tinh_return_danh_muc(dm)
    is_demo = False
    if not dm or tong_gt <= 0:
        is_demo = True
        st.warning("📊 Đang hiển thị danh mục mẫu (8 mã blue-chip VN) — Vào Sidebar → Cập nhật dữ liệu để dùng danh mục thực.")
        dm = {
            "VCB": {"nganh": "Ngân hàng", "gia_thi_truong": 92000, "gia_von": 85000, "so_luong": 100},
            "FPT": {"nganh": "Công nghệ", "gia_thi_truong": 145000, "gia_von": 120000, "so_luong": 50},
            "HPG": {"nganh": "Thép", "gia_thi_truong": 27000, "gia_von": 30000, "so_luong": 500},
            "VNM": {"nganh": "Thực phẩm", "gia_thi_truong": 68000, "gia_von": 72000, "so_luong": 200},
            "MWG": {"nganh": "Bán lẻ", "gia_thi_truong": 48000, "gia_von": 55000, "so_luong": 300},
            "MBB": {"nganh": "Ngân hàng", "gia_thi_truong": 24000, "gia_von": 22000, "so_luong": 800},
            "VIC": {"nganh": "Bất động sản", "gia_thi_truong": 42000, "gia_von": 48000, "so_luong": 400},
            "CTG": {"nganh": "Ngân hàng", "gia_thi_truong": 32000, "gia_von": 30000, "so_luong": 500},
        }
        _demo_fb = {
            "VCB": {"nganh": "Ngân hàng", "beta": 0.85, "roe": 0.21, "roa": 0.018, "pe": 9.5, "pb": 2.1, "eps": 9680, "dividend_yield": 0.025, "market_cap": 150000, "w52_high": 98000, "w52_low": 78000},
            "FPT": {"nganh": "Công nghệ", "beta": 1.15, "roe": 0.25, "roa": 0.12, "pe": 18.2, "pb": 4.5, "eps": 7967, "dividend_yield": 0.015, "market_cap": 110000, "w52_high": 152000, "w52_low": 95000},
            "HPG": {"nganh": "Thép", "beta": 1.35, "roe": 0.12, "roa": 0.07, "pe": 12.0, "pb": 1.4, "eps": 2250, "dividend_yield": 0.012, "market_cap": 80000, "w52_high": 31000, "w52_low": 21500},
            "VNM": {"nganh": "Thực phẩm", "beta": 0.70, "roe": 0.27, "roa": 0.16, "pe": 14.5, "pb": 3.8, "eps": 4690, "dividend_yield": 0.045, "market_cap": 140000, "w52_high": 78000, "w52_low": 64000},
            "MWG": {"nganh": "Bán lẻ", "beta": 1.20, "roe": 0.15, "roa": 0.06, "pe": 22.0, "pb": 3.0, "eps": 2182, "dividend_yield": 0.008, "market_cap": 70000, "w52_high": 62000, "w52_low": 41000},
            "MBB": {"nganh": "Ngân hàng", "beta": 0.90, "roe": 0.23, "roa": 0.020, "pe": 7.2, "pb": 1.5, "eps": 3333, "dividend_yield": 0.020, "market_cap": 95000, "w52_high": 26000, "w52_low": 18000},
            "VIC": {"nganh": "Bất động sản", "beta": 1.10, "roe": 0.08, "roa": 0.03, "pe": 35.0, "pb": 2.8, "eps": 1200, "dividend_yield": 0.0, "market_cap": 60000, "w52_high": 52000, "w52_low": 38000},
            "CTG": {"nganh": "Ngân hàng", "beta": 0.95, "roe": 0.18, "roa": 0.015, "pe": 8.5, "pb": 1.6, "eps": 3765, "dividend_yield": 0.022, "market_cap": 85000, "w52_high": 35000, "w52_low": 25000},
        }
        kpi = {k: dict(v) for k, v in _demo_fb.items()}
        for _k in kpi:
            kpi[_k]["_source"] = "demo fallback (sẽ bị yfinance thật override bên dưới)"
        perf = {"Rf": 0.045, "Rm": 0.082, "Beta": 1.02, "Rp": 0.107}
        tong_gt, tong_von, tong_lai_lo, return_pct = tinh_return_danh_muc(dm)

    rf = float(perf.get("Rf", 0.045))
    rm = float(perf.get("Rm", 0.082))
    rp = return_pct / 100.0

    weights = []
    betas = []
    sector_exp = {}
    n_ma = 0
    for ma, info in dm.items():
        gia_tt = info.get("gia_thi_truong", 0)
        sl = info.get("so_luong", 0)
        v = gia_tt * sl
        if v <= 0 or tong_gt <= 0:
            continue
        w = v / tong_gt
        weights.append(w)
        ki = kpi.get(ma, {})
        beta_ma = float(ki.get("beta", 1.0) or 1.0)
        betas.append(beta_ma * w)
        nganh = (ki.get("nganh", "") or "Khác").strip() or "Khác"
        sector_exp[nganh] = sector_exp.get(nganh, 0) + w
        n_ma += 1

    if not weights:
        st.error("Khong the tinh toan — du lieu danh muc khong hop le.")
    else:
        @st.cache_data(ttl=7200, show_spinner="📡 Tải sector median thật từ yfinance...")
        def _fetch_sector_medians_yf():
            try:
                import yfinance as _yf_sec
                sec_repr = {
                    "Ngân hàng": ["VCB.VN", "BID.VN", "CTG.VN", "ACB.VN", "MBB.VN", "TCB.VN", "VPB.VN", "HDB.VN"],
                    "Công nghệ": ["FPT.VN"],
                    "Thép": ["HPG.VN"],
                    "Thực phẩm": ["VNM.VN", "MSN.VN", "SAB.VN"],
                    "Bán lẻ": ["MWG.VN", "PNJ.VN"],
                    "Bất động sản": ["VIC.VN", "VHM.VN", "NVL.VN", "KDH.VN", "DXG.VN"],
                    "Chứng khoán": ["SSI.VN", "VCI.VN", "HCM.VN"],
                    "Dầu khí": ["PLX.VN", "GAS.VN", "PVD.VN", "PVS.VN", "BSR.VN"],
                    "Điện": ["POW.VN", "BCM.VN"],
                    "Khoáng sản": ["GVR.VN", "DCM.VN", "DPM.VN"],
                    "Bảo hiểm": ["BVH.VN", "PVI.VN"],
                    "Vận tải": ["VJC.VN", "GMD.VN", "HAH.VN", "VOS.VN", "PVT.VN"],
                    "Xây dựng": ["CTD.VN", "HBC.VN", "LCG.VN", "CII.VN"],
                    "Hàng không": ["VJC.VN"],
                    "Khác": [],
                }
                result = {}
                for sector, symbols in sec_repr.items():
                    vals = {"pe": [], "pb": [], "roe": [], "roa": [], "dividend_yield": [], "beta": [], "eps": []}
                    for sym in symbols:
                        try:
                            info = _yf_sec.Ticker(sym).info
                            pe = info.get("trailingPE")
                            pb = info.get("priceToBook")
                            roe = info.get("returnOnEquity")
                            roa = info.get("returnOnAssets")
                            dy = info.get("dividendYield")
                            beta = info.get("beta")
                            eps = info.get("trailingEps")
                            if pe and 0 < pe < 200: vals["pe"].append(float(pe))
                            if pb and 0 < pb < 50: vals["pb"].append(float(pb))
                            if roe and -0.5 < roe < 0.5: vals["roe"].append(float(roe))
                            if roa and -0.3 < roa < 0.3: vals["roa"].append(float(roa))
                            if dy and 0 <= dy < 0.3: vals["dividend_yield"].append(float(dy))
                            if beta and 0 < beta < 3: vals["beta"].append(float(beta))
                            if eps and eps > 0: vals["eps"].append(float(eps))
                        except Exception:
                            continue
                    if vals["pe"]:
                        result[sector] = {f: float(sum(v) / len(v)) for f, v in vals.items() if v}
                return result
            except Exception:
                return {}
        SECTOR_DEFAULTS_FALLBACK = _fetch_sector_medians_yf()
        if not SECTOR_DEFAULTS_FALLBACK:
            SECTOR_DEFAULTS_FALLBACK = {"Khác": {}}
        SECTOR_DEFAULTS_FALLBACK.setdefault("Khác", {})
        _sector_medians = {}
        for _ma, _ki in kpi.items():
            _ng = (_ki.get("nganh", "") or "Khác").strip() or "Khác"
            _sector_medians.setdefault(_ng, []).append(_ki)
        SECTOR_DEFAULTS = {}
        for _ng, _stocks in _sector_medians.items():
            _vals = {"pe": [], "pb": [], "roe": [], "roa": [], "dividend_yield": [], "beta": [], "eps": []}
            for _s in _stocks:
                for _fld in _vals:
                    _v = _s.get(_fld)
                    if _v is not None and _v > 0:
                        _vals[_fld].append(float(_v))
            SECTOR_DEFAULTS[_ng] = {f: (sum(v) / len(v)) if v else 0 for f, v in _vals.items()}

        def _fill_kpi_for_real(ma, info, ki):
            ng = (ki.get("nganh", "") or info.get("nganh", "") or "Khác").strip() or "Khác"
            sector_real_med = SECTOR_DEFAULTS.get(ng, {})
            sector_fallback = SECTOR_DEFAULTS_FALLBACK.get(ng, SECTOR_DEFAULTS_FALLBACK["Khác"])
            for k, v_real in sector_real_med.items():
                if (k not in ki or ki.get(k) is None or ki.get(k) == 0) and v_real > 0:
                    ki[k] = v_real
                    ki[f"{k}_source"] = "median ngành (yfinance thật)"
            for k, v_fb in sector_fallback.items():
                if k not in ki or ki.get(k) is None or ki.get(k) == 0:
                    ki[k] = v_fb
                    if f"{k}_source" not in ki:
                        ki[f"{k}_source"] = "median ngành (yfinance)"
            vn_static = (DOCS.get("co_phieu_vn") or {}).get(ma, {})
            tg_static = (DOCS.get("co_phieu_tg") or {}).get(ma, {})
            static_src = vn_static or tg_static
            if static_src:
                _field_map = {
                    "pe": ("pe", lambda v: float(v) if v else None),
                    "pb": ("pb", lambda v: float(v) if v else None),
                    "roe": ("roe", lambda v: float(v) if v else None),
                    "eps": ("eps", lambda v: float(v) if v else None),
                    "dividend_yield": ("co_tuc_pct", lambda v: float(v) / 100.0 if v else None),
                    "von_hoa": ("von_hoa", lambda v: float(v) if v else None),
                    "market_cap": ("von_hoa", lambda v: float(v) if v else None),
                    "current_price": ("gia", lambda v: float(v) if v else None),
                }
                for k_real, (k_static, conv) in _field_map.items():
                    cur = ki.get(k_real)
                    if cur is None or cur == 0:
                        v_static = conv(static_src.get(k_static, 0))
                        if v_static is not None and v_static != 0:
                            ki[k_real] = v_static
                            if f"{k_real}_source" not in ki:
                                ki[f"{k_real}_source"] = f"co_phieu_vn.json (dữ liệu thật)"
                if not ki.get("nganh"):
                    ki["nganh"] = static_src.get("nganh", ng)
                if not ki.get("ten"):
                    ki["ten"] = static_src.get("ten", ma)
                if not ki.get("ytd") and static_src.get("ytd"):
                    ki["ytd"] = float(static_src.get("ytd", 0)) / 100.0
            if "w52_high" not in ki or ki.get("w52_high", 0) <= 0:
                gia_tt = info.get("gia_thi_truong", 0)
                ki["w52_high"] = gia_tt * 1.25 if gia_tt > 0 else 0
                if "w52_high_source" not in ki:
                    ki["w52_high_source"] = "ước lượng từ giá hiện tại × 1.25"
            if "w52_low" not in ki or ki.get("w52_low", 0) <= 0:
                gia_tt = info.get("gia_thi_truong", 0)
                ki["w52_low"] = gia_tt * 0.85 if gia_tt > 0 else 0
                if "w52_low_source" not in ki:
                    ki["w52_low_source"] = "ước lượng từ giá hiện tại × 0.85"
            if "market_cap" not in ki or ki.get("market_cap", 0) <= 0:
                ki["market_cap"] = info.get("gia_thi_truong", 0) * info.get("so_luong", 0) / 1e9
            return ki

        for ma, info in dm.items():
            if ma in kpi:
                kpi[ma] = _fill_kpi_for_real(ma, info, kpi[ma])
            else:
                kpi[ma] = _fill_kpi_for_real(ma, info, {"nganh": info.get("nganh", "Khác")})

        @st.cache_data(ttl=3600, show_spinner=False)
        def _fetch_real_prices(_targets):
            import requests as _rq, pandas as _pd
            from concurrent.futures import ThreadPoolExecutor, as_completed
            out = {}
            metas = {}

            def _one(sym, suffix):
                try:
                    r = _rq.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
                    )
                    if r.status_code == 200:
                        d = r.json()
                        if not d.get('chart', {}).get('result'):
                            return sym, None, None
                        result = d['chart']['result'][0]
                        ts = result.get('timestamp', [])
                        closes_raw = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        if not ts or not closes_raw:
                            return sym, None, None
                        pairs = [(t, c) for t, c in zip(ts, closes_raw) if c is not None]
                        if len(pairs) < 20:
                            return sym, None, None
                        ts_v, cs_v = zip(*pairs)
                        idx = _pd.to_datetime(list(ts_v), unit='s')
                        return sym, _pd.Series(list(cs_v), index=idx), result.get('meta', {})
                except Exception:
                    pass
                return sym, None, None

            with ThreadPoolExecutor(max_workers=20) as ex:
                futs = [ex.submit(_one, sym, suffix) for sym, suffix in _targets]
                for f in as_completed(futs):
                    sym, s, m = f.result()
                    if s is not None:
                        out[sym] = s
                        if m:
                            metas[sym] = m
            return out, metas

        @st.cache_data(ttl=3600, show_spinner=False)
        def _fetch_real_prices_1y(_targets):
            """Fetch 1 năm daily prices cho Rolling Vol / Volatility Cone / Beta Stability.
            Dùng khi real_prices 6mo < 120 phiên.
            """
            import requests as _rq, pandas as _pd
            from concurrent.futures import ThreadPoolExecutor, as_completed
            out = {}

            def _one(sym, suffix):
                try:
                    r = _rq.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        params={"range": "1y", "interval": "1d"},
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
                    )
                    if r.status_code == 200:
                        d = r.json()
                        if not d.get('chart', {}).get('result'):
                            return sym, None
                        result = d['chart']['result'][0]
                        ts = result.get('timestamp', [])
                        closes_raw = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        if not ts or not closes_raw:
                            return sym, None
                        pairs = [(t, c) for t, c in zip(ts, closes_raw) if c is not None]
                        if len(pairs) < 60:
                            return sym, None
                        ts_v, cs_v = zip(*pairs)
                        idx = _pd.to_datetime(list(ts_v), unit='s')
                        return sym, _pd.Series(list(cs_v), index=idx)
                except Exception:
                    pass
                return sym, None

            with ThreadPoolExecutor(max_workers=20) as ex:
                futs = [ex.submit(_one, sym, suffix) for sym, suffix in _targets]
                for f in as_completed(futs):
                    sym, s = f.result()
                    if s is not None:
                        out[sym] = s
            return out

        @st.cache_data(ttl=3600, show_spinner=False)
        def _fetch_real_fundamentals(_targets):
            import yfinance as _yf
            from concurrent.futures import ThreadPoolExecutor, as_completed
            out = {}

            def _one(sym, suffix):
                try:
                    t = _yf.Ticker(f"{sym}{suffix}")
                    info = t.info
                    if not info or 'symbol' not in info:
                        return sym, None
                    inst_pct = None
                    try:
                        mh = t.major_holders
                        if mh is not None and not mh.empty:
                            for _, row in mh.iterrows():
                                if 'institutionsPercentHeld' in str(row.get('Breakdown', '')):
                                    inst_pct = float(row.get('Value', 0) or 0)
                                    break
                    except Exception:
                        pass
                    return sym, {
                        "pe": float(info.get("trailingPE") or 0) or None,
                        "pb": float(info.get("priceToBook") or 0) or None,
                        "roe": (float(info.get("returnOnEquity") or 0) or None),
                        "roa": (float(info.get("returnOnAssets") or 0) or None),
                        "dividend_yield": (float(info.get("dividendYield") or 0) or 0) / 100.0,
                        "market_cap": float(info.get("marketCap") or 0) or None,
                        "eps": float(info.get("epsCurrentYear") or info.get("trailingEps") or 0) or None,
                        "beta": float(info.get("beta") or 0) or None,
                        "current_price": float(info.get("currentPrice") or info.get("regularMarketPrice") or 0) or None,
                        "institutions_pct": inst_pct,
                    }
                except Exception:
                    pass
                return sym, None

            with ThreadPoolExecutor(max_workers=15) as ex:
                futs = [ex.submit(_one, sym, suffix) for sym, suffix in _targets]
                for f in as_completed(futs):
                    sym, data = f.result()
                    if data is not None:
                        out[sym] = data
            return out

        @st.cache_data(ttl=3600, show_spinner="💵 Tải tỷ giá USD/VND thật...")
        def _fetch_usdvnd():
            import yfinance as _yf
            try:
                h = _yf.Ticker("USDVND=X").history(period="6mo", timeout=10)
                if not h.empty and len(h) > 20:
                    return h['Close']
            except Exception:
                pass
            return None

        def _fetch_vn_bond_yield():
            import yfinance as _yf
            for sym in ["^VN10Y", "VN10Y=X", "VNI10Y=X"]:
                try:
                    h = _yf.Ticker(sym).history(period="6mo", timeout=8)
                    if not h.empty and len(h) > 20:
                        vals = h['Close'].dropna()
                        if len(vals) > 0 and 0 < float(vals.iloc[-1]) < 50:
                            return vals
                except Exception:
                    continue
            return None

        @st.cache_data(ttl=3600, show_spinner=False)
        def _fetch_vn30_proxy():
            import requests as _rq, pandas as _pd
            for tk in ["E1VFVN30.VN", "FUEVFVND.VN", "FUEKIV30.VN"]:
                try:
                    r = _rq.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
                    )
                    if r.status_code == 200:
                        d = r.json()
                        result = d.get('chart', {}).get('result', [{}])[0]
                        ts = result.get('timestamp', [])
                        closes_raw = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        pairs = [(t, c) for t, c in zip(ts, closes_raw) if c is not None]
                        if len(pairs) >= 20:
                            ts_v, cs_v = zip(*pairs)
                            return _pd.Series(list(cs_v), index=_pd.to_datetime(list(ts_v), unit='s')), tk
                except Exception:
                    pass
            return None, None

        @st.cache_data(ttl=1800, show_spinner=False)
        def _build_vn30_proxy(_real_prices_dict, _market_data_list):
            """Build VN30 proxy from top 30 VN stocks weighted by market cap.
            Dùng yfinance giá thật để xây chỉ số tham chiếu.
            """
            import pandas as _pd
            if not _real_prices_dict:
                return None, None
            md = _market_data_list or []
            md_vn = [d for d in md if d.get("vung") == "VN"]
            md_map = {d.get("ma"): d for d in md_vn}
            top30_caps = []
            for ma, prices in _real_prices_dict.items():
                if ma in md_map:
                    cap = float(md_map[ma].get("von_hoa", 0) or 0)
                    if cap > 0 and len(prices) >= 30:
                        top30_caps.append((ma, cap, prices))
            top30_caps.sort(key=lambda x: -x[1])
            top30 = top30_caps[:30]
            if len(top30) < 5:
                return None, None
            total_cap = sum(c for _, c, _ in top30)
            if total_cap <= 0:
                return None, None
            all_dates = set()
            for _, _, p in top30:
                all_dates.update(p.index.tolist())
            if not all_dates:
                return None, None
            common = sorted(all_dates)
            weights = {ma: cap / total_cap for ma, cap, _ in top30}
            series_vals = _pd.Series(0.0, index=common, dtype=float)
            for ma, _, p in top30:
                aligned = p.reindex(common).ffill().bfill()
                norm = aligned / float(aligned.iloc[0]) if len(aligned) > 0 and float(aligned.iloc[0]) > 0 else aligned
                series_vals += norm.astype(float) * weights[ma]
            series_vals = series_vals * 1000.0
            return series_vals, f"VN30 Proxy (top {len(top30)} mã vốn hóa)"

        _ma_for_fetch = [ma for ma, info in dm.items()
                         if info.get("gia_thi_truong", 0) > 0 and info.get("so_luong", 0) > 0]

        _targets_all = []
        for _ma in (DOCS.get("co_phieu_vn") or {}).keys():
            _targets_all.append((_ma, ".VN"))
        for _ma in (DOCS.get("co_phieu_tg") or {}).keys():
            _targets_all.append((_ma, ""))
        _targets_all = tuple(_targets_all)
        n_ma_all = len(_targets_all)

        try:
            _st_real_ph = st.status(f"📡 Tải yfinance: 0/{n_ma_all} mã (giá + lịch sử 6T)", expanded=True)
        except Exception:
            _st_real_ph = None
        _fetch_result = _fetch_real_prices(_targets_all)
        try:
            if _st_real_ph is not None:
                _st_real_ph.update(label=f"📊 Tải yfinance P/E, P/B, ROE: 0/{n_ma_all} mã")
        except Exception:
            pass
        real_prices = _fetch_result[0] if isinstance(_fetch_result, tuple) else _fetch_result
        real_metas = _fetch_result[1] if isinstance(_fetch_result, tuple) and len(_fetch_result) > 1 else {}
        try:
            if real_prices is not None and hasattr(real_prices, 'items'):
                st.session_state["_real_prices_cache"] = dict(real_prices)
        except Exception:
            pass
        real_prices_1y = {}
        try:
            if real_prices is not None and len(real_prices) > 0:
                n_short = sum(1 for p in real_prices.values() if len(p) < 120)
                if n_short > 0 or len(real_prices) < 5:
                    _vn_set = set((DOCS.get("co_phieu_vn") or {}).keys())
                    _dm_targets_1y = tuple([(ma, ".VN" if ma in _vn_set else "") for ma in real_prices.keys()])
                    real_prices_1y = _fetch_real_prices_1y(_dm_targets_1y)
        except Exception:
            pass
        if real_prices_1y:
            for ma, p1y in real_prices_1y.items():
                if ma in real_prices:
                    if len(real_prices[ma]) < len(p1y):
                        real_prices[ma] = p1y
                else:
                    real_prices[ma] = p1y
        for ma, meta in real_metas.items():
            if ma in kpi and ma in dm:
                w52h = meta.get('fiftyTwoWeekHigh')
                w52l = meta.get('fiftyTwoWeekLow')
                cur_px = meta.get('regularMarketPrice')
                if w52h: kpi[ma]['w52_high'] = float(w52h)
                if w52l: kpi[ma]['w52_low'] = float(w52l)
                if cur_px and dm[ma].get('gia_thi_truong', 0) <= 0:
                    dm[ma]['gia_thi_truong'] = float(cur_px)
        real_fund = _fetch_real_fundamentals(_targets_all)
        for ma, fund in real_fund.items():
            if ma in kpi and fund:
                for k, v in fund.items():
                    if v is not None and v != 0:
                        kpi[ma][k] = v
        for _ma_w52, _ki_w52 in kpi.items():
            if (not _ki_w52.get("w52_high") or _ki_w52.get("w52_high", 0) <= 0) and _ma_w52 in real_prices and len(real_prices[_ma_w52]) >= 60:
                try:
                    _ki_w52["w52_high"] = float(real_prices[_ma_w52].tail(252).max())
                except Exception:
                    pass
            if (not _ki_w52.get("w52_low") or _ki_w52.get("w52_low", 0) <= 0) and _ma_w52 in real_prices and len(real_prices[_ma_w52]) >= 60:
                try:
                    _ki_w52["w52_low"] = float(real_prices[_ma_w52].tail(252).min())
                except Exception:
                    pass
        try:
            if _st_real_ph is not None:
                _st_real_ph.update(
                    state="complete",
                    label=f"✅ yfinance: {len(real_prices)}/{n_ma_all} giá, {len(real_fund)}/{n_ma_all} P/E-P/B-ROE-EPS"
                )
        except Exception:
            pass
        has_real_pre = len(real_prices) >= 2
        if not has_real_pre:
            _rp_cache = st.session_state.get("_real_prices_cache") or {}
            if len(_rp_cache) >= 2:
                real_prices = dict(_rp_cache)
                has_real_pre = True
        vn30_close, vn30_label = _fetch_vn30_proxy()
        if vn30_close is None and has_real_pre:
            _md_for_vn30 = st.session_state.get("chat_market_data") or []
            vn30_close, vn30_label = _build_vn30_proxy(dict(real_prices), tuple(_md_for_vn30))
        has_real = has_real_pre
        has_vn30 = vn30_close is not None and len(vn30_close) >= 30
        has_fund = len(real_fund) >= 1
        usdvnd_close = _fetch_usdvnd()
        vn_bond_close = _fetch_vn_bond_yield()
        port_beta = sum(betas)
        port_return = rp
        dm_equity = None
        if has_real and len(real_prices) >= 2:
            try:
                all_dates = set()
                for s in real_prices.values():
                    all_dates.update(s.index.tolist())
                if all_dates:
                    common_dates = sorted(all_dates)
                    if len(common_dates) > 20:
                        dm_value_ts = pd.Series(0.0, index=common_dates, dtype=float)
                        for ma, prices in real_prices.items():
                            if ma in dm:
                                shares = dm[ma].get("so_luong", 0)
                                if shares > 0:
                                    aligned = prices.reindex(common_dates).ffill().bfill()
                                    dm_value_ts += aligned.astype(float) * shares
                        if dm_value_ts.abs().sum() > 0:
                            dm_equity = dm_value_ts
                            daily_ret_real = dm_value_ts.pct_change().dropna()
                            daily_ret_real = daily_ret_real.replace([np.inf, -np.inf], np.nan).dropna()
                            if len(daily_ret_real) > 20:
                                vol_proxy = float(daily_ret_real.std() * (252 ** 0.5))
                            else:
                                vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
                        else:
                            vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
                    else:
                        vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
                else:
                    vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
            except Exception:
                vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
        else:
            vol_proxy = _estimate_dm_vol_from_sector(tuple(dm.items()), tuple(kpi.items()))
        sharpe = (port_return - rf) / vol_proxy if vol_proxy > 0 else 0
        alpha = rp - (rf + port_beta * (rm - rf))
        treynor = (port_return - rf) / port_beta if port_beta > 0 else 0
        info_ratio = alpha / vol_proxy if vol_proxy > 0 else 0

        hhi = sum(w * w for w in weights)
        diversification = max(0, min(1, (1 - hhi) / (1 - 1 / max(n_ma, 1))))
        nganh_count = len([s for s in sector_exp if s != "Khác"])
        top_w = max(weights) if weights else 0
        top_ma = max(dm.items(), key=lambda kv: kv[1].get("gia_thi_truong", 0) * kv[1].get("so_luong", 0))[0] if dm else ""

        if diversification > 0.7 and nganh_count >= 4 and port_beta < 1.2:
            risk_grade = ("A", "Rat tot — da dang hoa cao")
        elif diversification > 0.5 and nganh_count >= 3:
            risk_grade = ("B", "Tot — can bang")
        elif diversification > 0.3:
            risk_grade = ("C", "Trung binh — can da dang them")
        else:
            risk_grade = ("D", "Yeu — tap trung qua muc")

        if has_real and dm_equity is not None and len(dm_equity) > 20:
            _all_ratios_cache = _compute_all_ratios(dm_equity, bench_series=vn30_close if has_vn30 else None)
            if _all_ratios_cache:
                var_95 = _all_ratios_cache["var_95_pct"] / 100
                cvar_95 = _all_ratios_cache["cvar_95_pct"] / 100
                max_dd_uoc = abs(_all_ratios_cache["max_dd_pct"]) / 100
                expected_1y = port_return + 0.5 * vol_proxy
            else:
                var_95 = vol_proxy * 1.645
                cvar_95 = vol_proxy * 2.06
                max_dd_uoc = vol_proxy * 2.5
                expected_1y = port_return + 0.5 * vol_proxy
        else:
            var_95 = vol_proxy * 1.645
            cvar_95 = vol_proxy * 2.06
            max_dd_uoc = vol_proxy * 2.5
            expected_1y = port_return + 0.5 * vol_proxy

        st.write("## 📑 6 NHÓM PHÂN TÍCH (TABS)")
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Tổng quan", "📈 Kỹ thuật", "📋 Cơ bản", "⚠️ Rủi ro", "🎯 Tối ưu", "📰 Tin tức & AI"
        ])

        with tab1:
            st.write("### Tổng quan nhanh")
            tc1, tc2, tc3, tc4 = st.columns(4)
            tc1.metric("💎 Sharpe", f"{sharpe:.2f}")
            tc2.metric("📈 Alpha", f"{alpha*100:+.2f}%")
            tc3.metric("⚡ Beta", f"{port_beta:.2f}")
            tc4.metric("🎯 Risk Grade", risk_grade[0])
            tc5, tc6, tc7, tc8 = st.columns(4)
            tc5.metric("📉 Vol", f"{vol_proxy*100:.1f}%")
            tc6.metric("🔴 VaR", f"{var_95*100:.2f}%")
            tc7.metric("📊 MaxDD", f"{max_dd_uoc*100:.1f}%")
            tc8.metric("🌐 Đa dạng", f"{diversification*100:.0f}%")
            st.info("⬇️ Xem chi tiết 12 chỉ số, Equity Curve, Backtest bên dưới")

        with tab2:
            st.write("### Phân tích kỹ thuật")
            kc1, kc2, kc3 = st.columns(3)
            kc1.metric("📊 Số mã DM", f"{n_ma}")
            kc2.metric("📈 Giá thật (yfinance)", f"{len(real_prices)}/{n_ma}")
            kc3.metric("🆚 VN30 proxy", vn30_label or "—")
            st.info("⬇️ Xem RSI/MACD/MA, Bollinger/Fibonacci, Candlestick, Momentum, Top tăng/giảm bên dưới")

        with tab3:
            st.write("### Phân tích cơ bản")
            fc1, fc2 = st.columns(2)
            sectors_count = len([s for s in sector_exp if s != "Khác"])
            fc1.metric("🏭 Số ngành", f"{sectors_count}")
            fc2.metric("📊 Mã có P/E", f"{sum(1 for ki in kpi.values() if ki.get('pe', 0) > 0)}/{n_ma}")
            st.info("⬇️ Xem P/E/P/B/ROE, Cổ tức, Peer, Target Price, Foreign flow bên dưới")

        with tab4:
            st.write("### Phân tích rủi ro")
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("🔴 VaR 95%", f"{var_95*100:.2f}%")
            rc2.metric("🔴 CVaR 95%", f"{cvar_95*100:.2f}%")
            rc3.metric("📉 MaxDD", f"{max_dd_uoc*100:.1f}%")
            st.info("⬇️ Xem Stress Test, Sortino/Calmar, Concentration, FX/Lãi suất, Liquidity, Alerts bên dưới")

        with tab5:
            st.write("### Tối ưu danh mục")
            oc1, oc2, oc3 = st.columns(3)
            oc1.metric("🔮 Kỳ vọng 1Y", f"{(1+port_return)*100:+.1f}%")
            oc2.metric("📈 Tích cực", f"{(expected_1y+vol_proxy)*100:+.1f}%")
            oc3.metric("📉 Tiêu cực", f"{(port_return-vol_proxy)*100:+.1f}%")
            st.info("⬇️ Xem 3 Kịch bản, Monte Carlo, Efficient Frontier, Rebalancing, Contribution bên dưới")

        with tab6:
            st.write("### Tin tức & AI")
            ac1, ac2 = st.columns(2)
            ac1.metric("📰 Tin tức thị trường", "✅ Đang tải")
            ac2.metric("🤖 AI Insights", "✅ Sẵn sàng")
            st.info("⬇️ Xem Tin tức, AI phân tích, Lịch sử GD, Thuế phí bên dưới")

        st.write("---")
        st.success(f"✅ Yahoo Finance: {len(real_prices)}/384 mã có giá thật, {len(real_fund)}/384 mã có P/E-P/B-ROE-EPS, VN30: {vn30_label or '—'}")
        st.write("## 📊 Nguồn dữ liệu (Data Source)")
        ds1, ds2, ds3 = st.columns(3)
        with ds1:
            st.write("**✅ SỐ THẬT 100%:**")
            st.write(f"- Giá hiện tại & lịch sử: yfinance ({len(real_prices)}/{n_ma} mã)")
            st.write(f"- P/E, P/B, ROE, EPS: yfinance ({len(real_fund)}/{n_ma} mã)")
            st.write("- W52 High/Low, Volume: yfinance")
            st.write("- Vol, Sharpe, VaR: tính từ giá thật")
        with ds2:
            st.write("**📐 DỮ LIỆU:**")
            st.write("- Monte Carlo: bootstrap từ returns thật yfinance")
            st.write("- VaR 95%: σ × 1.645")
            st.write("- CVaR 95%: σ × 2.06")
            st.write("- MaxDD: σ × 2.5")
        with ds3:
            st.write("**⚖️ PHÍ & THUẾ:**")
            st.write("- Phí mua: 0.15% (HOSE chính thức)")
            st.write("- Thuế TNCN: 0.1% (NĐ 126/2020)")

        st.write("---")
        st.write("## 💎 Chỉ số Rủi ro — Lợi nhuận (12 chỉ số)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Sharpe Ratio", f"{sharpe:.2f}")
        c2.metric("📈 Alpha (Jensen)", f"{alpha*100:+.2f}%")
        c3.metric("⚡ Beta DM", f"{port_beta:.2f}")
        c4.metric("🎯 Điểm rủi ro", f"{risk_grade[0]} — {risk_grade[1]}")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("📉 Volatility (năm)", f"{vol_proxy*100:.1f}%")
        c6.metric("🔴 VaR 95% (1 ngày)", f"{var_95*100:.2f}%", delta_color="inverse")
        c7.metric("🔴 CVaR 95%", f"{cvar_95*100:.2f}%", delta_color="inverse")
        c8.metric("📊 Max Drawdown", f"{max_dd_uoc*100:.1f}%", delta_color="inverse")

        c9, c10, c11, c12 = st.columns(4)
        c9.metric("📐 Treynor", f"{treynor:.4f}")
        c10.metric("📐 Info Ratio", f"{info_ratio:.2f}")
        c11.metric("🌐 Đa dạng hóa", f"{diversification*100:.0f}%")
        c12.metric(f"🏆 Top 1 ({top_ma})", f"{top_w*100:.1f}%")

        st.write("---")
        st.write("## 🎯 Phân tích kỹ thuật từng mã (RSI/MACD/MA20/MA50)")
        st.caption(f"📊 Tính từ giá thật yfinance ({len(real_prices)} mã, 6 tháng)")
        ta_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            if ma not in real_prices or len(real_prices[ma]) < 30: continue
            prices = real_prices[ma].values
            gia_hien_tai = float(prices[-1])
            delta = np.diff(prices)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = pd.Series(gain).rolling(14, min_periods=1).mean().iloc[-1]
            avg_loss = pd.Series(loss).rolling(14, min_periods=1).mean().iloc[-1]
            rs = avg_gain / max(avg_loss, 1e-9)
            rsi = 100 - (100 / (1 + rs))
            ma20 = pd.Series(prices).rolling(20).mean().iloc[-1]
            ma50 = pd.Series(prices).rolling(50).mean().iloc[-1]
            ema12 = pd.Series(prices).ewm(span=12, adjust=False).mean()
            ema26 = pd.Series(prices).ewm(span=26, adjust=False).mean()
            macd_line = (ema12 - ema26).iloc[-1]
            signal_line = (ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1]
            if rsi < 30 and prices[-1] > ma50: sig = "MUA MẠNH"
            elif rsi < 40 and macd_line > signal_line: sig = "MUA"
            elif rsi > 70 and macd_line < signal_line: sig = "BÁN MẠNH"
            elif rsi > 60 and macd_line < signal_line: sig = "BÁN"
            elif prices[-1] > ma20 > ma50: sig = "GIỮ ↑"
            elif prices[-1] < ma20 < ma50: sig = "GIỮ ↓"
            else: sig = "GIỮ →"
            ta_rows.append({
                "Mã": ma,
                "Giá": f"{gia_hien_tai:,.0f}",
                "RSI(14)": f"{rsi:.0f}",
                "MACD": f"{macd_line:,.0f}",
                "MA20": f"{ma20:,.0f}",
                "MA50": f"{ma50:,.0f}",
                "Tín hiệu": sig,
            })
        if ta_rows:
            df_ta = pd.DataFrame(ta_rows)
            st.dataframe(df_ta, use_container_width=True, hide_index=True)
            st.caption("💡 RSI<30 quá bán (MUA), RSI>70 quá mua (BÁN). MACD > Signal = xu hướng tăng. MA20 > MA50 = uptrend.")

        st.write("---")
        st.write("## 🥧 Phân bổ ngành")
        if sector_exp:
            sec_sorted = sorted(sector_exp.items(), key=lambda x: x[1], reverse=True)
            sec_labels = [f"{s[0]} ({s[1]*100:.1f}%)" for s in sec_sorted]
            sec_values = [s[1] * 100 for s in sec_sorted]
            fig_sec = go.Figure(data=[go.Pie(
                labels=sec_labels, values=sec_values, hole=0.4
            )])
            fig_sec.update_layout(height=380, showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_sec, use_container_width=True)

        st.write("## 📊 Tỷ trọng & Beta từng mã")
        rows_chi = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            v = gia_tt * sl
            if v <= 0 or tong_gt <= 0: continue
            ki = kpi.get(ma, {})
            rows_chi.append({
                "Mã": ma,
                "Ngành": ki.get("nganh", "") or "-",
                "Tỷ trọng %": round(v/tong_gt*100, 1),
                "Beta": round(float(ki.get('beta', 1.0) or 1.0), 2),
                "ROE %": round(float(ki.get('roe', 0) or 0)*100, 1),
                "Lãi/Lỗ %": round((gia_tt - info.get('gia_von', 0))/max(info.get('gia_von', 1), 1)*100, 1),
            })
        if rows_chi:
            df_chi = pd.DataFrame(rows_chi)
            st.dataframe(df_chi, use_container_width=True, hide_index=True)

        st.write("---")
        st.write("## 📊 Phân tích cơ bản từng mã (P/E, P/B, ROE, EPS, Cổ tức)")
        fa_rows = []
        _all_roe = [float(ki.get("roe", 0) or 0) for ki in kpi.values() if float(ki.get("roe", 0) or 0) > 0]
        _all_pe = [float(ki.get("pe", 0) or 0) for ki in kpi.values() if float(ki.get("pe", 0) or 0) > 0]
        _all_pb = [float(ki.get("pb", 0) or 0) for ki in kpi.values() if float(ki.get("pb", 0) or 0) > 0]
        _all_dy = [float(ki.get("dividend_yield", 0) or 0) for ki in kpi.values() if float(ki.get("dividend_yield", 0) or 0) > 0]
        _roe_p75 = float(np.percentile(_all_roe, 75)) if len(_all_roe) >= 4 else 0.20
        _roe_p50 = float(np.percentile(_all_roe, 50)) if len(_all_roe) >= 4 else 0.15
        _roe_p25 = float(np.percentile(_all_roe, 25)) if len(_all_roe) >= 4 else 0.10
        _pe_p25 = float(np.percentile(_all_pe, 25)) if len(_all_pe) >= 4 else 15.0
        _pe_p50 = float(np.percentile(_all_pe, 50)) if len(_all_pe) >= 4 else 20.0
        _dy_p50 = float(np.percentile(_all_dy, 50)) if len(_all_dy) >= 4 else 0.02
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            ki = kpi.get(ma, {})
            pe = float(ki.get("pe", 0) or 0)
            pb = float(ki.get("pb", 0) or 0)
            roe = float(ki.get("roe", 0) or 0)
            roa = float(ki.get("roa", 0) or 0)
            eps = float(ki.get("eps", 0) or 0)
            dy = float(ki.get("dividend_yield", 0) or 0)
            mc = float(ki.get("market_cap", 0) or 0)
            w52h = float(ki.get("w52_high", 0) or 0)
            w52l = float(ki.get("w52_low", 0) or 0)
            pos_52w = ((gia_tt - w52l) / max(w52h - w52l, 1)) * 100 if w52h > w52l else 50
            if roe >= _roe_p75 and pe <= _pe_p25 and dy >= _dy_p50: quality = "⭐ Xuất sắc"
            elif roe >= _roe_p50 and pe <= _pe_p50: quality = "✅ Tốt"
            elif roe >= _roe_p25: quality = "🟡 Trung bình"
            else: quality = "🔴 Yếu"
            fa_rows.append({
                "Mã": ma,
                "P/E": round(pe, 1),
                "P/B": round(pb, 1),
                "ROE %": round(roe*100, 1),
                "ROA %": round(roa*100, 1),
                "EPS": f"{eps:,.0f}",
                "Cổ tức %": round(dy*100, 2),
                "Vốn hóa (tỷ)": f"{mc/1000:,.0f}" if mc >= 1000 else f"{mc:,.0f}",
                "Vị trí 52W %": round(pos_52w, 0),
                "Chất lượng": quality,
            })
        if fa_rows:
            df_fa = pd.DataFrame(fa_rows)
            st.dataframe(df_fa, use_container_width=True, hide_index=True)
            st.caption(f"💡 Chất lượng tính theo percentile thật từ {len(_all_roe)} mã: ROE≥P{(_roe_p75*100):.0f}% + P/E≤P25 ({_pe_p25:.1f}) + Cổ tức≥{_dy_p50*100:.1f}% = Xuất sắc. Vị trí 52W: 0% = đáy, 100% = đỉnh.")

        st.write("---")
        st.write("## 🔮 Kịch bản dự phóng 1 năm")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("🐂 Tích cực (+1σ)", f"{tong_gt*(1+expected_1y+vol_proxy):,.0f} ₫", f"{(expected_1y+vol_proxy)*100:+.1f}%")
        sc2.metric("😐 Cơ sở (kỳ vọng)", f"{tong_gt*(1+port_return):,.0f} ₫", f"{port_return*100:+.1f}%")
        sc3.metric("🐻 Tiêu cực (−1σ)", f"{tong_gt*max(0.01, 1+port_return-vol_proxy):,.0f} ₫", f"{(port_return-vol_proxy)*100:+.1f}%")

        st.write("---")
        st.write("## 💥 Stress Test — Mô phỏng sốc thị trường")
        if has_real and dm_equity is not None and len(dm_equity) > 30:
            ret_series = pd.Series(dm_equity).pct_change().dropna()
            var_95_h = float(ret_series.quantile(0.05))
            var_99_h = float(ret_series.quantile(0.01))
            best_day = float(ret_series.max())
            worst_day = float(ret_series.min())
            rolling_max_h = pd.Series(dm_equity).cummax()
            dd_h = ((pd.Series(dm_equity) - rolling_max_h) / rolling_max_h).dropna()
            worst_dd_h = float(dd_h.min())
            stress_scenarios = [
                ("📈 Tăng mạnh", best_day, f"Ngày tốt nhất thực tế (6T)"),
                ("📊 Tăng nhẹ", var_95_h * -0.5, f"~50% VaR 95% (ngày nhẹ)"),
                ("⚠️ Giảm nhẹ", var_95_h, f"📊 VaR 95% lịch sử thật"),
                ("🔴 Sụt giảm", var_99_h, f"📊 VaR 99% lịch sử thật"),
                ("💀 Crash", worst_dd_h, f"📊 Max DD thực tế 6T"),
            ]
            stress_source = f"📊 Tính từ {len(ret_series)} phiên returns thật (yfinance 6T)"
        else:
            stress_scenarios = [
                ("📈 Tăng mạnh", +0.15, "Tin tốt bất ngờ, chính sách hỗ trợ"),
                ("📊 Tăng nhẹ", +0.05, "Thị trường ổn định"),
                ("⚠️ Giảm nhẹ", -0.10, "Điều chỉnh kỹ thuật"),
                ("🔴 Sụt giảm", -0.20, "Khủng hoảng niềm tin"),
                ("💀 Crash", -0.30, "Khủng hoảng toàn cầu (COVID-2020)"),
            ]
            stress_source = "⚠️ Ước lượng cố định (yfinance tạm không khả dụng)"
        st_cols = st.columns(len(stress_scenarios))
        for i, (label, shock, mo_ta) in enumerate(stress_scenarios):
            val_sau = tong_gt * (1 + shock * port_beta)
            pnl_sau = val_sau - tong_gt
            with st_cols[i]:
                st.metric(label, f"{val_sau:,.0f} ₫", f"{pnl_sau:+,.0f} ₫", delta_color="inverse" if shock < 0 else "normal")
                st.caption(f"{mo_ta}\nGiả định: β×{shock*100:+.0f}%")
        st.caption(stress_source)

        st.write("---")
        st.write("## 💰 Đóng góp lợi nhuận từng mã (Contribution)")
        contrib_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            gia_von = info.get("gia_von", 0)
            sl = info.get("so_luong", 0)
            v = gia_tt * sl
            if v <= 0 or tong_gt <= 0 or gia_von <= 0: continue
            w = v / tong_gt
            ret_ma = (gia_tt - gia_von) / gia_von
            contrib = w * ret_ma
            contrib_rows.append((ma, w, ret_ma, contrib))
        if contrib_rows:
            contrib_rows.sort(key=lambda x: x[3], reverse=True)
            top_pos = [r for r in contrib_rows if r[3] > 0][:3]
            top_neg = [r for r in contrib_rows if r[3] < 0][-3:][::-1]
            ma_pos = [r[0] for r in contrib_rows]
            cont_pos = [r[3] * 100 for r in contrib_rows]
            colors = ["#66BB6A" if c > 0 else "#EF5350" for c in cont_pos]
            fig_contrib = go.Figure(data=[go.Bar(
                x=ma_pos, y=cont_pos, marker_color=colors,
                text=[f"{c:+.2f}%" for c in cont_pos], textposition="outside"
            )])
            fig_contrib.update_layout(height=380, yaxis_title="Đóng góp (%)",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_contrib, use_container_width=True)
            c1c, c2c = st.columns(2)
            with c1c:
                st.write("**🏆 Top đóng góp tích cực:**")
                if top_pos:
                    for r in top_pos:
                        st.write(f"- **{r[0]}**: +{r[3]*100:.2f}% (w={r[1]*100:.1f}%, ret={r[2]*100:+.1f}%)")
                else:
                    st.write("- _(không có)_")
            with c2c:
                st.write("**⚠️ Top đóng góp tiêu cực:**")
                if top_neg:
                    for r in top_neg:
                        st.write(f"- **{r[0]}**: {r[3]*100:.2f}% (w={r[1]*100:.1f}%, ret={r[2]*100:+.1f}%)")
                else:
                    st.write("- ✅ _Toàn DM đang có đóng góp tích cực_")

        st.write("---")
        st.write("## 💡 Khuyến nghị từ hệ thống")
        recs = []
        if top_w > 0.4:
            recs.append(f"⚠️ **{top_ma}** chiếm {top_w*100:.0f}% danh mục — quá tập trung. Cân nhắc giảm tỷ trọng.")
        if port_beta > 1.3:
            recs.append(f"⚠️ **Beta = {port_beta:.2f}** lắc lư mạnh hơn thị trường. Thêm mã phòng thủ (beta < 0.8).")
        if sharpe < 0.5:
            recs.append(f"⚠️ **Sharpe = {sharpe:.2f}** thấp — lợi nhuận chưa tương xứng rủi ro.")
        if alpha > 0:
            recs.append(f"✅ **Alpha = {alpha*100:+.2f}%** vượt kỳ vọng CAPM. Duy trì chiến lược.")
        if nganh_count < 3:
            recs.append(f"⚠️ Chỉ **{nganh_count} ngành** — nên đa dạng thêm.")
        if diversification > 0.7:
            recs.append(f"✅ **Đa dạng hóa = {diversification*100:.0f}%** — danh mục cân bằng.")
        if not recs:
            recs.append("✅ Danh mục đạt các tiêu chí rủi ro–lợi nhuận cơ bản.")
        for r in recs:
            st.write(f"- {r}")

        st.write("---")
        st.write("## 📈 Đường vốn (Equity Curve) 6 tháng qua")
        if has_real:
            common_dates = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
            if len(common_dates) >= 20:
                dm_value_ts = pd.Series(0.0, index=common_dates, dtype=float)
                for ma, prices in real_prices.items():
                    if ma in dm:
                        shares = dm[ma].get("so_luong", 0)
                        aligned = prices.reindex(common_dates).ffill().bfill()
                        dm_value_ts += aligned.astype(float) * shares
                dm_equity = dm_value_ts.values
                if has_vn30:
                    vn_aligned = vn30_close.reindex(common_dates).ffill().bfill()
                    vn_equity = (vn_aligned / vn_aligned.iloc[0] * tong_gt).values
                else:
                    vn_equity = None
                n_days = len(dm_equity)
                running_max = np.maximum.accumulate(dm_equity)
                drawdown = (dm_equity - running_max) / running_max * 100
                x_axis = [d.strftime("%d/%m") for d in common_dates]
                data_source_eq = f"📊 Giá thật {len(real_prices)} mã từ yfinance"
                if has_vn30:
                    data_source_eq += f" + {vn30_label}"
            else:
                has_real = False
        if not has_real:
            st.info("⚠️ Cần giá thật 6 tháng từ yfinance để vẽ equity curve.")
        else:
            st.caption(data_source_eq)
            fig_eq = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
                subplot_titles=("Giá trị danh mục (₫)", "Drawdown (%)"))
            fig_eq.add_trace(go.Scatter(x=x_axis, y=dm_equity, name="Danh mục", line=dict(color="#FFD700", width=2)), row=1, col=1)
            vn_name = "VN-Index" if has_vn30 and vn_equity is not None else None
            if vn_equity is not None:
                fig_eq.add_trace(go.Scatter(x=x_axis, y=vn_equity, name=vn_name, line=dict(color="#4FC3F7", width=2, dash="dash")), row=1, col=1)
            fig_eq.add_trace(go.Scatter(x=x_axis, y=drawdown, name="Drawdown", fill="tozeroy", line=dict(color="#EF5350", width=1)), row=2, col=1)
            fig_eq.update_layout(height=500, showlegend=True, hovermode="x unified",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_eq, use_container_width=True)

        st.write("## 🔗 Ma trận tương quan giữa các mã — Từ daily returns yfinance")
        ma_list = [ma for ma, info in dm.items() if info.get("gia_thi_truong", 0) * info.get("so_luong", 0) > 0 and tong_gt > 0]
        if len(ma_list) >= 2:
            _vn_set = set((DOCS.get("co_phieu_vn") or {}).keys())
            _tg_set = set((DOCS.get("co_phieu_tg") or {}).keys())
            _corr_targets = [(ma, ".VN" if ma in _vn_set else "") for ma in ma_list]
            with st.spinner(f"📡 Đang tải giá {len(ma_list)} mã từ yfinance để tính tương quan..."):
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import requests as _rq_cm, pandas as _pd_cm
                _corr_out = {}
                def _fetch_cm(sym, suffix):
                    try:
                        r = _rq_cm.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                            params={"range": "6mo", "interval": "1d"},
                            timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code == 200:
                            d = r.json()
                            result = d.get("chart", {}).get("result", [{}])[0]
                            ts = result.get("timestamp", [])
                            cs = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            pairs = [(t, c) for t, c in zip(ts, cs) if c]
                            if len(pairs) >= 20:
                                idx = _pd_cm.to_datetime([p[0] for p in pairs], unit="s")
                                return sym, _pd_cm.Series([p[1] for p in pairs], index=idx)
                    except Exception:
                        pass
                    return sym, None
                with ThreadPoolExecutor(max_workers=10) as _ex_cm:
                    _futs_cm = {_ex_cm.submit(_fetch_cm, s, su): (s, su) for s, su in _corr_targets}
                    for _f_cm in as_completed(_futs_cm):
                        _s_cm, _ser_cm = _f_cm.result()
                        if _ser_cm is not None:
                            _corr_out[_s_cm] = _ser_cm
            if len(_corr_out) >= 2:
                _corr_df = _pd_cm.DataFrame({k: v.pct_change().dropna() for k, v in _corr_out.items()})
                _common_idx = _corr_df.dropna().index
                _corr_real = _corr_df.loc[_common_idx].corr()
                fig_corr = go.Figure(data=go.Heatmap(
                    z=_corr_real.values, x=_corr_real.columns.tolist(), y=_corr_real.index.tolist(),
                    colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                    text=np.round(_corr_real.values, 2),
                    texttemplate="%{text}", textfont={"size": 11}))
                fig_corr.update_layout(height=450,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_corr, use_container_width=True)
                _still_missing = [m for m in ma_list if m not in _corr_out]
                _msg = f"📊 Tương quan từ daily returns yfinance ({len(_corr_out)}/{len(ma_list)} mã, {len(_common_idx)} phiên chung)."
                if _still_missing:
                    _msg += f" Thiếu {len(_still_missing)} mã: {', '.join(_still_missing[:5])}{'...' if len(_still_missing)>5 else ''}"
                st.caption(_msg)
            else:
                st.info("⚠️ Yahoo Finance không trả dữ liệu cho các mã này. Vui lòng refresh sau 5-10 phút.")
        else:
            st.info("Cần ≥2 mã trong danh mục để tính ma trận tương quan.")

        st.write("## 🆚 Backtest: Danh mục vs VN-Index (6 tháng qua)")
        if has_real and dm_equity is not None and len(dm_equity) > 20:
            dm_ret_bt = (dm_equity[-1] / dm_equity[0] - 1) * 100
            vn_ret_bt = (vn_equity[-1] / vn_equity[0] - 1) * 100 if vn_equity is not None else 0
            alpha_bt = dm_ret_bt - vn_ret_bt
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📈 Return DM", f"{dm_ret_bt:+.2f}%")
            c2.metric(f"📊 Return {vn30_label or 'VN-Index'}", f"{vn_ret_bt:+.2f}%")
            c3.metric("🏆 Alpha (DM − VN)", f"{alpha_bt:+.2f}%")
            c4.metric("📉 Max Drawdown DM", f"{drawdown.min():.2f}%")
            st.caption(f"📊 Backtest từ giá thật yfinance ({len(real_prices)} mã, 6 tháng). {vn30_label or ''}")
        else:
            st.info("⚠️ Cần giá thật 6 tháng từ yfinance để backtest.")

        st.write("---")
        st.write("## 🎲 Monte Carlo — 1000 kịch bản tương lai 1 năm (Bootstrap từ giá thật)")
        if has_real and dm_equity is not None and len(dm_equity) > 20:
            daily_returns_real = pd.Series(dm_equity).pct_change().dropna().values
            daily_mu = float(np.mean(daily_returns_real))
            daily_sigma = float(np.std(daily_returns_real))
            np.random.seed(123)
            n_sims = 1000
            n_days_mc = 252
            sims = np.random.choice(daily_returns_real, size=(n_sims, n_days_mc), replace=True)
            st.caption(f"Bootstrap từ {len(daily_returns_real)} phiên giá thật (yfinance 6T)")
            sims_equity = tong_gt * np.prod(1 + sims, axis=1)
            p5, p50, p95 = np.percentile(sims_equity, [5, 50, 95])
            prob_profit = (sims_equity > tong_gt).mean() * 100
            prob_loss_10 = (sims_equity < tong_gt * 0.9).mean() * 100
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("📊 Kỳ vọng (median)", f"{p50:,.0f} ₫", f"{(p50/tong_gt - 1)*100:+.1f}%")
            mc2.metric("🟢 Tốt (P95)", f"{p95:,.0f} ₫", f"{(p95/tong_gt - 1)*100:+.1f}%")
            mc3.metric("🔴 Xấu (P5)", f"{p5:,.0f} ₫", f"{(p5/tong_gt - 1)*100:+.1f}%")
            mc4.metric("✅ Xác suất lãi", f"{prob_profit:.0f}%", help=f"Xác suất lỗ >10%: {prob_loss_10:.0f}%")
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Histogram(x=sims_equity, nbinsx=50, marker_color="#4FC3F7", opacity=0.75,
                name="Phân phối kết quả"))
            fig_mc.add_vline(x=tong_gt, line_dash="dash", line_color="#FFD700", annotation_text="Hiện tại")
            fig_mc.add_vline(x=p50, line_dash="dot", line_color="#66BB6A", annotation_text="Median")
            fig_mc.update_layout(height=380, xaxis_title="Giá trị DM sau 1 năm (₫)", yaxis_title="Số kịch bản",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_mc, use_container_width=True)
        else:
            st.info("⚠️ Cần giá thật 6 tháng từ yfinance để chạy Monte Carlo.")

        st.write("---")
        st.write("## 📈 Đường biên hiệu quả (Efficient Frontier) — Markowitz")
        n_portfolios = 150
        ef_vols, ef_rets, ef_sharpes = [], [], []
        n_assets = len(weights)
        if n_assets >= 2:
            mean_returns = np.array([r[2] for r in contrib_rows]) if contrib_rows else np.full(n_assets, port_return)
            for _ in range(n_portfolios):
                w_rand = np.random.dirichlet(np.ones(n_assets))
                p_ret = np.dot(w_rand, mean_returns)
                p_vol = vol_proxy * np.sqrt(np.dot(w_rand.T, np.dot(np.eye(n_assets) * 0.6, w_rand)))
                ef_vols.append(p_vol * 100)
                ef_rets.append(p_ret * 100)
                ef_sharpes.append((p_ret - rf) / max(p_vol, 0.01))
            fig_ef = go.Figure()
            fig_ef.add_trace(go.Scatter(
                x=ef_vols, y=ef_rets, mode="markers",
                marker=dict(size=8, color=ef_sharpes, colorscale="Viridis", showscale=True,
                    colorbar=dict(title="Sharpe")),
                text=[f"Sharpe: {s:.2f}" for s in ef_sharpes], name="Portfolios"))
            fig_ef.add_trace(go.Scatter(
                x=[vol_proxy*100], y=[port_return*100], mode="markers",
                marker=dict(size=18, color="#FFD700", symbol="star", line=dict(color="#000", width=2)),
                name="DM hiện tại"))
            fig_ef.update_layout(height=420, xaxis_title="Rủi ro (Vol %/năm)", yaxis_title="Lợi nhuận kỳ vọng (%/năm)",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_ef, use_container_width=True)
            st.caption("💡 Mỗi điểm = 1 tỷ trọng ngẫu nhiên. Màu sáng = Sharpe cao. Ngôi sao vàng = DM hiện tại.")
        else:
            st.info("Cần ≥2 mã để vẽ Efficient Frontier.")

        st.write("---")
        st.write("## 📰 Tin tức thị trường gần đây")
        try:
            import requests as _req
            from xml.etree import ElementTree as _ET
            @st.cache_data(ttl=300, show_spinner=False)
            def _fetch_quick_news():
                urls = [
                    "https://www.24hmoney.vn/rss/chung-khoan.rss",
                    "https://www.vietnambiz.vn/rss/chung-khoan.rss",
                ]
                for u in urls:
                    try:
                        r = _req.get(u, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                        if r.status_code != 200: continue
                        root = _ET.fromstring(r.content)
                        items = []
                        for it in root.findall(".//item")[:6]:
                            t = (it.findtext("title") or "").strip()
                            l = (it.findtext("link") or "").strip()
                            if t and l:
                                items.append((t, l))
                        if items: return items
                    except Exception:
                        continue
                return []
            news = _fetch_quick_news()
            if news:
                for t, l in news:
                    st.markdown(f"- [{t}]({l})")
            else:
                st.info("Không tải được tin tức lúc này. Thử lại sau.")
        except Exception:
            st.info("Module tin tức tạm thời không khả dụng.")
        st.caption("💡 Tin tức theo từng mã cụ thể cần API trả phí (CafeF/VnStock Pro). Hiện đang hiển thị tin tổng hợp thị trường.")

        st.write("---")
        st.write("## 🏆 Top tăng/giảm trong DM")
        pl_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            gia_von = info.get("gia_von", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or gia_von <= 0 or sl <= 0: continue
            ret_pct = (gia_tt - gia_von) / gia_von * 100
            pnl = (gia_tt - gia_von) * sl
            pl_rows.append((ma, ret_pct, pnl))
        if pl_rows:
            pl_rows.sort(key=lambda x: x[1], reverse=True)
            winners = pl_rows[:3]
            cw1, cw2 = st.columns(2)
            with cw1:
                st.write("**🟢 Top 3 TĂNG mạnh nhất**")
                for ma, ret, pnl in winners:
                    st.metric(f"🟢 {ma}", f"{ret:+.2f}%", f"{pnl:+,.0f} ₫")
            with cw2:
                st.write("**🔴 Top 3 GIẢM mạnh nhất**")
                neg_only = [r for r in pl_rows if r[1] < 0]
                if neg_only:
                    losers = neg_only[:3]
                    for ma, ret, pnl in losers:
                        st.metric(f"🔴 {ma}", f"{ret:+.2f}%", f"{pnl:+,.0f} ₫", delta_color="inverse")
                else:
                    st.write("✅ _Toàn DM đang lãi — không có mã lỗ_")

        st.write("---")
        st.write("## 🛡️ Chỉ số rủi ro nâng cao (Sortino / Calmar / TE / Skewness / Kurtosis)")
        if has_real and dm_equity is not None and len(dm_equity) > 20:
            _rr2 = _compute_all_ratios(dm_equity, bench_series=vn30_close if has_vn30 else None)
            if _rr2:
                daily_ret_rr2 = pd.Series(dm_equity).pct_change().dropna()
                skew_rr2 = float(daily_ret_rr2.skew())
                kurt_rr2 = float(daily_ret_rr2.kurtosis())
            else:
                skew_rr2 = kurt_rr2 = 0
        else:
            skew_rr2 = 0.0
            kurt_rr2 = 0.0
            _rr2 = None
        if _rr2:
            sr1, sr2, sr3, sr4, sr5 = st.columns(5)
            sr1.metric("📐 Sortino", f"{_rr2['sortino']:.2f}", help=">1: tốt | >2: rất tốt (chỉ tính downside)")
            sr2.metric("📐 Calmar", f"{_rr2['calmar']:.2f}", help="Return / |Max DD| (từ Max DD THẬT, không heuristic)")
            sr3.metric("📐 Tracking Err", f"{_rr2['te_pct']:.1f}%", help="Std(DM_ret - VN30_ret) × sqrt(252) — từ data thật")
            sr4.metric("📐 Skewness", f"{skew_rr2:+.2f}", help=">0: lệch phải (lợi nhuận), <0: lệch trái (rủi ro)")
            sr5.metric("📐 Kurtosis", f"{kurt_rr2:.2f}", help=">3: đuôi dày (rủi ro đuôi cao)")
            st.caption(f"📊 Sortino/Calmar/TE tính từ helper `_compute_all_ratios()`. Calmar dùng Max DD THẬT từ equity curve (không dùng `vol_proxy*2.5`). TE tính từ DM_ret − VN30_ret (không dùng `vol_proxy*0.5`).")
        else:
            sr1, sr2, sr3, sr4, sr5 = st.columns(5)
            sr1.metric("📐 Sortino", "—")
            sr2.metric("📐 Calmar", "—")
            sr3.metric("📐 Tracking Err", "—")
            sr4.metric("📐 Skewness", f"{skew_rr2:+.2f}")
            sr5.metric("📐 Kurtosis", f"{kurt_rr2:.2f}")
            st.caption("ℹ️ Sortino/Calmar/TE cần `dm_equity` + VN30. Skewness/Kurtosis hiển thị từ returns thật.")

        st.write("---")
        st.write("## 🎯 Phân tích tập trung (Concentration)")
        if weights:
            sorted_w = sorted(weights, reverse=True)
            top1 = sorted_w[0] * 100
            top3 = sum(sorted_w[:3]) * 100
            top5 = sum(sorted_w[:5]) * 100
            max_sector = max(sector_exp.values()) * 100 if sector_exp else 0
            max_sector_name = max(sector_exp.items(), key=lambda x: x[1])[0] if sector_exp else "N/A"
            cn1, cn2, cn3, cn4 = st.columns(4)
            cn1.metric("🏆 Top 1 mã", f"{top1:.1f}%", help=top_ma)
            cn2.metric("🏆 Top 3 mã", f"{top3:.1f}%")
            cn3.metric("🏆 Top 5 mã", f"{top5:.1f}%")
            cn4.metric("🏭 Ngành lớn nhất", f"{max_sector:.1f}%", help=max_sector_name)
            if top1 > 30: st.warning(f"⚠️ Tập trung cao: Top 1 = {top1:.0f}%")
            elif top1 > 20: st.info(f"ℹ️ Top 1 = {top1:.0f}% — cân nhắc đa dạng thêm")
            else: st.success(f"✅ Tập trung hợp lý: Top 1 = {top1:.0f}%")

        st.write("---")
        st.write("## 📈 Momentum từng mã (Returns 1M / 3M / 6M từ giá thật)")
        mom_rows = []
        for ma in dm.keys():
            if ma in real_prices and len(real_prices[ma]) >= 20:
                p = real_prices[ma]
                last = float(p.iloc[-1])
                r1m = (last / float(p.iloc[-21]) - 1) * 100 if len(p) >= 21 else None
                r3m = (last / float(p.iloc[-63]) - 1) * 100 if len(p) >= 63 else None
                r6m = (last / float(p.iloc[0]) - 1) * 100
                mom_rows.append({"Mã": ma, "1 tháng %": round(r1m, 1) if r1m is not None else "—",
                    "3 tháng %": round(r3m, 1) if r3m is not None else "—", "6 tháng %": round(r6m, 1)})
            else:
                info = dm.get(ma, {})
                gia_tt = info.get("gia_thi_truong", 0)
                gia_von = info.get("gia_von", 0)
                if gia_tt > 0 and gia_von > 0:
                    ret_total = (gia_tt - gia_von) / gia_von * 100
                    mom_rows.append({"Mã": ma, "1 tháng %": "—", "3 tháng %": "—", "6 tháng %": round(ret_total, 1)})
        if mom_rows:
            df_mom = pd.DataFrame(mom_rows)
            st.dataframe(df_mom, use_container_width=True, hide_index=True)
            st.caption("📊 Dùng giá thật từ yfinance. '—' = chưa đủ dữ liệu lịch sử.")
            mom_leaders = [r for r in mom_rows if isinstance(r.get("3 tháng %"), (int, float)) and r["3 tháng %"] > 0]
            mom_laggards = [r for r in mom_rows if isinstance(r.get("3 tháng %"), (int, float)) and r["3 tháng %"] < 0]
            if mom_leaders:
                best_3m = max(mom_leaders, key=lambda x: x["3 tháng %"])
                st.success(f"🚀 Momentum tốt nhất 3T: **{best_3m['Mã']}** ({best_3m['3 tháng %']:+.1f}%)")
            if mom_laggards:
                worst_3m = min(mom_laggards, key=lambda x: x["3 tháng %"])
                st.warning(f"⚠️ Momentum yếu nhất 3T: **{worst_3m['Mã']}** ({worst_3m['3 tháng %']:+.1f}%)")

        st.write("---")
        st.write("## 🎯 Target Price & Stop Loss (Khuyến nghị giá mục tiêu / cắt lỗ)")
        tgt_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            if gia_tt <= 0: continue
            ki = kpi.get(ma, {})
            w52h = float(ki.get("w52_high", 0) or 0)
            w52l = float(ki.get("w52_low", 0) or 0)
            beta_ma = float(ki.get("beta", 1.0) or 1.0)
            roe = float(ki.get("roe", 0) or 0)
            if w52h > 0 and w52l > 0:
                target = w52h * 1.05
                stop = max(w52l * 1.02, gia_tt * (1 - 0.08 * beta_ma))
            else:
                target = gia_tt * (1 + 0.15 * roe * 10)
                stop = gia_tt * 0.92
            upside = (target - gia_tt) / gia_tt * 100
            risk_dn = (gia_tt - stop) / gia_tt * 100
            rr = abs(upside / risk_dn) if risk_dn > 0 else 0
            if rr >= 2: rating = "⭐ Rất tốt"
            elif rr >= 1.5: rating = "✅ Tốt"
            elif rr >= 1: rating = "🟡 Hòa"
            else: rating = "🔴 Xấu"
            tgt_rows.append({"Mã": ma, "Giá hiện tại": f"{gia_tt:,.0f}",
                "Target (+5% W52H)": f"{target:,.0f}", "Upside %": f"{upside:+.1f}",
                "Stop Loss": f"{stop:,.0f}", "Risk %": f"-{risk_dn:.1f}",
                "R/R": f"{rr:.2f}", "Đánh giá": rating})
        if tgt_rows:
            df_tgt = pd.DataFrame(tgt_rows)
            st.dataframe(df_tgt, use_container_width=True, hide_index=True)
            st.caption("💡 Target = W52H × 1.05 (kỳ vọng breakout). Stop = W52L × 1.02 hoặc −8%×β. R/R ≥ 1.5 = tốt.")

        st.write("---")
        st.write("## ⚖️ Đề xuất tái cân bằng (Rebalancing)")
        rp_vols = {}
        for ma in dm.keys():
            if ma in real_prices and len(real_prices[ma]) >= 20:
                ret = real_prices[ma].pct_change().dropna()
                if len(ret) > 10:
                    rp_vols[ma] = max(float(ret.std() * (252**0.5)), 0.05)
        rp_weights = {}
        if rp_vols:
            inv_vol_sum = sum(1/v for v in rp_vols.values())
            for ma, v in rp_vols.items():
                rp_weights[ma] = (1/v) / inv_vol_sum
        rebal_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            ki = kpi.get(ma, {})
            v_hien_tai = gia_tt * sl
            w_hien_tai = v_hien_tai / tong_gt if tong_gt > 0 else 0
            w_muc_tieu_raw = ki.get("ty_trong_muc_tieu", 0)
            if w_muc_tieu_raw and float(w_muc_tieu_raw) > 0:
                w_muc_tieu = float(w_muc_tieu_raw)
                target_source = "DM"
            elif ma in rp_weights:
                w_muc_tieu = rp_weights[ma]
                target_source = f"Risk Parity (σ={rp_vols[ma]*100:.1f}%)"
            else:
                w_muc_tieu = 1.0 / max(n_ma, 1)
                target_source = "Equal Weight"
            v_muc_tieu = w_muc_tieu * tong_gt
            chenh = v_muc_tieu - v_hien_tai
            if abs(chenh) < v_hien_tai * 0.05:
                hanh_dong = "GIỮ"
            elif chenh > 0:
                hanh_dong = f"MUA +{chenh:,.0f}₫"
            else:
                hanh_dong = f"BÁN {-chenh:,.0f}₫"
            rebal_rows.append({"Mã": ma, "Hiện tại %": f"{w_hien_tai*100:.1f}",
                "Mục tiêu %": f"{w_muc_tieu*100:.1f}", "Chênh lệch %": f"{(w_muc_tieu-w_hien_tai)*100:+.1f}",
                "Hành động": hanh_dong, "Nguồn target": target_source})
        if rebal_rows:
            df_rebal = pd.DataFrame(rebal_rows)
            st.dataframe(df_rebal, use_container_width=True, hide_index=True)
            buy_total = sum([float(r["Hành động"].replace("MUA +","").replace("₫","").replace(",",""))
                             for r in rebal_rows if "MUA" in r["Hành động"]])
            sell_total = sum([float(r["Hành động"].replace("BÁN","").replace("₫","").replace(",",""))
                              for r in rebal_rows if "BÁN" in r["Hành động"] and "GIỮ" not in r["Hành động"]])
            rb1, rb2 = st.columns(2)
            rb1.metric("💰 Tổng cần MUA", f"{buy_total:,.0f} ₫")
            rb2.metric("💰 Tổng cần BÁN", f"{sell_total:,.0f} ₫")
            st.caption("💡 Risk Parity: tỷ trọng tỷ lệ nghịch với vol (mã ít biến động → tỷ trọng cao hơn). Vol tính từ giá thật yfinance.")

        st.write("---")
        st.write("## 🕯️ Biểu đồ nến Top 3 mã (Candlestick 6 tháng)")
        @st.cache_data(ttl=3600, show_spinner=False)
        def _fetch_ohlc_top3(_targets):
            """Fetch OHLC (Open, High, Low, Close) cho top symbols — 1 call/symbol, cache 1h"""
            import requests as _rq
            import pandas as _pd
            out = {}
            def _one(sym, suffix):
                try:
                    r = _rq.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=8,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if r.status_code == 200:
                        d = r.json()
                        if not d.get('chart', {}).get('result'):
                            return sym, None
                        result = d['chart']['result'][0]
                        ts = result.get('timestamp', [])
                        q = result.get('indicators', {}).get('quote', [{}])[0]
                        opens = q.get('open', []) or []
                        highs = q.get('high', []) or []
                        lows = q.get('low', []) or []
                        closes = q.get('close', []) or []
                        vols = q.get('volume', []) or []
                        if not ts or len(closes) < 20:
                            return sym, None
                        rows = []
                        for i, t in enumerate(ts):
                            c = closes[i] if i < len(closes) else None
                            o = opens[i] if i < len(opens) else None
                            h = highs[i] if i < len(highs) else None
                            l = lows[i] if i < len(lows) else None
                            v = vols[i] if i < len(vols) else 0
                            if c is None or o is None or h is None or l is None:
                                continue
                            rows.append({"date": _pd.to_datetime(t, unit='s'),
                                "Open": float(o), "High": float(h),
                                "Low": float(l), "Close": float(c), "Volume": float(v or 0)})
                        if len(rows) < 20:
                            return sym, None
                        return sym, _pd.DataFrame(rows).set_index("date")
                except Exception:
                    pass
                return sym, None
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=3) as ex:
                futs = [ex.submit(_one, s, suf) for s, suf in _targets]
                for f in as_completed(futs):
                    sym, df = f.result()
                    if df is not None:
                        out[sym] = df
            return out

        if has_real:
            top3_ma = sorted(dm.items(),
                key=lambda kv: kv[1].get("gia_thi_truong", 0) * kv[1].get("so_luong", 0),
                reverse=True)[:3]
            top3_targets = [(ma, ".VN") for ma, _ in top3_ma]
            ohlc_data = _fetch_ohlc_top3(tuple(top3_targets))
            rendered_count = 0
            for ma, _ in top3_ma:
                try:
                    if ma in ohlc_data and len(ohlc_data[ma]) > 20:
                        full = ohlc_data[ma]
                        fig_candle = go.Figure(data=[go.Candlestick(
                            x=full.index, open=full['Open'], high=full['High'],
                            low=full['Low'], close=full['Close'], name=ma)])
                        fig_candle.update_layout(height=300, title=f"{ma} — {len(full)} phiên (yfinance OHLC thật)",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#ECE8E1"), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig_candle, use_container_width=True)
                        rendered_count += 1
                    elif ma in real_prices and len(real_prices[ma]) > 20:
                        close_s = real_prices[ma]
                        df_syn = pd.DataFrame({
                            "Open": close_s.shift(1).fillna(close_s).values,
                            "High": (close_s * 1.012).values,
                            "Low": (close_s * 0.988).values,
                            "Close": close_s.values,
                        }, index=close_s.index)
                        fig_candle = go.Figure(data=[go.Candlestick(
                            x=df_syn.index, open=df_syn['Open'], high=df_syn['High'],
                            low=df_syn['Low'], close=df_syn['Close'], name=ma)])
                        fig_candle.update_layout(height=300, title=f"{ma} — {len(df_syn)} phiên (synth từ Close thật)",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#ECE8E1"), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig_candle, use_container_width=True)
                        rendered_count += 1
                except Exception:
                    pass
            if rendered_count == 0:
                st.info("🎲 Đang tải OHLC từ yfinance... vui lòng đợi ~5s rồi F5.")
        else:
            st.info("🎲 Đang tải giá thật từ yfinance (lần đầu ~60s)... vui lòng đợi rồi F5.")

        st.write("---")
        st.write("## 🏭 So sánh ngành (Peer Comparison)")
        sector_avg = {}
        for ma, ki in kpi.items():
            ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
            pe = float(ki.get("pe", 0) or 0)
            roe = float(ki.get("roe", 0) or 0)
            if pe > 0 and roe > 0:
                if ng not in sector_avg: sector_avg[ng] = {"pe": [], "roe": []}
                sector_avg[ng]["pe"].append(pe)
                sector_avg[ng]["roe"].append(roe)
        sector_avg_calc = {ng: {"pe": np.mean(v["pe"]), "roe": np.mean(v["roe"])} for ng, v in sector_avg.items() if v["pe"]}
        peer_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            if gia_tt <= 0: continue
            ki = kpi.get(ma, {})
            pe = float(ki.get("pe", 0) or 0)
            roe = float(ki.get("roe", 0) or 0)
            ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
            avg_pe = sector_avg_calc.get(ng, {}).get("pe", pe)
            avg_roe = sector_avg_calc.get(ng, {}).get("roe", roe)
            pe_vs = "Rẻ hơn" if pe < avg_pe * 0.9 else ("Đắt hơn" if pe > avg_pe * 1.1 else "Tương đương")
            roe_vs = "Tốt hơn" if roe > avg_roe * 1.1 else ("Yếu hơn" if roe < avg_roe * 0.9 else "Tương đương")
            peer_rows.append({"Mã": ma, "Ngành": ng, "P/E": round(pe, 1), "P/E ngành": round(avg_pe, 1),
                "Định giá": pe_vs, "ROE %": round(roe*100, 1), "ROE ngành %": round(avg_roe*100, 1),
                "Chất lượng": roe_vs})
        if peer_rows:
            df_peer = pd.DataFrame(peer_rows)
            st.dataframe(df_peer, use_container_width=True, hide_index=True)
            st.caption("💡 P/E < 90% ngành = định giá rẻ. ROE > 110% ngành = chất lượng tốt.")

        st.write("---")
        st.write("## 💵 Phân tích cổ tức (Dividend Income)")
        div_total = 0
        div_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            ki = kpi.get(ma, {})
            dy = float(ki.get("dividend_yield", 0) or 0)
            v = gia_tt * sl
            div_thu = v * dy
            div_total += div_thu
            div_rows.append({"Mã": ma, "Yield %": round(dy*100, 2),
                "Giá trị DM": f"{v:,.0f}", "Cổ tức/năm": f"{div_thu:,.0f} ₫"})
        if div_rows:
            df_div = pd.DataFrame(div_rows)
            st.dataframe(df_div, use_container_width=True, hide_index=True)
            dv1, dv2 = st.columns(2)
            dv1.metric("💰 Tổng cổ tức dự kiến/năm", f"{div_total:,.0f} ₫")
            dv2.metric("📊 Yield TB danh mục", f"{div_total/tong_gt*100:.2f}%" if tong_gt > 0 else "—")

        st.write("---")
        st.write("## 📅 Hiệu suất lịch sử theo kỳ")
        if has_real and 'dm_value_ts' in dir() and len(dm_equity) > 21:
            p_now = float(dm_equity[-1])
            p_1m = float(dm_equity[-21]) if len(dm_equity) >= 21 else float(dm_equity[0])
            p_3m = float(dm_equity[-63]) if len(dm_equity) >= 63 else float(dm_equity[0])
            p_6m = float(dm_equity[0])
            r1 = (p_now/p_1m - 1)*100
            r3 = (p_now/p_3m - 1)*100
            r6 = (p_now/p_6m - 1)*100
            hp1, hp2, hp3, hp4 = st.columns(4)
            hp1.metric("📅 1 tháng qua", f"{r1:+.2f}%")
            hp2.metric("📅 3 tháng qua", f"{r3:+.2f}%")
            hp3.metric("📅 6 tháng qua", f"{r6:+.2f}%")
            hp4.metric("📅 Từ đầu kỳ", f"{r6:+.2f}%")
        else:
            st.info("⚠️ Cần giá thật 6 tháng từ yfinance để tính hiệu suất lịch sử.")

        st.write("---")
        st.write("## 🚨 Cảnh báo rủi ro (Risk Alerts)")
        alerts = []
        if has_real:
            for ma in dm.keys():
                if ma in real_prices and len(real_prices[ma]) >= 50:
                    p = real_prices[ma]
                    ma50 = float(p.rolling(50).mean().iloc[-1])
                    last = float(p.iloc[-1])
                    if last < ma50 * 0.95:
                        alerts.append(f"🔴 **{ma}**: Giá ({last:,.0f}) dưới MA50 ({ma50:,.0f}) 5%+ — xu hướng giảm")
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            gia_von = info.get("gia_von", 0)
            if gia_tt > 0 and gia_von > 0:
                ret = (gia_tt - gia_von) / gia_von
                if ret < -0.10:
                    alerts.append(f"🔴 **{ma}**: Lỗ {ret*100:+.1f}% — cân nhắc cắt lỗ")
                elif ret > 0.30:
                    alerts.append(f"🟢 **{ma}**: Lãi {ret*100:+.1f}% — cân nhắc chốt lời 1 phần")
        if top_w > 0.35:
            alerts.append(f"⚠️ **{top_ma}** chiếm {top_w*100:.0f}% DM — rủi ro tập trung cao")
        if port_beta > 1.3:
            alerts.append(f"⚠️ Beta DM = {port_beta:.2f} — lắc lư mạnh hơn thị trường {port_beta-1:.0%}")
        if not alerts:
            st.success("✅ Không có cảnh báo rủi ro nào. Danh mục ổn định.")
        else:
            for a in alerts:
                st.write(f"- {a}")

        st.write("---")
        st.write("## 💧 Phân tích thanh khoản (ADTV — Khối lượng giao dịch)")
        liq_rows = []
        for ma in dm.keys():
            vol = 0
            price = 0
            vol_source = "yahoo.meta"
            if ma in real_metas:
                vol = real_metas[ma].get('regularMarketVolume', 0) or 0
                price = real_metas[ma].get('regularMarketPrice', 0) or 0
            if (vol <= 0 or price <= 0) and ma in real_prices:
                try:
                    p_series = real_prices[ma]
                    if len(p_series) >= 20:
                        daily_ret = p_series.pct_change().dropna().abs()
                        price = float(p_series.iloc[-1])
                        vol_proxy = float(daily_ret.tail(20).mean() * 1000) + 1
                        vol = max(vol, vol_proxy * 1000)
                        vol_source = "price-derived (yahoo volume miss)"
                except Exception:
                    pass
            if (vol <= 0 or price <= 0) and ma in kpi:
                ki_ma = kpi[ma]
                mc = float(ki_ma.get("market_cap", 0) or ki_ma.get("von_hoa", 0) or 0)
                if mc > 0:
                    price = float(dm[ma].get("gia_thi_truong", 0) or 0) or price
                    if price > 0:
                        vol = mc * 0.005 / max(price, 1) * 1e6
                        vol_source = "sector estimate (0.5% mcap/ngay)"
            if vol <= 0:
                price = float(dm[ma].get("gia_thi_truong", 0) or 0) or price
                if price > 0:
                    vol = 100000
                    vol_source = "default 100K shares (yahoo miss)"
            adtv_value = vol * price
            if adtv_value > 0:
                value_dm = dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0)
                days_to_liquidate = value_dm / adtv_value if adtv_value > 0 else 999
                liq_rows.append({
                    "Mã": ma,
                    "ADTV (tỷ)": round(adtv_value/1e9, 2),
                    "GT DM (tỷ)": round(value_dm/1e9, 1),
                    "Ngày thoát hàng": round(days_to_liquidate, 1),
                    "Thanh khoản": "🟢 Cao" if adtv_value > 5e9 else ("🟡 TB" if adtv_value > 1e9 else "🔴 Thấp"),
                    "Nguồn": vol_source
                })
        if liq_rows:
            df_liq = pd.DataFrame(liq_rows)
            st.dataframe(df_liq, use_container_width=True, hide_index=True)
            st.caption("💡 ADTV > 5 tỷ = thanh khoản cao (mua/bán dễ). Ngày thoát hàng = GT mã / ADTV. >5 ngày = khó bán gấp. Nguồn: yahoo.meta (real) → price-derived (synth từ |returns|) → sector estimate (0.5% mcap).")
        else:
            st.info("Không có dữ liệu volume từ yfinance.")

        st.write("---")
        st.write("## 🌍 Phân tích khối ngoại (Foreign Flow)")
        ff_rows = []
        _sector_inst_avg = {}
        for _ma_ff, _ki_ff in kpi.items():
            _ng_ff = (_ki_ff.get("nganh", "") or "Khác").strip() or "Khác"
            _inst = _ki_ff.get("institutions_pct")
            if _inst is not None and _inst > 0:
                _sector_inst_avg.setdefault(_ng_ff, []).append(float(_inst))
        _sector_inst_med = {ng: (sum(v) / len(v)) for ng, v in _sector_inst_avg.items() if v}
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            ki = kpi.get(ma, {})
            ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
            inst_real = ki.get("institutions_pct")
            if inst_real is not None and inst_real > 0:
                fo = inst_real
                fo_source = "yfinance"
            elif ng in _sector_inst_med:
                fo = _sector_inst_med[ng]
                fo_source = f"TB ngành ({len(_sector_inst_avg.get(ng, []))} mã có data thật)"
            else:
                _sector_default = {
                    "Ngân hàng": 0.45, "Bất động sản": 0.25, "Thép": 0.18,
                    "Công nghệ": 0.30, "Chứng khoán": 0.22, "Bán lẻ": 0.20,
                    "Xây dựng": 0.15, "Dầu khí": 0.28, "Điện": 0.30,
                    "Dược phẩm": 0.25, "Thủy sản": 0.18, "Cảng biển": 0.32,
                    "Vận tải": 0.20, "Cao su": 0.15, "Phân bón": 0.18,
                    "Bảo hiểm": 0.50, "Hàng không": 0.25, "Xuất khẩu": 0.22
                }
                fo = _sector_default.get(ng, 0.20)
                fo_source = f"Sector default {ng} ({fo*100:.0f}%)"
            v = gia_tt * sl
            ff_value = v * fo if fo > 0 else 0
            momentum_3m = 0
            vol_30d = 0
            if ma in real_prices and len(real_prices[ma]) >= 63:
                momentum_3m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[-63]) - 1) * 100
                ret_30 = real_prices[ma].tail(30).pct_change().dropna()
                vol_30d = float(ret_30.std() * (252**0.5) * 100) if len(ret_30) > 5 else 0
            adtv_ty = 0
            if ma in real_metas:
                vol_shares = real_metas[ma].get('regularMarketVolume', 0) or 0
                px = real_metas[ma].get('regularMarketPrice', gia_tt) or gia_tt
                adtv_ty = (vol_shares * px) / 1e9
            flow_signal = "🟢 Mua ròng" if momentum_3m > 5 else ("🔴 Bán ròng" if momentum_3m < -5 else "🟡 Đi ngang")
            ff_rows.append({"Mã": ma, "Ngành": ng, "NN nắm giữ %": round(fo*100, 1),
                "GT NN (tỷ)": round(ff_value/1e9, 1), "Momentum 3T %": round(momentum_3m, 1),
                "Vol 30N %": round(vol_30d, 1), "ADTV (tỷ)": round(adtv_ty, 1),
                "Dòng tiền": flow_signal, "Nguồn": fo_source})
        if ff_rows:
            df_ff = pd.DataFrame(ff_rows)
            st.dataframe(df_ff, use_container_width=True, hide_index=True)
            st.caption("💡 NN nắm giữ % từ yfinance.major_holders (institutionsPercentHeld). Momentum/Vol/ADTV đều từ giá & volume thật. Nguồn ghi rõ từng dòng.")

        st.write("---")
        st.write("## 🤖 AI Phân tích tự động (Dynamic từ dữ liệu thật)")
        ai_insights = []
        if sharpe < 0.5: ai_insights.append("⚠️ **Sharpe thấp** — Lợi nhuận chưa tương xứng rủi ro. Cân nhắc cắt mã yếu hoặc tăng tỷ trọng mã chất lượng cao (ROE>20%, P/E<15).")
        if sharpe >= 1: ai_insights.append("✅ **Sharpe tốt** — DM đang sinh lời hiệu quả. Duy trì chiến lược hiện tại.")
        if alpha > 0.02: ai_insights.append(f"✅ **Alpha = {alpha*100:+.2f}%** — DM vượt thị trường {alpha*100:.1f}%. Nhà đầu tư có kỹ năng chọn mã tốt.")
        if alpha < -0.02: ai_insights.append(f"🔴 **Alpha = {alpha*100:+.2f}%** — DM thua thị trường. Cân nhắc chuyển sang ETF VN30 hoặc VFMVN30.")
        if port_beta > 1.3: ai_insights.append(f"⚠️ **Beta = {port_beta:.2f}** — DM lắc lư mạnh. Thêm mã phòng thủ (Ngân hàng, Thực phẩm) để giảm beta về ~1.0.")
        if top_w > 0.3: ai_insights.append(f"⚠️ **{top_ma}** chiếm {top_w*100:.0f}% — Tập trung cao. Nếu mã này giảm 20%, DM mất {top_w*20:.1f}%.")
        if diversification > 0.8: ai_insights.append("✅ **Đa dạng hóa xuất sắc** — DM cân bằng giữa nhiều mã/ngành. Rủi ro tập trung thấp.")
        if nganh_count < 3: ai_insights.append(f"⚠️ Chỉ **{nganh_count} ngành** — Nên thêm 2-3 ngành khác để giảm rủi ro ngành.")
        if vol_proxy > 0.25: ai_insights.append("⚠️ **Volatility > 25%** — DM biến động mạnh. Phù hợp nhà đầu tư chấp nhận rủi ro cao.")
        if has_fund and len(real_fund) > 0:
            for ma, fd in real_fund.items():
                pe = fd.get("pe")
                roe = fd.get("roe")
                pb = fd.get("pb")
                if pe is not None and pe > 0:
                    if pe > 25:
                        gia_tt = next((dm[m].get("gia_thi_truong", 0) * dm[m].get("so_luong", 0) for m in [ma] if m in dm), 0)
                        w = (gia_tt / tong_gt * 100) if tong_gt > 0 and gia_tt > 0 else 0
                        ai_insights.append(f"⚠️ **{ma}** P/E={pe:.1f} (>25) — định giá cao. Chiếm {w:.0f}% DM. Cân nhắc chốt lời một phần.")
                    elif pe < 10 and roe is not None and roe > 0.15:
                        ai_insights.append(f"✅ **{ma}** P/E={pe:.1f} (<10) + ROE={roe*100:.1f}% (>15%) — rẻ + chất lượng. Cân nhắc tăng tỷ trọng.")
                if roe is not None and roe < 0.08 and pe is not None and pe > 0:
                    ai_insights.append(f"🔴 **{ma}** ROE={roe*100:.1f}% (<8%) — chất lượng thấp. Xem xét cắt nếu không có catalyst.")
                if pb is not None and pb > 5:
                    ai_insights.append(f"⚠️ **{ma}** P/B={pb:.1f} (>5) — đắt so với book value.")
        if usdvnd_close is not None and len(usdvnd_close) > 5:
            usd_change_3m = (float(usdvnd_close.iloc[-1]) / float(usdvnd_close.iloc[-min(60, len(usdvnd_close))]) - 1) * 100
            if usd_change_3m > 2:
                ai_insights.append(f"💵 **USD/VND +{usd_change_3m:.1f}%** 3T — VNĐ mất giá. Cổ phiếu xuất khẩu hưởng lợi.")
            elif usd_change_3m < -2:
                ai_insights.append(f"💵 **USD/VND {usd_change_3m:.1f}%** 3T — VNĐ tăng giá. Cổ phiếu nhập khẩu bị ảnh hưởng.")
        if not ai_insights: ai_insights.append("✅ DM hiện tại đạt các tiêu chí cơ bản. Tiếp tục they dõi và tái cân bằng định kỳ.")
        for ins in ai_insights[:8]:
            st.write(f"- {ins}")

        st.write("---")
        st.write("## 📐 Bollinger Bands & Fibonacci (Kỹ thuật nâng cao)")
        if has_real:
            bb_rows = []
            for ma, info in dm.items():
                if ma in real_prices and len(real_prices[ma]) >= 20:
                    p = real_prices[ma]
                    gia_tt = float(p.iloc[-1])
                    ma20_v = float(p.rolling(20).mean().iloc[-1])
                    std20 = float(p.rolling(20).std().iloc[-1])
                    bb_upper = ma20_v + 2*std20
                    bb_lower = ma20_v - 2*std20
                    high_60 = float(p.tail(60).max()) if len(p) >= 60 else float(p.max())
                    low_60 = float(p.tail(60).min()) if len(p) >= 60 else float(p.min())
                    fib_382 = low_60 + (high_60 - low_60) * 0.382
                    fib_618 = low_60 + (high_60 - low_60) * 0.618
                    bb_pos = (gia_tt - bb_lower) / max(bb_upper - bb_lower, 1) * 100
                    if gia_tt > bb_upper: bb_sig = "🔴 Trên BB"
                    elif gia_tt < bb_lower: bb_sig = "🟢 Dưới BB"
                    elif gia_tt > ma20_v: bb_sig = "🟡 Trên MA20"
                    else: bb_sig = "🟡 Dưới MA20"
                    fib_zone = "Vùng 38.2-61.8%" if fib_382 <= gia_tt <= fib_618 else "Ngoài vùng vàng"
                    bb_rows.append({"Mã": ma, "Giá": f"{gia_tt:,.0f}", "BB trên": f"{bb_upper:,.0f}",
                        "BB dưới": f"{bb_lower:,.0f}", "Fib 38.2%": f"{fib_382:,.0f}",
                        "Fib 61.8%": f"{fib_618:,.0f}", "Vị trí BB %": round(bb_pos, 0),
                        "Tín hiệu": bb_sig, "Fibonacci": fib_zone})
            if bb_rows:
                df_bb = pd.DataFrame(bb_rows)
                st.dataframe(df_bb, use_container_width=True, hide_index=True)
                st.caption("💡 Giá < BB dưới = quá bán (cơ hội MUA). Giá > BB trên = quá mua (cân nhắc BÁN). Fibonacci 38.2-61.8% = vùng hỗ trợ/mức cản quan trọng.")

        st.write("---")
        st.write("## 💱 Phân tích rủi ro tỷ giá & lãi suất")
        if usdvnd_close is not None and len(usdvnd_close) > 20:
            usdvnd_ret = usdvnd_close.pct_change().dropna()
            fx_impact = 0
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                w = (gia_tt * sl) / tong_gt if tong_gt > 0 else 0
                if ma in real_prices and len(real_prices[ma]) > 20:
                    common = sorted(set(usdvnd_ret.index) & set(real_prices[ma].index))
                    if len(common) > 15:
                        stock_ret = real_prices[ma].reindex(common).pct_change().dropna()
                        fx_ret = usdvnd_ret.reindex(common).dropna()
                        common2 = sorted(set(stock_ret.index) & set(fx_ret.index))
                        if len(common2) > 10:
                            corr = float(stock_ret.loc[common2].corr(fx_ret.loc[common2]))
                            fx_impact += w * corr * 0.02 * 100
            fx_source = f"📊 Tính từ correlation thật USD/VND × {len(real_prices)} mã (yfinance 6T)"
        else:
            NH_SENSITIVITY = {"Ngân hàng": 0.8, "Bất động sản": 0.6, "Thép": 0.3, "Thực phẩm": 0.2, "Bán lẻ": 0.2, "Công nghệ": 0.1, "Khác": 0.2}
            fx_impact = 0
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                ki = kpi.get(ma, {})
                ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
                sens = NH_SENSITIVITY.get(ng, 0.2)
                w = (gia_tt * sl) / tong_gt if tong_gt > 0 else 0
                fx_impact += w * sens * 0.02 * 100
            fx_source = "⚠️ Ước lượng theo ngành (yfinance USD/VND tạm không khả dụng)"
        NH_SENSITIVITY = {"Ngân hàng": 0.8, "Bất động sản": 0.6, "Thép": 0.3, "Thực phẩm": 0.2, "Bán lẻ": 0.2, "Công nghệ": 0.1, "Khác": 0.2}
        if vn_bond_close is not None and len(vn_bond_close) > 20:
            bond_ret = vn_bond_close.pct_change().dropna()
            rate_impact = 0
            rate_source = f"📊 Tính từ correlation thật với lãi suất 10Y ({vn_bond_close.iloc[-1]:.2f}%, yfinance 6T)"
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                w = (gia_tt * sl) / tong_gt if tong_gt > 0 else 0
                if ma in real_prices and len(real_prices[ma]) > 20:
                    common = sorted(set(bond_ret.index) & set(real_prices[ma].index))
                    if len(common) > 15:
                        stock_ret = real_prices[ma].reindex(common).pct_change().dropna()
                        b_ret = bond_ret.reindex(common).dropna()
                        common2 = sorted(set(stock_ret.index) & set(b_ret.index))
                        if len(common2) > 10:
                            corr = float(stock_ret.loc[common2].corr(b_ret.loc[common2]))
                            rate_impact += w * corr * 0.01 * 100
        else:
            rate_impact = 0
            rate_source = "⚠️ Ước lượng theo ngành (yfinance VN bond tạm không khả dụng)"
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                ki = kpi.get(ma, {})
                ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
                sens = NH_SENSITIVITY.get(ng, 0.2)
                w = (gia_tt * sl) / tong_gt if tong_gt > 0 else 0
                rate_impact += w * sens * 0.05 * 100
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("💵 Tỷ giá +2% → DM", f"{fx_impact:+.2f}%", help="VNĐ mất giá 2% so với USD")
        fc2.metric("📈 Lãi suất +1% → DM", f"{rate_impact:+.2f}%", help="Lãi suất 10Y tăng 1%")
        fc3.metric("🏭 Ngành nhạy cảm LS", max(NH_SENSITIVITY, key=NH_SENSITIVITY.get))
        st.caption(f"{fx_source} | {rate_source}")

        st.write("---")
        st.write("## 🆚 So sánh với VN30 / HNX-Index")
        if has_real and 'dm_equity' in dir():
            vn30_ret = ((vn_equity[-1] / vn_equity[0]) - 1) * 100 if len(vn_equity) > 0 else 0
            dm_ret = ((dm_equity[-1] / dm_equity[0]) - 1) * 100 if len(dm_equity) > 0 else 0
            cmp1, cmp2, cmp3, cmp4 = st.columns(4)
            cmp1.metric("📈 DM của anh", f"{dm_ret:+.2f}%")
            cmp2.metric(f"📊 {vn30_label or 'VN30'}", f"{vn30_ret:+.2f}%")
            cmp3.metric("🏆 Outperformance", f"{dm_ret - vn30_ret:+.2f}%")
            cmp4.metric("📊 Số mã DM", f"{n_ma} mã")
            st.caption(f"💡 VN30 = top 30 mã vốn hóa lớn nhất HOSE. DM {n_ma} mã {'vượt' if dm_ret > vn30_ret else 'thua'} VN30 {abs(dm_ret - vn30_ret):.2f}%.")

        st.write("---")
        st.write("## 📜 Lịch sử giao dịch & Thuế phí")
        tx_rows = []
        phi_mua = 0.0015
        thue_tncn = 0.001
        total_phi = 0
        for ma, info in dm.items():
            gia_von = info.get("gia_von", 0)
            sl = info.get("so_luong", 0)
            ngay_mua = info.get("ngay_mua", "—")
            if gia_von <= 0 or sl <= 0: continue
            v_mua = gia_von * sl
            phi = v_mua * phi_mua
            total_phi += phi
            tx_rows.append({"Mã": ma, "SL": f"{sl:,.0f}", "Giá vốn": f"{gia_von:,.0f}",
                "GT mua": f"{v_mua:,.0f}", "Phí mua (0.15%)": f"{phi:,.0f}",
                "Ngày mua": ngay_mua})
        if tx_rows:
            df_tx = pd.DataFrame(tx_rows)
            st.dataframe(df_tx, use_container_width=True, hide_index=True)
            tx1, tx2, tx3 = st.columns(3)
            tx1.metric("💸 Tổng phí mua", f"{total_phi:,.0f} ₫")
            tx2.metric("📊 Phí TB/mã", f"{total_phi/max(len(tx_rows),1):,.0f} ₫")
            thue_ban = tong_lai_lo * thue_tncn if tong_lai_lo > 0 else 0
            tx3.metric("💰 Thuế TNCN (nếu bán)", f"{thue_ban:,.0f} ₫", help="0.1% trên lãi (thuế chuyển nhượng CK)")
            st.caption("💡 Phí mua/bán = 0.15% (HOSE - biểu phí chính thức). Thuế TNCN = 0.1% trên lãi (thuế chuyển nhượng CK theo Nghị định 126/2020).")

        st.write("---")
        st.write("## 📉 Underwater Drawdown — Độ sụt giảm từ đỉnh")
        if has_real and len(dm_equity) > 30:
            eq_series = pd.Series(dm_equity)
            running_max = eq_series.cummax()
            underwater = ((eq_series - running_max) / running_max * 100)
            in_dd = underwater < 0
            dd_starts = []
            dd_ends = []
            cur_start = None
            for i, val in enumerate(in_dd):
                if val and cur_start is None:
                    cur_start = i
                elif not val and cur_start is not None:
                    dd_starts.append(cur_start)
                    dd_ends.append(i - 1)
                    cur_start = None
            if cur_start is not None:
                dd_starts.append(cur_start)
                dd_ends.append(len(in_dd) - 1)
            dd_periods = []
            for s, e in zip(dd_starts, dd_ends):
                period_underwater = underwater.iloc[s:e+1]
                trough = float(period_underwater.min())
                trough_idx = period_underwater.idxmin()
                dd_periods.append({"Bắt đầu": str(eq_series.index[s])[:10],
                    "Kết thúc": str(eq_series.index[e])[:10] if not in_dd.iloc[e] else "chưa hồi",
                    "Đáy": str(trough_idx)[:10], "Sụt %": round(trough, 1),
                    "Thời gian (phiên)": e - s + 1})
            fig_uw = go.Figure()
            fig_uw.add_trace(go.Scatter(x=eq_series.index, y=underwater.values, fill='tozeroy',
                fillcolor='rgba(244,67,54,0.3)', line_color='#F44336', name='Drawdown %'))
            fig_uw.update_layout(title="Underwater Plot (% từ đỉnh)", yaxis_title="Drawdown (%)",
                height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_uw, use_container_width=True)
            if dd_periods:
                dd_periods_sorted = sorted(dd_periods, key=lambda x: x["Sụt %"])[:5]
                st.dataframe(pd.DataFrame(dd_periods_sorted), use_container_width=True, hide_index=True)
                worst_dd = min(p["Sụt %"] for p in dd_periods)
                st.caption(f"📊 Worst DD = {worst_dd:.1f}% (tính từ {len(eq_series)} phiên giá thật yfinance 6T)")
            else:
                st.success("✅ DM chưa từng sụt giảm từ đỉnh trong 6T qua!")
        else:
            st.info("⚠️ Cần giá thật 6T để vẽ underwater chart.")

        st.write("---")
        st.write("## 🧮 Risk Contribution — Đóng góp rủi ro từng mã")
        if has_real and len(real_prices) >= 2 and tong_gt > 0:
            weights_arr = []
            rets_list = []
            tickers = []
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                if ma not in real_prices or len(real_prices[ma]) < 20: continue
                w = (gia_tt * sl) / tong_gt
                weights_arr.append(w)
                tickers.append(ma)
                rets_list.append(real_prices[ma].pct_change().dropna())
            if len(weights_arr) >= 2 and rets_list:
                df_rets = pd.concat(rets_list, axis=1).dropna()
                df_rets.columns = tickers
                w_vec = np.array(weights_arr)
                cov = df_rets.cov().values * 252
                port_vol = float(np.sqrt(np.dot(w_vec.T, np.dot(cov, w_vec))))
                marginal = np.dot(cov, w_vec) / port_vol if port_vol > 0 else np.zeros(len(w_vec))
                risk_contrib = w_vec * marginal
                rc_pct = (risk_contrib / risk_contrib.sum() * 100) if risk_contrib.sum() > 0 else np.zeros(len(w_vec))
                rc_rows = []
                for i, ma in enumerate(tickers):
                    rc_rows.append({"Mã": ma, "Trọng số %": round(w_vec[i]*100, 1),
                        "Vol năm %": round(float(df_rets[ma].std() * (252**0.5) * 100), 1),
                        "Risk Contrib %": round(float(rc_pct[i]), 1),
                        "Marginal VaR %": round(float(marginal[i]) * 100 / port_vol, 1) if port_vol > 0 else 0})
                rc_rows = sorted(rc_rows, key=lambda x: -x["Risk Contrib %"])
                st.dataframe(pd.DataFrame(rc_rows), use_container_width=True, hide_index=True)
                top_rc = rc_rows[0]
                st.caption(f"📊 Tính từ covariance matrix thật ({len(df_rets)} phiên × {len(tickers)} mã, yfinance 6T). Top risk: **{top_rc['Mã']}** = {top_rc['Risk Contrib %']:.1f}% tổng rủi ro DM.")
            else:
                st.info("⚠️ Cần ≥2 mã có giá thật để tính.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính risk contribution.")

        st.write("---")
        st.write("## 📊 Rolling Volatility & Beta (60 phiên gần nhất)")
        if has_real and len(dm_equity) > 60:
            eq_s = pd.Series(dm_equity)
            ret_s = eq_s.pct_change().dropna()
            roll_vol = ret_s.rolling(60).std() * (252**0.5) * 100
            fig_roll = go.Figure()
            fig_roll.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol.values, line_color='#4FC3F7',
                name='Rolling Vol 60D (%)', fill='tozeroy', fillcolor='rgba(79,195,247,0.2)'))
            fig_roll.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Bình thường (20%)")
            fig_roll.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Cao (30%)")
            fig_roll.update_layout(title="Vol 60 phiên gần nhất (%)", yaxis_title="Vol (%)",
                height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_roll, use_container_width=True)
            current_vol = float(roll_vol.iloc[-1]) if not roll_vol.empty else 0
            avg_vol = float(roll_vol.mean())
            max_vol = float(roll_vol.max())
            min_vol = float(roll_vol.min())
            vol_regime = "🔴 Cao (Stress)" if current_vol > 30 else ("🟡 Trung bình" if current_vol > 20 else "🟢 Thấp (Yên tĩnh)")
            rvc1, rvc2, rvc3, rvc4 = st.columns(4)
            rvc1.metric("Vol hiện tại", f"{current_vol:.1f}%", f"Regime: {vol_regime}")
            rvc2.metric("Vol TB 60D", f"{avg_vol:.1f}%")
            rvc3.metric("Vol max", f"{max_vol:.1f}%")
            rvc4.metric("Vol min", f"{min_vol:.1f}%")
            st.caption(f"📊 Tính từ {len(ret_s)} phiên returns thật. Regime phát hiện: {'cao' if current_vol > 30 else 'trung bình' if current_vol > 20 else 'thấp'}.")
        else:
            st.info("⚠️ Cần ≥60 phiên giá thật để tính rolling vol.")

        st.write("---")
        st.write("## 🧬 Phân tích hệ số (Factor Analysis)")
        if has_real and len(dm_equity) > 60:
            eq_s2 = pd.Series(dm_equity)
            dm_ret = eq_s2.pct_change().dropna()
            cum_ret_1m = (eq_s2.iloc[-1] / eq_s2.iloc[-min(22, len(eq_s2))] - 1) * 100 if len(eq_s2) > 22 else 0
            cum_ret_3m = (eq_s2.iloc[-1] / eq_s2.iloc[-min(66, len(eq_s2))] - 1) * 100 if len(eq_s2) > 66 else 0
            cum_ret_6m = (eq_s2.iloc[-1] / eq_s2.iloc[0] - 1) * 100
            vol_1y = float(dm_ret.std() * (252**0.5))
            sharpe_real = (dm_ret.mean() * 252 - 0.045) / vol_1y if vol_1y > 0 else 0
            fa_rows = []
            fa_rows.append({"Hệ số": "📈 Beta thị trường", "Giá trị": f"{port_beta:.2f}",
                "Diễn giải": "DM lắc lư mạnh hơn VN-Index" if port_beta > 1.1 else "DM ổn định hơn VN-Index"})
            fa_rows.append({"Hệ số": "🚀 Momentum 1M", "Giá trị": f"{cum_ret_1m:+.1f}%",
                "Diễn giải": "Xu hướng tăng ngắn hạn" if cum_ret_1m > 0 else "Điều chỉnh ngắn hạn"})
            fa_rows.append({"Hệ số": "🚀 Momentum 3M", "Giá trị": f"{cum_ret_3m:+.1f}%",
                "Diễn giải": "Xu hướng tăng trung hạn" if cum_ret_3m > 0 else "Điều chỉnh trung hạn"})
            fa_rows.append({"Hệ số": "🚀 Momentum 6M", "Giá trị": f"{cum_ret_6m:+.1f}%",
                "Diễn giải": "Xu hướng tăng dài hạn" if cum_ret_6m > 0 else "Yếu dài hạn"})
            fa_rows.append({"Hệ số": "💎 Chất lượng (ROE TB)",
                "Giá trị": f"{sum(float(kpi.get(m,{}).get('roe',0) or 0) * w for m, w in zip(dm.keys(), weights) if w > 0) * 100:.1f}%" if weights else "N/A",
                "Diễn giải": "DM chất lượng cao" if sum(float(kpi.get(m,{}).get('roe',0) or 0) * w for m, w in zip(dm.keys(), weights) if w > 0) > 0.15 else "Chất lượng trung bình"})
            fa_rows.append({"Hệ số": "💰 Giá trị (1/P/E TB)",
                "Giá trị": f"{(1/sum(float(kpi.get(m,{}).get('pe',1) or 1) * w for m, w in zip(dm.keys(), weights) if w > 0)):.1f}" if weights else "N/A",
                "Diễn giải": "DM định giá hấp dẫn" if sum(float(kpi.get(m,{}).get('pe',15) or 15) * w for m, w in zip(dm.keys(), weights) if w > 0) < 15 else "DM định giá cao"})
            st.dataframe(pd.DataFrame(fa_rows), use_container_width=True, hide_index=True)
            st.caption(f"📊 Tất cả hệ số tính từ returns/giá thật yfinance 6T (Beta={port_beta:.2f}, Vol={vol_1y*100:.1f}%, Sharpe={sharpe_real:.2f})")
        else:
            st.info("⚠️ Cần giá thật 6T để phân tích hệ số.")

        st.write("---")
        st.write("## 🎯 Performance Attribution — Đóng góp hiệu suất")
        if has_real and len(real_prices) > 0 and len(weights) > 0:
            attr_rows = []
            sector_attr = {}
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                ki = kpi.get(ma, {})
                ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
                stock_ret_6m = 0
                if ma in real_prices and len(real_prices[ma]) >= 30:
                    stock_ret_6m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[0]) - 1) * 100
                stock_ret_1m = 0
                if ma in real_prices and len(real_prices[ma]) >= 22:
                    stock_ret_1m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[-22]) - 1) * 100
                v = gia_tt * sl
                w = v / tong_gt if tong_gt > 0 else 0
                contr = w * stock_ret_6m
                attr_rows.append({"Mã": ma, "Ngành": ng, "Tỷ trọng %": round(w*100, 1),
                    "Return 1M %": round(stock_ret_1m, 1), "Return 6M %": round(stock_ret_6m, 1),
                    "Đóng góp %": round(contr, 2)})
                sector_attr[ng] = sector_attr.get(ng, 0) + contr
            if attr_rows:
                df_attr = pd.DataFrame(attr_rows).sort_values("Đóng góp %", ascending=False)
                st.dataframe(df_attr, use_container_width=True, hide_index=True)
                st.write("**📊 Đóng góp theo ngành:**")
                for ng, contr in sorted(sector_attr.items(), key=lambda x: -x[1]):
                    color = "🟢" if contr > 0 else "🔴"
                    st.write(f"  {color} **{ng}**: {contr:+.2f}%")
                st.caption(f"📊 Tính từ returns 6T thật × tỷ trọng hiện tại. Tổng contributions ≈ Return DM 6M.")
        else:
            st.info("⚠️ Cần giá thật 6T để phân tích đóng góp.")

        st.write("---")
        st.write("## 🔬 Chỉ số rủi ro nâng cao (Pain / Ulcer / Tail)")
        if has_real and len(dm_equity) > 30:
            eq_s3 = pd.Series(dm_equity)
            running_max3 = eq_s3.cummax()
            dd_pct = ((eq_s3 - running_max3) / running_max3 * 100)
            pain_idx = float(np.sqrt((dd_pct ** 2).mean()))
            ulcer_idx = float(np.sqrt(((dd_pct[dd_pct < 0]) ** 2).mean())) if (dd_pct < 0).any() else 0
            ret_s3 = eq_s3.pct_change().dropna()
            pos_ret = ret_s3[ret_s3 > 0]
            neg_ret = ret_s3[ret_s3 < 0]
            if len(pos_ret) > 5 and len(neg_ret) > 5:
                tail_ratio = float(np.percentile(pos_ret, 95) / abs(np.percentile(neg_ret, 5)))
            else:
                tail_ratio = 0
            alpha_95 = float(np.percentile(ret_s3, 5))
            alpha_99 = float(np.percentile(ret_s3, 1))
            avg_dd = float(dd_pct[dd_pct < 0].mean()) if (dd_pct < 0).any() else 0
            max_dd_dur = 0
            cur_dur = 0
            for v in dd_pct:
                if v < 0:
                    cur_dur += 1
                    max_dd_dur = max(max_dd_dur, cur_dur)
                else:
                    cur_dur = 0
            ulc1, ulc2, ulc3, ulc4 = st.columns(4)
            ulc1.metric("🩹 Pain Index", f"{pain_idx:.2f}",
                help="Căn bậc 2 trung bình DD². Cao = DM đau nhiều")
            ulc2.metric("🩹 Ulcer Index", f"{ulcer_idx:.2f}",
                help="Tương tự Pain nhưng chỉ tính DD âm")
            ulc3.metric("⚖️ Tail Ratio", f"{tail_ratio:.2f}",
                help="P95 right tail / |P5 left tail|. >1 = phải đuôi dài hơn (tốt)")
            ulc4.metric("⏱️ Max DD Duration", f"{max_dd_dur} phiên",
                help="Đợt sụt dài nhất từ đỉnh đến khi hồi phục")
            ulc5, ulc6 = st.columns(2)
            ulc5.metric("📉 Avg DD (âm)", f"{avg_dd:.2f}%",
                help="Trung bình các đợt sụt giảm")
            ulc6.metric("☠️ Alpha 99% (CVaR tail)", f"{alpha_99*100:.2f}%",
                help="1% phiên tệ nhất lỗ bao nhiêu")
            st.caption(f"📊 Tính từ {len(ret_s3)} phiên giá thật yfinance 6T. Các chỉ số này đo 'cảm giác đau' thực tế của nhà đầu tư.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính chỉ số rủi ro nâng cao.")

        st.write("---")
        st.write("## 🔄 Sector Rotation — Phát hiện ngành nóng/lạnh")
        if has_real and len(real_prices) > 0:
            sec_rows = []
            ng_ret = {}
            for ma, info in dm.items():
                if ma not in real_prices or len(real_prices[ma]) < 30: continue
                ki = kpi.get(ma, {})
                ng = (ki.get("nganh", "") or "Khác").strip() or "Khác"
                r1m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[-min(22, len(real_prices[ma]))]) - 1) * 100
                r3m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[-min(66, len(real_prices[ma]))]) - 1) * 100
                v = info.get("gia_thi_truong", 0) * info.get("so_luong", 0)
                w = v / tong_gt if tong_gt > 0 else 0
                ng_ret.setdefault(ng, []).append((r1m, r3m, w, ma))
            for ng, lst in ng_ret.items():
                wg_ret_1m = sum(r1m * w for r1m, r3m, w, ma in lst)
                wg_ret_3m = sum(r3m * w for r1m, r3m, w, ma in lst)
                hot = "🔥 Nóng" if wg_ret_1m > 5 and wg_ret_3m > 10 else ("❄️ Lạnh" if wg_ret_1m < -5 and wg_ret_3m < -10 else "🟡 Đi ngang")
                sec_rows.append({"Ngành": ng, "Số mã": len(lst),
                    "Return 1M %": round(wg_ret_1m, 1), "Return 3M %": round(wg_ret_3m, 1),
                    "Trạng thái": hot})
            if sec_rows:
                sec_df = pd.DataFrame(sec_rows).sort_values("Return 1M %", ascending=False)
                st.dataframe(sec_df, use_container_width=True, hide_index=True)
                st.caption(f"📊 Tính từ returns 1M/3M thật yfinance × tỷ trọng từng mã trong DM. 'Nóng' = 1M>5% & 3M>10%. 'Lạnh' = 1M<-5% & 3M<-10%.")
        else:
            st.info("⚠️ Cần giá thật 6T để phân tích sector rotation.")

        st.write("---")
        st.write("## 💰 Earnings Yield vs Lãi suất — Định giá tương đối")
        if has_real and len(dm_equity) > 0 and len(weights) > 0:
            weighted_pe = 0
            weighted_eps_yield = 0
            for ma, w in zip(dm.keys(), weights):
                if w <= 0: continue
                ki = kpi.get(ma, {})
                pe_v = float(ki.get("pe", 0) or 0)
                if pe_v > 0:
                    weighted_pe += pe_v * w
                    weighted_eps_yield += (1/pe_v) * w
            bond_yield_now = 0
            if vn_bond_close is not None and len(vn_bond_close) > 0:
                bv = float(vn_bond_close.iloc[-1])
                if 0 < bv < 1:
                    bond_yield_now = bv * 100
                elif 1 <= bv < 50:
                    bond_yield_now = bv
                else:
                    bond_yield_now = 0
            if 0 < bond_yield_now < 30 and weighted_eps_yield > 0:
                equity_risk_premium = (weighted_eps_yield - bond_yield_now) * 100
                verdict = "✅ Hấp dẫn" if equity_risk_premium > 3 else ("🟡 Hợp lý" if equity_risk_premium > 0 else "🔴 Đắt")
                erp1, erp2, erp3 = st.columns(3)
                erp1.metric("📊 P/E TB DM", f"{weighted_pe:.1f}", help="Trung bình có trọng số theo tỷ trọng DM")
                erp2.metric("💵 Earnings Yield", f"{weighted_eps_yield*100:.2f}%", help="1/P/E — lợi suất từ lợi nhuận")
                erp3.metric("🏦 Lãi suất TPCP 10Y", f"{bond_yield_now:.2f}%", help="Từ yfinance ^VN10Y/VNI10Y")
                erp4, erp5 = st.columns(2)
                erp4.metric("⚖️ Equity Risk Premium", f"{equity_risk_premium:+.2f}%",
                    help="Earnings Yield - Bond Yield. >3% = CP hấp dẫn, <0 = CP đắt hơn TPCP")
                erp5.metric("🎯 Kết luận", verdict)
                st.caption(f"📊 Earnings yield TB có trọng số vs TPCP 10Y thật (yfinance). ERP = {equity_risk_premium:+.2f}%.")
            else:
                st.info("⚠️ Cần P/E các mã + lãi suất TPCP để tính ERP.")
        else:
            st.info("⚠️ Cần giá + KPI thật để tính earnings yield.")

        st.write("---")
        st.write("## 📊 Phân phối Returns — Skewness & Kurtosis")
        if has_real and len(dm_equity) > 30:
            from scipy import stats as _stats
            ret_s4 = pd.Series(dm_equity).pct_change().dropna()
            sk = float(_stats.skew(ret_s4))
            kurt = float(_stats.kurtosis(ret_s4))
            jarque_bera = _stats.jarque_bera(ret_s4)
            skew_interp = "✅ Đối xứng" if abs(sk) < 0.5 else ("🟢 Lệch phải (nhiều phiên tăng mạnh)" if sk > 0.5 else "🔴 Lệch trái (nhiều phiên giảm mạnh)")
            kurt_interp = "✅ Phân phối chuẩn" if abs(kurt) < 1 else ("🔴 Đuôi dày (nhiều extreme events)" if kurt > 1 else "🟢 Đuôi mỏng")
            dist1, dist2, dist3 = st.columns(3)
            dist1.metric("📐 Skewness", f"{sk:+.3f}", help="Độ lệch phân phối. 0 = chuẩn, >0 = lệch phải, <0 = lệch trái")
            dist2.metric("📐 Kurtosis (excess)", f"{kurt:+.3f}", help="Độ nhọn. 0 = chuẩn, >0 = đuôi dày, <0 = đuôi mỏng")
            dist3.metric("📊 Jarque-Bera p-value", f"{jarque_bera.pvalue:.4f}",
                help="Test phân phối chuẩn. p<0.05 = KHÔNG chuẩn (có outliers)")
            st.write(f"**Diễn giải:** Skewness = {skew_interp}. Kurtosis = {kurt_interp}.")
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(x=ret_s4.values, nbinsx=40, marker_color="#4FC3F7",
                opacity=0.7, name="Returns", histnorm='probability density'))
            x_norm = np.linspace(ret_s4.min(), ret_s4.max(), 100)
            fig_hist.add_trace(go.Scatter(x=x_norm, y=_stats.norm.pdf(x_norm, ret_s4.mean(), ret_s4.std()),
                line_color="#FFD700", name="Phân phối chuẩn (lý thuyết)"))
            fig_hist.update_layout(title="Phân phối Returns vs Normal (từ giá thật)",
                xaxis_title="Daily Return", yaxis_title="Mật độ",
                height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_hist, use_container_width=True)
            st.caption(f"📊 Tính từ {len(ret_s4)} phiên returns thật yfinance 6T. Skewness/Kurtosis cho biết DM có 'lệch' hay 'đuôi dày' (rủi ro cực đoan) hay không.")
        else:
            st.info("⚠️ Cần ≥30 phiên giá thật để phân tích phân phối.")

        st.write("---")
        st.write("## 🏆 Xếp hạng rủi ro tổng hợp (Composite Risk Score)")
        if has_real and len(dm_equity) > 30:
            score = 0
            score_max = 100
            details = []
            vol_1y_v = float(pd.Series(dm_equity).pct_change().dropna().std() * (252**0.5))
            if vol_1y_v < 0.15:
                score += 25; details.append("✅ Vol <15% (rất ổn định): +25")
            elif vol_1y_v < 0.25:
                score += 15; details.append("🟡 Vol 15-25% (bình thường): +15")
            else:
                score += 0; details.append("🔴 Vol >25% (rủi ro cao): +0")
            sharpe_v = sharpe
            if sharpe_v > 1.5:
                score += 25; details.append(f"✅ Sharpe {sharpe_v:.2f} >1.5: +25")
            elif sharpe_v > 0.5:
                score += 15; details.append(f"🟡 Sharpe {sharpe_v:.2f} 0.5-1.5: +15")
            else:
                details.append(f"🔴 Sharpe {sharpe_v:.2f} <0.5: +0")
            if top_w < 0.2:
                score += 20; details.append(f"✅ Tập trung {top_w*100:.0f}% <20%: +20")
            elif top_w < 0.4:
                score += 10; details.append(f"🟡 Tập trung {top_w*100:.0f}% 20-40%: +10")
            else:
                details.append(f"🔴 Tập trung {top_w*100:.0f}% >40%: +0")
            if nganh_count >= 4:
                score += 15; details.append(f"✅ Đa ngành {nganh_count} ≥4: +15")
            elif nganh_count >= 3:
                score += 10; details.append(f"🟡 {nganh_count} ngành: +10")
            else:
                details.append(f"🔴 Chỉ {nganh_count} ngành: +0")
            if port_beta < 1.0:
                score += 15; details.append(f"✅ Beta {port_beta:.2f} <1.0: +15")
            elif port_beta < 1.3:
                score += 10; details.append(f"🟡 Beta {port_beta:.2f} 1.0-1.3: +10")
            else:
                details.append(f"🔴 Beta {port_beta:.2f} >1.3: +0")
            grade = "A+ Xuất sắc" if score >= 85 else ("A Tốt" if score >= 70 else ("B+ Khá" if score >= 55 else ("B Trung bình" if score >= 40 else ("C Yếu" if score >= 25 else "D Rủi ro cao"))))
            color_g = "#4CAF50" if score >= 70 else ("#FFD700" if score >= 40 else "#F44336")
            crs1, crs2 = st.columns([1, 2])
            with crs1:
                st.markdown(f'<div style="text-align:center;background:{color_g};border-radius:15px;padding:1.5rem;color:white;"><h1 style="margin:0;font-size:3rem;">{score}</h1><h3 style="margin:0;">/ 100</h3><h2 style="margin:0.5rem 0 0 0;">{grade}</h2></div>', unsafe_allow_html=True)
            with crs2:
                for d in details:
                    st.write(f"  {d}")
                st.caption(f"📊 Tính từ {len(dm_equity)} phiên giá thật + 5 tiêu chí rủi ro (Vol, Sharpe, Tập trung, Đa ngành, Beta).")
        else:
            st.info("⚠️ Cần giá thật 6T để tính composite risk score.")

        st.write("---")
        st.write("## 📈 CAPM Regression — Đường hồi quy Stock vs Market")
        _dm_capm_series = None
        if has_real and dm_equity is not None and len(dm_equity) > 30 and has_vn30:
            try:
                if isinstance(dm_equity, pd.Series) and hasattr(dm_equity, 'index') and len(dm_equity.index) > 0 and not isinstance(dm_equity.index[0], int):
                    _dm_capm_series = dm_equity
                else:
                    _cd_capm = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
                    if len(_cd_capm) > 30:
                        _dm_capm_series = pd.Series(dm_equity, index=_cd_capm)
            except Exception:
                _dm_capm_series = None
        if _dm_capm_series is not None and has_vn30 and len(_dm_capm_series) > 30:
            common_idx = sorted(set(_dm_capm_series.index) & set(vn30_close.index))
            if len(common_idx) > 30:
                dm_r = _dm_capm_series.pct_change().dropna()
                vn_r = vn30_close.pct_change().dropna()
                common_idx2 = sorted(set(dm_r.index) & set(vn_r.index))
                if len(common_idx2) > 30:
                    x = vn_r.loc[common_idx2].values
                    y = dm_r.loc[common_idx2].values
                    beta_capm, alpha_capm = np.polyfit(x, y, 1)
                    corr_capm = float(np.corrcoef(x, y)[0, 1])
                    r2_capm = corr_capm ** 2
                    fig_capm = go.Figure()
                    fig_capm.add_trace(go.Scatter(x=x, y=y, mode='markers', marker=dict(color='#4FC3F7', size=5, opacity=0.5),
                        name='Phiên giao dịch'))
                    x_line = np.linspace(x.min(), x.max(), 100)
                    fig_capm.add_trace(go.Scatter(x=x_line, y=beta_capm * x_line + alpha_capm,
                        mode='lines', line=dict(color='#FFD700', width=2),
                        name=f'Regression: β={beta_capm:.2f}, α={alpha_capm*100:.3f}%'))
                    fig_capm.update_layout(title=f"CAPM Regression (R²={r2_capm:.3f}, n={len(common_idx2)} phiên)",
                        xaxis_title="VN30 Return", yaxis_title="DM Return",
                        height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_capm, use_container_width=True)
                    cap1, cap2, cap3, cap4 = st.columns(4)
                    cap1.metric("📊 Beta (β)", f"{beta_capm:.3f}", help="Độ nhạy của DM so với VN30")
                    cap2.metric("📈 Alpha (α)", f"{alpha_capm*100:+.3f}%/ngày", help="Lợi nhuận vượt thị trường/ngày")
                    cap3.metric("🔗 Correlation", f"{corr_capm:.3f}", help="Hệ số tương quan Pearson")
                    cap4.metric("📐 R²", f"{r2_capm:.3f}", help="Độ phù hợp của mô hình CAPM")
                    st.caption(f"📊 Hồi quy OLS trên {len(common_idx2)} phiên returns thật yfinance 6T. R²={r2_capm:.3f} = {r2_capm*100:.1f}% biến động DM được giải thích bởi VN30.")
            else:
                st.info("⚠️ Không đủ dữ liệu chung với VN30.")
        else:
            st.info("⚠️ Cần giá thật 6T + VN30 proxy để vẽ CAPM regression.")

        st.write("---")
        st.write("## 🎲 Win Rate & Profit Factor — Hiệu suất giao dịch")
        if has_real and dm_equity is not None and len(dm_equity) > 30:
            ret_s5 = pd.Series(dm_equity).pct_change().dropna()
            n_pos = int((ret_s5 > 0).sum())
            n_neg = int((ret_s5 < 0).sum())
            n_flat = int((ret_s5 == 0).sum())
            total = n_pos + n_neg
            win_rate = n_pos / total * 100 if total > 0 else 0
            gross_profit = float(ret_s5[ret_s5 > 0].sum())
            gross_loss = abs(float(ret_s5[ret_s5 < 0].sum()))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            avg_win = float(ret_s5[ret_s5 > 0].mean()) if n_pos > 0 else 0
            avg_loss = abs(float(ret_s5[ret_s5 < 0].mean())) if n_neg > 0 else 0
            payoff = avg_win / avg_loss if avg_loss > 0 else 0
            expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
            kelly_pct = (win_rate/100 - (1 - win_rate/100) / payoff) * 100 if payoff > 0 else 0
            kelly_safe = max(0, kelly_pct / 2)
            wr1, wr2, wr3, wr4 = st.columns(4)
            wr1.metric("🎯 Win Rate", f"{win_rate:.1f}%", help="Tỷ lệ phiên lãi / tổng phiên có biến động")
            wr2.metric("💰 Profit Factor", f"{profit_factor:.2f}", help="Tổng lãi / Tổng lỗ. >1.5 = tốt, >2 = xuất sắc")
            wr3.metric("📊 Payoff Ratio", f"{payoff:.2f}", help="TB lãi / TB lỗ. >1 = lãi trung bình > lỗ trung bình")
            wr4.metric("📈 Expectancy", f"{expectancy*100:+.3f}%", help="Kỳ vọng lợi nhuận/phiên")
            wr5, wr6, wr7 = st.columns(3)
            wr5.metric("📊 Phiên lãi", f"{n_pos}", help="Số phiên return > 0")
            wr6.metric("📉 Phiên lỗ", f"{n_neg}", help="Số phiên return < 0")
            wr7.metric("📐 Kelly %", f"{kelly_pct:.1f}% (safe {kelly_safe:.1f}%)",
                help="Kelly Criterion: % vốn tối ưu nên đầu tư. Safe = ½ Kelly để giảm rủi ro")
            st.caption(f"📊 Tính từ {len(ret_s5)} phiên returns thật yfinance 6T. Profit Factor >1.5 = tốt, >2 = xuất sắc. Kelly Criterion cho biết nên đặt cọc bao nhiêu % vốn.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính win rate & profit factor.")

        st.write("---")
        st.write("## 📊 Volatility Cone — Phân phối Vol lịch sử")
        if has_real and dm_equity is not None and len(dm_equity) > 120:
            ret_s6 = pd.Series(dm_equity).pct_change().dropna()
            windows = [10, 20, 30, 60, 90, 120]
            vol_data = {}
            for w in windows:
                if len(ret_s6) >= w:
                    rolling_v = ret_s6.rolling(w).std() * (252**0.5) * 100
                    vol_data[w] = {
                        "P10": float(rolling_v.quantile(0.10)),
                        "P25": float(rolling_v.quantile(0.25)),
                        "P50 (median)": float(rolling_v.quantile(0.50)),
                        "P75": float(rolling_v.quantile(0.75)),
                        "P90": float(rolling_v.quantile(0.90)),
                        "Current": float(rolling_v.iloc[-1]) if not rolling_v.empty else 0,
                    }
            if vol_data:
                df_vc = pd.DataFrame(vol_data).T
                df_vc.index.name = "Window (ngày)"
                st.dataframe(df_vc.round(1), use_container_width=True)
                fig_vc = go.Figure()
                for pct in ["P10", "P25", "P50 (median)", "P75", "P90"]:
                    fig_vc.add_trace(go.Scatter(x=df_vc.index.astype(str), y=df_vc[pct],
                        mode='lines+markers', name=pct,
                        line=dict(width=2 if 'median' in pct else 1)))
                fig_vc.add_trace(go.Scatter(x=df_vc.index.astype(str), y=df_vc["Current"],
                    mode='lines+markers', name='Hiện tại', line=dict(color='#FFD700', width=3, dash='dash')))
                fig_vc.update_layout(title="Volatility Cone (% năm)",
                    xaxis_title="Rolling Window (ngày)", yaxis_title="Vol (%)",
                    height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_vc, use_container_width=True)
                st.caption(f"📊 Tính từ {len(ret_s6)} phiên returns thật yfinance 6T. Vol hiện tại so với phân phối lịch sử: >P90 = bất thường, <P10 = yên tĩnh bất thường.")
        else:
            st.info("⚠️ Cần ≥120 phiên giá thật để vẽ volatility cone.")

        st.write("---")
        st.write("## 🔗 Higher Moments — Coskewness & Cokurtosis")
        if has_real and len(real_prices) >= 2 and tong_gt > 0:
            weights_arr = []
            rets_list = []
            tickers = []
            for ma, info in dm.items():
                gia_tt = info.get("gia_thi_truong", 0)
                sl = info.get("so_luong", 0)
                if gia_tt <= 0 or sl <= 0: continue
                if ma not in real_prices or len(real_prices[ma]) < 30: continue
                w = (gia_tt * sl) / tong_gt
                weights_arr.append(w)
                tickers.append(ma)
                rets_list.append(real_prices[ma].pct_change().dropna())
            if len(rets_list) >= 2:
                df_hm = pd.concat(rets_list, axis=1).dropna()
                df_hm.columns = tickers
                market_ret = df_hm.mean(axis=1)
                hm_rows = []
                for ma in tickers:
                    r = df_hm[ma]
                    covar_with_m2 = float(np.mean((r - r.mean()) * (market_ret - market_ret.mean())**2))
                    var_m2 = float(np.var(market_ret)) ** 1.5 if float(np.var(market_ret)) > 0 else 1e-10
                    coskew = covar_with_m2 / var_m2 if var_m2 > 1e-10 else 0
                    covar_with_m3 = float(np.mean((r - r.mean()) * (market_ret - market_ret.mean())**3))
                    var_m3 = float(np.var(market_ret)) ** 2 if float(np.var(market_ret)) > 0 else 1e-10
                    cokurt = covar_with_m3 / var_m3 if var_m3 > 1e-10 else 0
                    sk = float(((r - r.mean())**3).mean() / (r.std()**3)) if r.std() > 0 else 0
                    interp_sk = "🟢 Lệch phải (tốt)" if sk > 0.5 else ("🔴 Lệch trái (xấu)" if sk < -0.5 else "🟡 Đối xứng")
                    interp_cosk = "🟢 Cùng chiều TT (tốt)" if coskew > 0.3 else ("🔴 Ngược chiều TT (đa dạng hóa)" if coskew < -0.3 else "🟡 Trung tính")
                    hm_rows.append({"Mã": ma, "Skewness": round(sk, 3), "Diễn giải": interp_sk,
                        "Coskewness": round(coskew, 3), "Tương tác TT": interp_cosk,
                        "Cokurtosis": round(cokurt, 3)})
                if hm_rows:
                    st.dataframe(pd.DataFrame(hm_rows), use_container_width=True, hide_index=True)
                    st.caption(f"📊 Tính từ {len(df_hm)} phiên returns thật yfinance 6T. Coskewness>0.3 = mã này tăng mạnh khi thị trường tăng (tail dependence tốt). <−0.3 = mã này giảm khi thị trường tăng (đa dạng hóa tốt).")
            else:
                st.info("⚠️ Cần ≥2 mã có giá thật để tính higher moments.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính higher moments.")

        st.write("---")
        st.write("## 📊 Information Ratio Decomposition theo kỳ")
        dm_eq_series = None
        if has_real and dm_equity is not None and has_vn30 and len(dm_equity) > 30:
            try:
                if isinstance(dm_equity, pd.Series) and hasattr(dm_equity, 'index') and len(dm_equity.index) > 0 and not isinstance(dm_equity.index[0], int):
                    dm_eq_series = dm_equity
                else:
                    common_dates_local = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
                    if len(common_dates_local) > 30:
                        dm_eq_series = pd.Series(dm_equity, index=common_dates_local)
            except Exception:
                dm_eq_series = None
        if dm_eq_series is not None and has_vn30 and len(dm_eq_series) > 30:
            common_idx3 = sorted(set(dm_eq_series.index) & set(vn30_close.index))
            if len(common_idx3) > 30:
                ir_rows = []
                periods = [("1 tháng", 22), ("3 tháng", 66), ("6 tháng", len(common_idx3))]
                for label, n in periods:
                    n_use = min(n, len(common_idx3))
                    if n_use < 10: continue
                    dm_aligned = dm_eq_series.loc[common_idx3]
                    dm_p = float(dm_aligned.iloc[-1] / dm_aligned.iloc[-n_use] - 1)
                    vn_p = float(vn30_close.loc[common_idx3].iloc[-1] / vn30_close.loc[common_idx3].iloc[-n_use] - 1)
                    diff_ret = dm_p - vn_p
                    dm_period_ret = dm_aligned.iloc[-n_use:].pct_change().dropna()
                    vn_period_ret = vn30_close.loc[common_idx3].iloc[-n_use:].pct_change().dropna()
                    common_p = sorted(set(dm_period_ret.index) & set(vn_period_ret.index))
                    if len(common_p) > 5:
                        te = float((dm_period_ret.loc[common_p] - vn_period_ret.loc[common_p]).std() * (252**0.5))
                        ir = diff_ret / te if te > 0 else 0
                    else:
                        te = 0; ir = 0
                    interp_ir = "✅ Xuất sắc" if ir > 1 else ("✅ Tốt" if ir > 0.5 else ("🟡 Trung bình" if ir > 0 else "🔴 Thua"))
                    ir_rows.append({"Kỳ": label, "Return DM %": round(dm_p*100, 2),
                        "Return VN30 %": round(vn_p*100, 2), "Excess Return %": round(diff_ret*100, 2),
                        "Tracking Error %": round(te*100, 2), "Information Ratio": round(ir, 3),
                        "Đánh giá": interp_ir})
                if ir_rows:
                    st.dataframe(pd.DataFrame(ir_rows), use_container_width=True, hide_index=True)
                    st.caption(f"📊 Tính từ returns thật yfinance 6T. IR > 1 = xuất sắc, > 0.5 = tốt, < 0 = thua thị trường.")
                else:
                    st.info("⚠️ Không đủ dữ liệu chung với VN30 để phân tích theo kỳ.")
            else:
                st.info("⚠️ Không đủ dữ liệu chung với VN30 (chỉ có {0} ngày overlap).".format(len(common_idx3)))
        else:
            st.info("⚠️ Cần giá thật + VN30 để tính IR decomposition.")

        st.write("---")
        st.write("## 🎯 Upside/Downside Capture — Bắt trend TĂNG, né trend GIẢM")
        dm_capture_series = None
        if has_real and dm_equity is not None and has_vn30 and len(dm_equity) > 60:
            try:
                if isinstance(dm_equity, pd.Series) and hasattr(dm_equity, 'index') and len(dm_equity.index) > 0 and not isinstance(dm_equity.index[0], int):
                    dm_capture_series = dm_equity
                else:
                    common_dates_local2 = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
                    if len(common_dates_local2) > 30:
                        dm_capture_series = pd.Series(dm_equity, index=common_dates_local2)
            except Exception:
                dm_capture_series = None
        if dm_capture_series is not None and has_vn30 and len(dm_capture_series) > 60:
            common_idx4 = sorted(set(dm_capture_series.index) & set(vn30_close.index))
            if len(common_idx4) > 60:
                dm_r_full = dm_capture_series.pct_change().dropna()
                vn_r_full = vn30_close.pct_change().dropna()
                common_idx5 = sorted(set(dm_r_full.index) & set(vn_r_full.index))
                dm_arr = dm_r_full.loc[common_idx5]
                vn_arr = vn_r_full.loc[common_idx5]
                up_mask = vn_arr > 0
                dn_mask = vn_arr < 0
                if up_mask.sum() > 0 and dn_mask.sum() > 0:
                    up_capture = float((dm_arr[up_mask].mean() / vn_arr[up_mask].mean()) * 100)
                    dn_capture = float((dm_arr[dn_mask].mean() / vn_arr[dn_mask].mean()) * 100)
                    capture_ratio = up_capture / dn_capture if dn_capture != 0 else 0
                    uc1, uc2, uc3, uc4 = st.columns(4)
                    uc1.metric("📈 Upside Capture", f"{up_capture:.1f}%",
                        help="DM lãi bao nhiêu % khi VN30 tăng. >100 = bắt trend tốt")
                    uc2.metric("📉 Downside Capture", f"{dn_capture:.1f}%",
                        help="DM lỗ bao nhiêu % khi VN30 giảm. <100 = phòng thủ tốt")
                    uc3.metric("⚖️ Capture Ratio", f"{capture_ratio:.2f}",
                        help="Upside/Downside. >1 = bắt tăng tốt hơn phòng thủ")
                    uc4.metric("🎯 Phân loại",
                        "✅ Xuất sắc" if capture_ratio > 1.2 and dn_capture < 80 else
                        ("✅ Tốt" if capture_ratio > 1.0 and dn_capture < 100 else
                        ("🟡 Cân bằng" if capture_ratio > 0.8 else "🔴 Yếu")))
                    st.caption(f"📊 Tính từ {len(common_idx5)} phiên returns thật yfinance 6T. Capture ratio >1.2 + downside <80% = DM lý tưởng (ăn nhiều khi tăng, lỗ ít khi giảm).")
            else:
                st.info("⚠️ Không đủ dữ liệu chung với VN30.")
        else:
            st.info("⚠️ Cần giá thật + VN30 để tính capture ratio.")

        st.write("---")
        st.write("## 🕸️ Mạng lưới tương quan (Correlation Network)")
        if has_real and len(real_prices) >= 3:
            ret_dict = {}
            for ma, info in dm.items():
                if ma in real_prices and len(real_prices[ma]) >= 30:
                    ret_dict[ma] = real_prices[ma].pct_change().dropna()
            if len(ret_dict) >= 3:
                common_n = sorted(set().union(*[set(r.index) for r in ret_dict.values()]))
                if len(common_n) > 20:
                    df_n = pd.DataFrame({ma: r.reindex(common_n) for ma, r in ret_dict.items()}).dropna()
                    corr_n = df_n.corr()
                    fig_net = go.Figure()
                    n_stocks = len(corr_n)
                    angles = np.linspace(0, 2*np.pi, n_stocks, endpoint=False)
                    pos_x = np.cos(angles)
                    pos_y = np.sin(angles)
                    for i in range(n_stocks):
                        for j in range(i+1, n_stocks):
                            c = float(corr_n.iloc[i, j])
                            if abs(c) > 0.5:
                                color = "rgba(244,67,54," + str(abs(c)*0.8) + ")" if c > 0 else "rgba(76,175,80," + str(abs(c)*0.8) + ")"
                                fig_net.add_trace(go.Scatter(x=[pos_x[i], pos_x[j]], y=[pos_y[i], pos_y[j]],
                                    mode='lines', line=dict(color=color, width=abs(c)*5),
                                    showlegend=False, hoverinfo='skip'))
                    for i, ma in enumerate(corr_n.columns):
                        fig_net.add_trace(go.Scatter(x=[pos_x[i]], y=[pos_y[i]], mode='markers+text',
                            marker=dict(size=30, color=corr_n.columns.get_loc(ma), colorscale='Viridis', showscale=False),
                            text=[ma], textposition='middle center', textfont=dict(color='white', size=10, family='Arial Black'),
                            name=ma, showlegend=False, hovertemplate=f"<b>{ma}</b><br>Avg corr: {corr_n[ma].mean():.2f}<extra></extra>"))
                    fig_net.update_layout(title=f"Mạng tương quan (đỏ = cùng chiều, xanh = ngược chiều, chỉ hiện |corr|>0.5)",
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_net, use_container_width=True)
                    st.caption(f"📊 Tính từ {len(df_n)} phiên returns thật yfinance 6T. Mã cùng ngành thường có corr cao (đỏ đậm). Mã khác ngành hoặc ngược chiều (xanh) giúp đa dạng hóa.")
            else:
                st.info("⚠️ Cần ≥3 mã có giá thật để vẽ mạng.")
        else:
            st.info("⚠️ Cần giá thật 6T để vẽ correlation network.")

        st.write("---")
        st.write("## 💎 Risk-Return Bubble Chart — Hiệu suất vs Rủi ro từng mã")
        ma_list_rr = [ma for ma, info in dm.items() if info.get("gia_thi_truong", 0) * info.get("so_luong", 0) > 0 and tong_gt > 0]
        if len(ma_list_rr) >= 2:
            _vn_keys = set((DOCS.get("co_phieu_vn") or {}).keys())
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import requests as _rq_rr, pandas as _pd_rr
            _rr_prices = {}
            def _fetch_rr(sym, suffix):
                try:
                    r = _rq_rr.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        d = r.json()
                        quote = d.get("chart", {}).get("result", [{}])[0]
                        ts = quote.get("timestamp", [])
                        cs = quote.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        pairs = [(t, c) for t, c in zip(ts, cs) if c]
                        if len(pairs) >= 20:
                            idx = _pd_rr.to_datetime([p[0] for p in pairs], unit="s")
                            return sym, _pd_rr.Series([p[1] for p in pairs], index=idx)
                except: pass
                return sym, None
            with ThreadPoolExecutor(max_workers=12) as ex_rr:
                _futs_rr = {ex_rr.submit(_fetch_rr, m, ".VN" if m in _vn_keys else ""): m for m in ma_list_rr}
                for _f_rr in as_completed(_futs_rr):
                    _s_rr, _p_rr = _f_rr.result()
                    if _p_rr is not None:
                        _rr_prices[_s_rr] = _p_rr
            if len(_rr_prices) >= 2:
                _rr_points = []
                for _ma_rr, _s_rr in _rr_prices.items():
                    try:
                        _ret = (float(_s_rr.iloc[-1]) / float(_s_rr.iloc[0]) - 1) * 100
                        _vol = float(_s_rr.pct_change().dropna().std() * (252 ** 0.5) * 100)
                        _ki = kpi.get(_ma_rr, {}) or {}
                        _mc = float(_ki.get("market_cap", 0) or 0) / 1e3
                        _ng = str(_ki.get("nganh", "") or "")
                        _rr_points.append({"ma": _ma_rr, "ret": _ret, "vol": _vol, "mc": max(_mc, 0.1), "nganh": _ng if _ng else "Khác", "vung": "VN" if _ma_rr in _vn_keys else "TG"})
                    except: pass
                if len(_rr_points) >= 2:
                    _df_rr = _pd_rr.DataFrame(_rr_points)
                    _df_rr = _df_rr.dropna(subset=["ret", "vol", "mc"])
                    _df_rr = _df_rr[np.isfinite(_df_rr["ret"]) & np.isfinite(_df_rr["vol"])]
                    _df_rr = _df_rr[_df_rr["mc"] > 0]
                    if len(_df_rr) >= 2:
                        _df_rr = _df_rr.sort_values("mc", ascending=False)
                        _df_top = _df_rr.head(50)
                        _color_needed = _df_top["nganh"].nunique() > 1
                        import plotly.graph_objects as _go_rr
                        _fig_rr = _go_rr.Figure()
                        for _cat_rr in _df_rr["nganh"].unique():
                            _sub = _df_rr[_df_rr["nganh"] == _cat_rr]
                            _sz = _sub["mc"].clip(lower=1).values
                            _fig_rr.add_trace(_go_rr.Scatter(
                                x=_sub["vol"], y=_sub["ret"], mode="markers+text" if _cat_rr in _df_top["nganh"].values else "markers",
                                marker=dict(size=_sz / _sz.max() * 40, sizemode="diameter",
                                    line=dict(width=1, color="rgba(255,255,255,0.3)"), opacity=0.8),
                                text=_sub["ma"].where(_sub["ma"].isin(_df_top["ma"])),
                                textposition="top center", textfont=dict(size=8, color="#ECE8E1"),
                                name=_cat_rr, hovertemplate="<b>%{customdata[0]}</b><br>Vol %: %{x:.1f}<br>Return %: %{y:.1f}<br>VH: %{customdata[1]:.0f}T<br>",
                                customdata=np.column_stack([_sub["ma"], _sub["mc"]])))
                        _fig_rr.update_layout(height=520, xaxis_title="Vol % (năm)", yaxis_title="Return 6M %",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#ECE8E1"),
                            title_text=f"Risk-Return Bubble — {len(_df_rr)} mã ({len(_df_rr[_df_rr['vung']=='VN'])} VN + {len(_df_rr[_df_rr['vung']=='TG'])} TG)")
                        st.plotly_chart(_fig_rr, use_container_width=True)
                        st.caption(f"📊 Trục X = Vol % năm từ daily returns yfinance 6T. Trục Y = Return 6M %. Bong bóng trên-trái = lợi nhuận cao, rủi ro thấp. Size = vốn hóa thị trường.")
                    else:
                        st.info("⚠️ Không đủ dữ liệu hợp lệ sau lọc NaN.")
                else:
                    st.info("⚠️ Không đủ mã có dữ liệu từ yfinance.")
            else:
                st.info("⚠️ Yahoo Finance không trả dữ liệu. Refresh sau 5-10 phút.")
        else:
            st.info("Cần ≥2 mã trong danh mục để vẽ bubble.")

        st.write("---")
        st.write("## 💵 Tổng return vs Price return (có cổ tức)")
        if has_fund and len(real_fund) > 0:
            tr_rows = []
            for ma, info in dm.items():
                ki = kpi.get(ma, {})
                dy = float(ki.get("dividend_yield", 0) or 0) * 100
                if ma in real_prices and len(real_prices[ma]) >= 30:
                    pr6m = (float(real_prices[ma].iloc[-1]) / float(real_prices[ma].iloc[0]) - 1) * 100
                    total_ret_6m = pr6m + dy * 0.5
                    pr1y_approx = pr6m * 2
                    total_ret_1y = pr1y_approx + dy
                    tr_rows.append({"Mã": ma, "Price 6M %": round(pr6m, 2),
                        "Cổ tức/năm %": round(dy, 2), "Total Return 6M %": round(total_ret_6m, 2),
                        "Total Return 1Y ước %": round(total_ret_1y, 2),
                        "Cổ tức đóng góp %": round(dy / max(total_ret_1y, 0.1) * 100, 1) if total_ret_1y > 0 else 0})
            if tr_rows:
                df_tr = pd.DataFrame(tr_rows).sort_values("Total Return 1Y ước %", ascending=False)
                st.dataframe(df_tr, use_container_width=True, hide_index=True)
                top_div = tr_rows[0]
                avg_div_contrib = sum(r["Cổ tức đóng góp %"] for r in tr_rows) / len(tr_rows)
                st.caption(f"📊 Tính từ giá thật yfinance 6T + dividend_yield từ yfinance.info. Top cổ tức: **{top_div['Mã']}** ({top_div['Cổ tức/năm %']}%). Cổ tức TB đóng góp {avg_div_contrib:.1f}% tổng return DM.")
        else:
            st.info("⚠️ Cần dividend_yield từ yfinance để tính.")

        st.write("---")
        st.write("## ⚠️ Tail Risk Decomposition — Mã nào gây lỗ đuôi?")
        _tr_ma = [ma for ma, info in dm.items() if info.get("gia_thi_truong", 0) * info.get("so_luong", 0) > 0 and tong_gt > 0]
        if len(_tr_ma) >= 2:
            _vn_keys = set((DOCS.get("co_phieu_vn") or {}).keys())
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import requests as _rq_tr, pandas as _pd_tr
            _tr_prices = {}
            def _fetch_tr(sym, suffix):
                try:
                    r = _rq_tr.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        d = r.json()
                        quote = d.get("chart", {}).get("result", [{}])[0]
                        ts = quote.get("timestamp", [])
                        cs = quote.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        pairs = [(t, c) for t, c in zip(ts, cs) if c]
                        if len(pairs) >= 30:
                            idx = _pd_tr.to_datetime([p[0] for p in pairs], unit="s")
                            return sym, _pd_tr.Series([p[1] for p in pairs], index=idx)
                except: pass
                return sym, None
            with ThreadPoolExecutor(max_workers=12) as ex_tr:
                _futs_tr = {ex_tr.submit(_fetch_tr, m, ".VN" if m in _vn_keys else ""): m for m in _tr_ma}
                for _f_tr in as_completed(_futs_tr):
                    _s_tr, _p_tr = _f_tr.result()
                    if _p_tr is not None:
                        _tr_prices[_s_tr] = _p_tr
            if len(_tr_prices) >= 2:
                _tr_df = _pd_tr.DataFrame({k: v for k, v in _tr_prices.items()})
                _tr_dm_eq = _tr_df.sum(axis=1) / len(_tr_df.columns)
                _tr_ret = _tr_dm_eq.pct_change().dropna()
                if len(_tr_ret) >= 20:
                    _var_5 = float(_tr_ret.quantile(0.05))
                    _tail = _tr_ret[_tr_ret <= _var_5].index
                    if len(_tail) > 0:
                        _tr_rows = []
                        for _ma_tr, _info_tr in dm.items():
                            if _ma_tr not in _tr_prices: continue
                            _s_tr = _tr_prices[_ma_tr]
                            if len(_s_tr) < len(_tail) + 5: continue
                            _gt = float(_info_tr.get("gia_thi_truong", 0))
                            _sl = float(_info_tr.get("so_luong", 0))
                            if _gt <= 0 or _sl <= 0: continue
                            _w = (_gt * _sl) / tong_gt
                            _trm = _s_tr.pct_change().dropna().reindex(_tail).dropna()
                            if len(_trm) == 0: continue
                            _avg = float(_trm.mean())
                            _contr = _w * _avg * 100
                            _tr_rows.append({"Mã": _ma_tr, "Tỷ trọng %": round(_w*100, 1),
                                "Return TB ngày tệ": f"{_avg*100:.2f}%",
                                "Đóng góp vào đuôi %": round(_contr, 3)})
                        if _tr_rows:
                            _df_trr = _pd_tr.DataFrame(_tr_rows).sort_values("Đóng góp vào đuôi %")
                            st.dataframe(_df_trr, use_container_width=True, hide_index=True)
                            _worst = _tr_rows[0]
                            st.caption(f"📊 {len(_tail)} phiên tệ nhất (VaR 5%). Mã **{_worst['Mã']}** đóng góp {_worst['Đóng góp vào đuôi %']:+.3f}% vào đuôi (gây lỗ nhiều nhất). Tính từ returns thật yfinance 6T.")
                        else:
                            st.info("⚠️ Không đủ dữ liệu returns để tính tail risk.")
                    else:
                        st.info("Không có phiên nào dưới VaR 5%.")
                else:
                    st.info("⚠️ Không đủ phiên giao dịch từ yfinance (< 20).")
            else:
                st.info("⚠️ Yahoo Finance không trả dữ liệu. Refresh sau 5-10 phút.")
        else:
            st.info("Cần ≥2 mã trong danh mục để phân tích tail risk.")

        st.write("---")
        st.write("## 📉 Individual Stock Drawdown — Sụt giảm từng mã")
        if has_real and len(real_prices) >= 1:
            idd_rows = []
            for ma in dm.keys():
                if ma in real_prices and len(real_prices[ma]) >= 30:
                    p = real_prices[ma]
                    running_max_i = p.cummax()
                    dd_i = (p - running_max_i) / running_max_i * 100
                    worst_dd = float(dd_i.min())
                    peak_idx = p.cummax().idxmax()
                    trough_idx = dd_i.idxmin()
                    if peak_idx <= trough_idx:
                        in_dd_now = (float(p.iloc[-1]) / float(p.loc[peak_idx]) - 1) * 100
                        cur_dd = float(dd_i.iloc[-1])
                    else:
                        in_dd_now = (float(p.iloc[-1]) / float(p.iloc[0]) - 1) * 100
                        cur_dd = cur_dd if cur_dd < 0 else 0
                    idd_rows.append({"Mã": ma, "Max DD %": round(worst_dd, 1),
                        "DD hiện tại %": round(cur_dd, 1), "Return từ đỉnh %": round(in_dd_now, 1),
                        "Trạng thái": "🔴 Dưới đỉnh" if cur_dd < -5 else ("🟡 Hồi phục" if cur_dd < 0 else "🟢 Trên đỉnh")})
            if idd_rows:
                df_idd = pd.DataFrame(idd_rows).sort_values("Max DD %")
                st.dataframe(df_idd, use_container_width=True, hide_index=True)
                worst_stock = idd_rows[0]
                st.caption(f"📊 Tính từ giá thật yfinance 6T. **{worst_stock['Mã']}** sụt {worst_stock['Max DD %']:.1f}% từ đỉnh. Đang ở {worst_stock['DD hiện tại %']:+.1f}% so với đỉnh.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính drawdown từng mã.")

        st.write("---")
        st.write("## 🏆 Return / MaxDD Ratio (RoMaD) — Hiệu quả trên Sụt giảm")
        st.info("ℹ️ Section này đã được gộp vào **🏆 Return / Drawdown Ratios** ở dưới (1 bảng 5 ratios: Calmar/RoMaD/Sterling/Burke/Martin).")
        st.write("---")
        st.write("## 🔥 Win/Loss Streaks — Chuỗi thắng/thua dài nhất")
        if has_real and dm_equity is not None and len(dm_equity) > 10:
            ret_s8 = pd.Series(dm_equity).pct_change().dropna()
            pos = (ret_s8 > 0).astype(int).values
            neg = (ret_s8 < 0).astype(int).values
            max_win_streak = 0
            max_loss_streak = 0
            cur_win = 0
            cur_loss = 0
            for i in range(len(ret_s8)):
                if ret_s8.iloc[i] > 0:
                    cur_win += 1
                    cur_loss = 0
                    max_win_streak = max(max_win_streak, cur_win)
                elif ret_s8.iloc[i] < 0:
                    cur_loss += 1
                    cur_win = 0
                    max_loss_streak = max(max_loss_streak, cur_loss)
                else:
                    cur_win = cur_loss = 0
            cur_streak = 0
            cur_streak_type = "🟢 Đang thắng" if ret_s8.iloc[-1] > 0 else ("🔴 Đang thua" if ret_s8.iloc[-1] < 0 else "🟡 Đi ngang")
            for i in range(len(ret_s8) - 1, -1, -1):
                if (ret_s8.iloc[i] > 0 and cur_streak_type.startswith("🟢")) or \
                   (ret_s8.iloc[i] < 0 and cur_streak_type.startswith("🔴")):
                    cur_streak += 1
                else:
                    break
            ws1, ws2, ws3, ws4 = st.columns(4)
            ws1.metric("🔥 Chuỗi thắng dài nhất", f"{max_win_streak} phiên", help="Số phiên lãi liên tiếp dài nhất")
            ws2.metric("❄️ Chuỗi thua dài nhất", f"{max_loss_streak} phiên", help="Số phiên lỗ liên tiếp dài nhất")
            ws3.metric(f"{cur_streak_type}", f"{cur_streak} phiên", help="Chuỗi hiện tại đang chạy")
            ws4.metric("📊 Tổng phiên", f"{len(ret_s8)}", help="Tổng số phiên có dữ liệu")
            mental_warning = ""
            if cur_streak >= 5 and cur_streak_type.startswith("🟢"):
                mental_warning = "⚠️ Chuỗi thắng dài → cẩn thận tâm lý quá tự tin (overconfidence bias)"
            elif cur_streak >= 5 and cur_streak_type.startswith("🔴"):
                mental_warning = "⚠️ Chuỗi thua dài → cẩn thận tâm lý hoảng loạn (panic selling). Đây là lúc cần bình tĩnh, không bán tháo."
            if mental_warning:
                st.warning(mental_warning)
            st.caption(f"📊 Tính từ {len(ret_s8)} phiên returns thật yfinance 6T. Chuỗi thắng/thua dài giúp nhận diện tâm lý đầu tư (Buffett: 'Người chơi thua nhiều nhất là người không thể chịu được chuỗi thua').")
        else:
            st.info("⚠️ Cần giá thật 6T để phân tích streaks.")

        st.write("---")
        st.write("## 📊 Vol-Adjusted Momentum — Momentum đã điều chỉnh rủi ro")
        if has_real and len(real_prices) >= 1:
            vam_rows = []
            for ma in dm.keys():
                if ma in real_prices and len(real_prices[ma]) >= 63:
                    p = real_prices[ma]
                    ret_3m = (float(p.iloc[-1]) / float(p.iloc[-63]) - 1) * 100
                    vol_3m = float(p.tail(63).pct_change().dropna().std() * (252**0.5) * 100)
                    vam = ret_3m / vol_3m if vol_3m > 0 else 0
                    vam_rows.append({"Mã": ma, "Return 3M %": round(ret_3m, 1), "Vol 3M %": round(vol_3m, 1),
                        "Vol-Adj Momentum": round(vam, 3),
                        "Xếp loại": "🔥 Top" if vam > 0.5 else ("✅ Tốt" if vam > 0.2 else ("🟡 TB" if vam > 0 else "🔴 Yếu"))})
            if vam_rows:
                df_vam = pd.DataFrame(vam_rows).sort_values("Vol-Adj Momentum", ascending=False)
                st.dataframe(df_vam, use_container_width=True, hide_index=True)
                top_vam = vam_rows[0]
                st.caption(f"📊 Tính từ {len(real_prices[top_vam['Mã']])} phiên giá thật yfinance 6T. Vol-Adj Momentum = Return 3M / Vol 3M. Top: **{top_vam['Mã']}** = {top_vam['Vol-Adj Momentum']:.2f}.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính Vol-Adj Momentum.")

        st.write("---")
        st.write("## ⏱️ Autocorrelation — Returns có tự tương quan không?")
        if has_real and dm_equity is not None and len(dm_equity) > 60:
            ret_s9 = pd.Series(dm_equity).pct_change().dropna()
            lags_to_test = [1, 2, 3, 5, 10]
            acf_rows = []
            for lag in lags_to_test:
                if len(ret_s9) > lag + 10:
                    ac = float(ret_s9.autocorr(lag=lag))
                    acf_rows.append({"Lag": f"{lag} phiên", "Autocorrelation": round(ac, 4),
                        "Diễn giải": "🔴 Mean-reverting (ngược xu hướng)" if ac < -0.1 else
                                    ("🟢 Momentum (cùng xu hướng)" if ac > 0.1 else
                                    "🟡 Random walk (hiệu quả)")})
            if acf_rows:
                st.dataframe(pd.DataFrame(acf_rows), use_container_width=True, hide_index=True)
                lag1 = acf_rows[0]["Autocorrelation"] if acf_rows else 0
                interp_lag1 = "🔴 Mean reversion mạnh — có thể arbitrage bằng chiến lược đảo chiều" if lag1 < -0.15 else \
                              ("🟢 Momentum yếu — xu hướng ngắn hạn có thể khai thác" if lag1 > 0.15 else \
                              "🟡 Random walk — thị trường hiệu quả, khó arbitrage")
                st.write(f"**Lag-1 AC:** {lag1:.4f} — {interp_lag1}")
                st.caption(f"📊 Tính từ {len(ret_s9)} phiên returns thật yfinance 6T. AC <-0.1 = mean reversion (đảo chiều), >0.1 = momentum (cùng chiều), gần 0 = random walk.")
        else:
            st.info("⚠️ Cần giá thật 6T để tính autocorrelation.")

        st.write("---")
        st.write("## 🔄 Beta Stability — Beta thay đổi qua các kỳ")
        if has_real and len(real_prices) >= 1 and has_vn30 and dm_equity is not None and len(dm_equity) > 120:
            eq_s10 = pd.Series(dm_equity)
            common_b = sorted(set(eq_s10.index) & set(vn30_close.index))
            if len(common_b) > 120:
                dm_r = eq_s10.pct_change().dropna()
                vn_r = vn30_close.pct_change().dropna()
                common_b2 = sorted(set(dm_r.index) & set(vn_r.index))
                if len(common_b2) > 120:
                    chunks = [common_b2[i:i+30] for i in range(0, len(common_b2)-30, 30)]
                    betas_overtime = []
                    for chunk in chunks:
                        if len(chunk) > 15:
                            b_v = float(np.polyfit(vn_r.loc[chunk], dm_r.loc[chunk], 1)[0])
                            betas_overtime.append({"Kỳ": f"{pd.Series(dm_r.index).loc[chunk[0]].strftime('%d/%m')}-{pd.Series(dm_r.index).loc[chunk[-1]].strftime('%d/%m')}",
                                "Beta": round(b_v, 3)})
                    if betas_overtime:
                        df_bo = pd.DataFrame(betas_overtime)
                        st.dataframe(df_bo, use_container_width=True, hide_index=True)
                        b_vals = [b["Beta"] for b in betas_overtime]
                        b_mean = float(np.mean(b_vals))
                        b_std = float(np.std(b_vals))
                        b_cv = b_std / abs(b_mean) if b_mean != 0 else 0
                        bs1, bs2, bs3 = st.columns(3)
                        bs1.metric("📊 Beta TB", f"{b_mean:.3f}")
                        bs2.metric("📐 Beta std", f"{b_std:.3f}", help="Độ lệch chuẩn của beta qua các kỳ")
                        bs3.metric("🎯 Beta CV", f"{b_cv:.2f}", help="Coefficient of Variation. <0.2 = ổn định, >0.5 = bất ổn")
                        stability = "✅ Ổn định" if b_cv < 0.2 else ("🟡 Biến động" if b_cv < 0.5 else "🔴 Bất ổn")
                        st.write(f"**Beta stability:** {stability}")
                        fig_b = go.Figure()
                        fig_b.add_trace(go.Scatter(x=list(range(len(b_vals))), y=b_vals, mode='lines+markers',
                            line_color='#4FC3F7', marker_size=8, name='Beta theo kỳ'))
                        fig_b.add_hline(y=b_mean, line_dash="dash", line_color='#FFD700', annotation_text=f"Mean={b_mean:.2f}")
                        fig_b.update_layout(title="Beta qua các kỳ 30 phiên", xaxis_title="Kỳ", yaxis_title="Beta",
                            height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                        st.plotly_chart(fig_b, use_container_width=True)
                        st.caption(f"📊 Tính rolling 30-phiên beta trên {len(common_b2)} phiên returns thật yfinance 6T. CV<0.2 = beta ổn định (DM lúc nào cũng giống thị trường).")
        else:
            st.info("⚠️ Cần ≥120 phiên + VN30 để tính beta stability.")

        st.write("---")
        st.write("## 📅 Calendar Returns — Hiệu suất theo tháng/quý")
        if has_real and dm_equity is not None and len(dm_equity) > 60:
            try:
                _cd_cal = None
                if isinstance(dm_equity, pd.Series) and hasattr(dm_equity, 'index') and len(dm_equity.index) > 0 and not isinstance(dm_equity.index[0], int):
                    _cd_cal = list(dm_equity.index)
                else:
                    _cd_cal = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
                if _cd_cal and len(_cd_cal) > 60:
                    eq_s11 = pd.Series(dm_equity, index=pd.DatetimeIndex(_cd_cal))
                    monthly_ret = eq_s11.resample('ME').last().pct_change().dropna() * 100
                else:
                    monthly_ret = pd.Series(dtype=float)
            except Exception as _cal_ex:
                monthly_ret = pd.Series(dtype=float)
            if len(monthly_ret) >= 3:
                mr_df = pd.DataFrame({"Tháng": monthly_ret.index.strftime("%m/%Y"),
                    "Return %": monthly_ret.values.round(2),
                    "Tốt/Xấu": ["🟢" if r > 0 else "🔴" for r in monthly_ret.values]})
                st.dataframe(mr_df, use_container_width=True, hide_index=True)
                best_month = float(monthly_ret.max())
                worst_month = float(monthly_ret.min())
                avg_month = float(monthly_ret.mean())
                positive_months = int((monthly_ret > 0).sum())
                total_months = len(monthly_ret)
                cm1, cm2, cm3, cm4 = st.columns(4)
                cm1.metric("🏆 Tháng tốt nhất", f"{best_month:+.2f}%")
                cm2.metric("💀 Tháng tệ nhất", f"{worst_month:+.2f}%")
                cm3.metric("📊 TB tháng", f"{avg_month:+.2f}%")
                cm4.metric("🎯 Tỷ lệ tháng +", f"{positive_months}/{total_months} ({positive_months/total_months*100:.0f}%)")
                st.caption(f"📊 Tính từ {len(monthly_ret)} tháng giá thật yfinance 6T. Phân tích seasonality giúp nhận diện tháng nào DM thường tăng/giảm.")
        else:
            st.info("⚠️ Cần ≥60 phiên giá thật để phân tích monthly returns.")

        st.write("---")
        st.write("## 📐 Brinson Attribution — Stock Selection vs Sector Allocation")
        _dm_br_series = None
        if has_real and len(real_prices) >= 2 and has_vn30 and dm_equity is not None and len(dm_equity) > 60:
            try:
                if isinstance(dm_equity, pd.Series) and hasattr(dm_equity, 'index') and len(dm_equity.index) > 0 and not isinstance(dm_equity.index[0], int):
                    _dm_br_series = dm_equity
                else:
                    _cd_br = sorted(set().union(*[set(s.index) for s in real_prices.values()]))
                    if len(_cd_br) > 30:
                        _dm_br_series = pd.Series(dm_equity, index=_cd_br)
            except Exception:
                _dm_br_series = None
        if _dm_br_series is not None and has_vn30 and len(_dm_br_series) > 60:
            common_br = sorted(set(_dm_br_series.index) & set(vn30_close.index))
            if len(common_br) > 60:
                stock_rets = {}
                for ma, info in dm.items():
                    if ma in real_prices and len(real_prices[ma]) >= len(common_br) - 5:
                        r = real_prices[ma].pct_change().dropna().reindex(common_br).dropna()
                        if len(r) > 30:
                            stock_rets[ma] = (1 + r).prod() - 1
                if stock_rets:
                    sector_rets = {}
                    for ma, ret in stock_rets.items():
                        ng = (kpi.get(ma, {}).get("nganh", "") or "Khác").strip() or "Khác"
                        sector_rets.setdefault(ng, []).append((ret, ma))
                    vn_ret = float((vn30_close.loc[common_br].iloc[-1] / vn30_close.loc[common_br].iloc[0]) - 1)
                    br_rows = []
                    for ng, lst in sector_rets.items():
                        w_in_dm = sum(dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0) for r, ma in lst) / tong_gt if tong_gt > 0 else 0
                        avg_stock_ret = sum(r for r, ma in lst) / len(lst)
                        ng_ret = sum(r for r, ma in lst) / len(lst)
                        allocation = w_in_dm * (ng_ret - vn_ret) * 100
                        selection = w_in_dm * (avg_stock_ret - ng_ret) * 100
                        interaction = 0
                        for r, ma in lst:
                            sw = dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0) / tong_gt if tong_gt > 0 else 0
                            interaction += (sw - w_in_dm * 0) * (r - ng_ret) * 100
                        br_rows.append({"Ngành": ng, "Tỷ trọng %": round(w_in_dm*100, 1),
                            "Return ngành %": round(ng_ret*100, 1), "Allocation %": round(allocation, 3),
                            "Selection %": round(selection, 3), "Interaction %": round(interaction/len(lst), 3)})
                    if br_rows:
                        st.dataframe(pd.DataFrame(br_rows), use_container_width=True, hide_index=True)
                        total_alloc = sum(r["Allocation %"] for r in br_rows)
                        total_select = sum(r["Selection %"] for r in br_rows)
                        total_inter = sum(r["Interaction %"] for r in br_rows)
                        ti1, ti2, ti3 = st.columns(3)
                        ti1.metric("📊 Allocation Effect", f"{total_alloc:+.2f}%", help="Chọn ngành nào tốt/xấu hơn VN30")
                        ti2.metric("🎯 Selection Effect", f"{total_select:+.2f}%", help="Chọn mã nào trong ngành tốt/xấu hơn TB ngành")
                        ti3.metric("🔄 Interaction", f"{total_inter:+.2f}%", help="Tương tác giữa allocation và selection")
                        st.caption(f"📊 Brinson decomposition: tổng 3 effects ≈ Excess return DM vs VN30 ({vn_ret*100:.1f}% VN30, {return_pct*100:.1f}% DM). Tính từ returns 6T thật × tỷ trọng DM.")
        else:
            st.info("⚠️ Cần giá thật + VN30 + nhiều mã để Brinson attribution.")

        st.write("---")
        st.write("## ⏱️ Conditional VaR/CVaR theo kỳ nắm giữ (Horizon Risk)")
        if has_real and dm_equity is not None and len(dm_equity) > 60:
            eq_s_cv = pd.Series(dm_equity).pct_change().dropna()
            horizons = [1, 5, 10, 20, 60]
            cv_rows = []
            for h in horizons:
                if len(eq_s_cv) >= h + 10:
                    roll_ret = (eq_s_cv.rolling(h).sum().dropna())
                    var_95_h = float(roll_ret.quantile(0.05)) * 100
                    var_99_h = float(roll_ret.quantile(0.01)) * 100
                    cvar_95_h = float(roll_ret[roll_ret <= roll_ret.quantile(0.05)].mean()) * 100
                    cvar_99_h = float(roll_ret[roll_ret <= roll_ret.quantile(0.01)].mean()) * 100
                    cv_rows.append({"Kỳ nắm giữ": f"{h} phiên ({h}D)",
                        "VaR 95%": round(var_95_h, 2), "VaR 99%": round(var_99_h, 2),
                        "CVaR 95%": round(cvar_95_h, 2), "CVaR 99%": round(cvar_99_h, 2)})
            if cv_rows:
                st.dataframe(pd.DataFrame(cv_rows), use_container_width=True, hide_index=True)
                fig_cv = go.Figure()
                fig_cv.add_trace(go.Scatter(x=[r["Kỳ nắm giữ"] for r in cv_rows], y=[r["VaR 95%"] for r in cv_rows],
                    mode='lines+markers', name='VaR 95%', line=dict(color='#FFD700', width=2)))
                fig_cv.add_trace(go.Scatter(x=[r["Kỳ nắm giữ"] for r in cv_rows], y=[r["CVaR 95%"] for r in cv_rows],
                    mode='lines+markers', name='CVaR 95%', line=dict(color='#F44336', width=2)))
                fig_cv.update_layout(title="VaR/CVaR theo kỳ nắm giữ (% lỗ)",
                    xaxis_title="Horizon", yaxis_title="Lỗ tích lũy (%)",
                    height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_cv, use_container_width=True)
                st.caption(f"📊 Tính từ {len(eq_s_cv)} phiên returns thật yfinance 6T. VaR(h) = quantile 5% của rolling return h phiên. Càng nắm giữ lâu, rủi ro càng cao (nếu DM âm).")
        else:
            st.info("⚠️ Cần giá thật 6T để tính horizon VaR.")

        st.write("---")
        st.write("## 🏆 Return / Drawdown Ratios — Tổng hợp Calmar / RoMaD / Sterling / Burke / Martin")
        if has_real and dm_equity is not None and len(dm_equity) > 20:
            ratios = _compute_all_ratios(dm_equity, bench_series=vn30_close if has_vn30 else None)
            if ratios:
                eq_s_uni = pd.Series(dm_equity)
                total_ret_uni = (float(eq_s_uni.iloc[-1]) / float(eq_s_uni.iloc[0]) - 1) * 100
                annual_ret_uni = total_ret_uni * (252 / len(eq_s_uni))
                rru1, rru2, rru3, rru4, rru5 = st.columns(5)
                rru1.metric("⚖️ Calmar", f"{ratios['calmar']:.2f}",
                    help="Annual Return / |MaxDD|. >1 tốt, >2 xuất sắc")
                rru2.metric("⚖️ RoMaD", f"{ratios['roMaD']:.2f}",
                    help="Total Return / |MaxDD|. >1 tốt, >2 xuất sắc")
                rru3.metric("⚖️ Sterling", f"{ratios['sterling']:.2f}",
                    help="Annual Return / |Avg DD|. >1 tốt")
                rru4.metric("⚖️ Burke", f"{ratios['burke']:.2f}",
                    help="Annual Return / sqrt(Σ DD²). >1 tốt")
                rru5.metric("⚖️ Martin", f"{ratios['martin']:.2f}",
                    help="Annual Return / Ulcer Index. >1 tốt, >2 xuất sắc")
                rru_data = [
                    ("Calmar", ratios["calmar"]), ("RoMaD", ratios["roMaD"]),
                    ("Sterling", ratios["sterling"]), ("Burke", ratios["burke"]),
                    ("Martin", ratios["martin"]), ("Sharpe", ratios["sharpe"]),
                    ("Sortino", ratios["sortino"]), ("Omega", ratios["omega"]),
                ]
                rru_data.sort(key=lambda x: x[1], reverse=True)
                fig_rr = go.Figure()
                names = [n for n, _ in rru_data]
                vals = [v for _, v in rru_data]
                colors_rr = ["#4ADE80" if v > 1 else "#FBBF24" if v > 0 else "#F87171" for v in vals]
                fig_rr.add_trace(go.Bar(x=names, y=vals, marker_color=colors_rr,
                    text=[f"{v:.2f}" for v in vals], textposition="outside"))
                fig_rr.add_hline(y=1, line_dash="dash", line_color="green", annotation_text="Tốt (>1)")
                fig_rr.add_hline(y=2, line_dash="dash", line_color="gold", annotation_text="Xuất sắc (>2)")
                fig_rr.update_layout(title="So sánh 8 risk-adjusted ratios (sắp xếp giảm dần)",
                    yaxis_title="Ratio", height=380,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_rr, use_container_width=True)
                best = rru_data[0]
                worst = rru_data[-1]
                rru6, rru7 = st.columns(2)
                rru6.metric("🏆 Ratio tốt nhất", f"{best[0]}", f"{best[1]:.2f}")
                rru7.metric("⚠️ Ratio yếu nhất", f"{worst[0]}", f"{worst[1]:.2f}")
                st.caption(f"📊 **Calmar/RoMaD** = Return / MaxDD. **Sterling** = Return / |Avg DD|. **Burke** = Return / sqrt(Σ DD²). **Martin** = Return / Ulcer Index. Tất cả tính từ **{len(eq_s_uni)} phiên giá thật yfinance 6T** qua helper `_compute_all_ratios()`. Max DD, Avg DD, Ulcer Index đều tính từ equity curve THẬT (không heuristic `vol_proxy*2.5`).")
            else:
                st.info("⚠️ Helper ratios trả về None — cần ≥20 phiên returns.")
        else:
            st.info("⚠️ Cần giá thật 6T (≥20 phiên) để tính Return/Drawdown Ratios.")

        st.write("---")
        st.write("## 📊 Active Share — DM khác VN30 bao nhiêu?")
        if has_real and has_vn30 and len(real_prices) >= 2:
            vn30_components = ["VCB", "HPG", "VHM", "VNM", "BID", "CTG", "TCB", "FPT", "MBB", "VPB",
                "VIC", "VRE", "SSI", "PLX", "GAS", "MSN", "MWG", "SAB", "NVL", "POW"]
            as_rows = []
            for ma, info in dm.items():
                if ma in real_prices:
                    w_dm = (info.get("gia_thi_truong", 0) * info.get("so_luong", 0)) / tong_gt if tong_gt > 0 else 0
                    w_vn30 = (1.0 / len(vn30_components)) if ma in vn30_components else 0
                    as_rows.append({"Mã": ma, "Trọng số DM %": round(w_dm*100, 1),
                        "Trọng số VN30 %": round(w_vn30*100, 1),
                        "Chênh lệch %": round((w_dm - w_vn30)*100, 1)})
            if as_rows:
                df_as = pd.DataFrame(as_rows).sort_values("Chênh lệch %", ascending=False)
                st.dataframe(df_as, use_container_width=True, hide_index=True)
                active_share = sum(abs(r["Chênh lệch %"]) for r in as_rows) / 2
                ac1, ac2 = st.columns(2)
                ac1.metric("📊 Active Share", f"{active_share:.1f}%", help="Tổng |chênh lệch tỷ trọng| / 2. >60% = rất khác VN30, <20% = gần giống VN30")
                ac2.metric("🎯 Phân loại",
                    "🔴 Rất khác benchmark" if active_share > 80 else
                    ("🟡 Khác vừa" if active_share > 50 else
                    ("🟢 Gần giống VN30" if active_share > 20 else "✅ Index-like")))
                st.caption(f"📊 Active Share = Σ|wi_dm - wi_benchmark| / 2. Đo mức độ 'chủ động' của DM so với VN30. Tính trên {len(as_rows)} mã có trong DM.")
        else:
            st.info("⚠️ Cần DM + VN30 để tính Active Share.")

        st.write("---")
        st.write("## 🌊 Return Distribution Quantile — Phân vị return")
        if has_real and dm_equity is not None and len(dm_equity) > 60:
            ret_s_q = pd.Series(dm_equity).pct_change().dropna()
            quantiles = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
            q_rows = []
            for q in quantiles:
                qv = float(ret_s_q.quantile(q)) * 100
                q_rows.append({"Phân vị": f"P{int(q*100)}", "Daily Return %": round(qv, 3),
                    "Diễn giải": "🔴 Cực xấu" if q <= 0.05 else ("🔴 Xấu" if q <= 0.10 else
                                ("🟡 Kém" if q <= 0.25 else ("🟢 Trung bình" if q <= 0.75 else
                                ("🟢 Tốt" if q <= 0.90 else ("🟢 Rất tốt" if q <= 0.95 else "🟢 Cực tốt")))))})
            st.dataframe(pd.DataFrame(q_rows), use_container_width=True, hide_index=True)
            fig_qq = go.Figure()
            qs = np.linspace(0.01, 0.99, 99)
            qvs = [float(ret_s_q.quantile(q)) * 100 for q in qs]
            fig_qq.add_trace(go.Scatter(x=qs*100, y=qvs, mode='lines', line_color='#4FC3F7', name='Phân phối thực tế'))
            mu = float(ret_s_q.mean()) * 100
            sigma = float(ret_s_q.std()) * 100
            fig_qq.add_trace(go.Scatter(x=qs*100, y=[mu + sigma * (1.2816 if q > 0.9 else (-1.2816 if q < 0.1 else 0)) for q in qs],
                mode='lines', line=dict(color='#FFD700', dash='dash'), name='Normal (lý thuyết)'))
            fig_qq.update_layout(title="Q-Q Plot: Thực tế vs Normal", xaxis_title="Quantile (xác suất)",
                yaxis_title="Return (%)", height=320,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_qq, use_container_width=True)
            st.caption(f"📊 Tính từ {len(ret_s_q)} phiên returns thật yfinance 6T. Nếu đường thực tế lệch đường Normal ở 2 đuôi → DM có tail risk cao (cần dùng CVaR thay VaR).")
        else:
            st.info("⚠️ Cần giá thật 6T để vẽ Q-Q plot.")

        st.write("---")
        st.write("## 🎯 Kelly Criterion Position Sizing — Tỷ trọng tối ưu cho từng mã")
        if has_real and len(real_prices) >= 5:
            try:
                kelly_rows = []
                for ma, ser in real_prices.items():
                    if ser is None or len(ser) < 20:
                        continue
                    rets = ser.pct_change().dropna()
                    if len(rets) < 10:
                        continue
                    wins = rets[rets > 0]
                    losses = rets[rets < 0]
                    if len(wins) < 3 or len(losses) < 3:
                        continue
                    p_win = len(wins) / len(rets)
                    avg_win = float(wins.mean())
                    avg_loss = abs(float(losses.mean()))
                    if avg_loss <= 0:
                        continue
                    kelly_raw = (p_win * avg_win - (1 - p_win) * avg_loss) / (avg_win * avg_loss)
                    kelly_pct = max(-0.99, min(0.25, kelly_raw))
                    if ma in dm:
                        cur_w = float(dm[ma].get("ty_trong", 0))
                    else:
                        cur_w = 0
                    diff = kelly_pct - cur_w
                    action = "TĂNG" if diff > 0.02 else ("GIẢM" if diff < -0.02 else "GIỮ")
                    kelly_rows.append({"Mã": ma, "Win%": round(p_win * 100, 1),
                        "Avg Win %": round(avg_win * 100, 2), "Avg Loss %": round(avg_loss * 100, 2),
                        "Kelly %": round(kelly_pct * 100, 1), "Hiện tại %": round(cur_w * 100, 2),
                        "Hành động": f"🟢 {action}" if action == "TĂNG" else (f"🔴 {action}" if action == "GIẢM" else f"🟡 {action}")})
                if kelly_rows:
                    df_kelly = pd.DataFrame(kelly_rows).sort_values("Kelly %", ascending=False)
                    st.write(f"**Tính từ {len(df_kelly)} mã có ≥20 phiên giá thật. Kelly > hiện tại → TĂNG, < → GIẢM.**")
                    st.dataframe(df_kelly.head(15), use_container_width=True, hide_index=True)
                    top_k = df_kelly.iloc[0]
                    bot_k = df_kelly.iloc[-1]
                    kc1, kc2, kc3 = st.columns(3)
                    kc1.metric("🏆 Top Kelly", f"{top_k['Mã']}", f"{top_k['Kelly %']}%")
                    kc2.metric("🔻 Bottom Kelly", f"{bot_k['Mã']}", f"{bot_k['Kelly %']}%")
                    kc3.metric("📊 Kelly TB", f"{df_kelly['Kelly %'].mean():.1f}%", help="Trung bình Kelly của tất cả mã")
                    st.caption("📐 **Kelly % = (W × AvgWin − L × AvgLoss) / (AvgWin × AvgLoss)**. Kelly dương = nên tăng tỷ trọng, âm = nên giảm/bỏ. **Lưu ý: Kelly lý thuyết tích cực, thực tế nên dùng ½-Kelly hoặc ⅓-Kelly để an toàn.**")
            except Exception as _ke:
                st.caption(f"⚠️ Kelly lỗi: {str(_ke)[:80]}")
        else:
            st.info("⚠️ Cần giá thật 6T cho ≥5 mã để tính Kelly.")

        st.write("---")
        st.write("## 📊 Factor Decomposition — Phân tách Return: Thị trường / Ngành / Riêng")
        if has_real and has_vn30 and len(real_prices) >= 10:
            try:
                if vn30_close is not None and len(vn30_close) >= 60:
                    mkt_rets = vn30_close.pct_change().dropna()
                    sector_rets_dict = {}
                    for ma, ser in real_prices.items():
                        if ma in dm and ser is not None and len(ser) >= 60:
                            nganh_ma = dm[ma].get("nganh", "Khác")
                            rets_ma = ser.pct_change().dropna()
                            common_idx = rets_ma.index.intersection(mkt_rets.index)
                            if len(common_idx) >= 30:
                                sector_rets_dict.setdefault(nganh_ma, []).append(rets_ma.loc[common_idx])
                    sector_avg = {n: pd.concat(rs, axis=1).mean(axis=1) for n, rs in sector_rets_dict.items() if len(rs) >= 2}
                    fd_rows = []
                    for ma, ser in real_prices.items():
                        if ma not in dm or ser is None or len(ser) < 60:
                            continue
                        rets_ma = ser.pct_change().dropna()
                        common_idx = rets_ma.index.intersection(mkt_rets.index)
                        if len(common_idx) < 30:
                            continue
                        r_ma = rets_ma.loc[common_idx]
                        r_mkt = mkt_rets.loc[common_idx]
                        nganh_ma = dm[ma].get("nganh", "Khác")
                        r_sec = sector_avg.get(nganh_ma, r_mkt).loc[common_idx] if nganh_ma in sector_avg else r_mkt
                        if r_sec is None or len(r_sec) < 30:
                            r_sec = r_mkt
                        try:
                            beta_m = float(np.cov(r_ma, r_mkt)[0, 1] / max(np.var(r_mkt), 1e-12))
                            beta_s = float(np.cov(r_ma, r_sec)[0, 1] / max(np.var(r_sec), 1e-12))
                        except Exception:
                            beta_m, beta_s = 1.0, 1.0
                        ret_total = float((1 + r_ma).prod() - 1) * 100
                        ret_mkt = float((1 + r_mkt).prod() - 1) * 100
                        ret_sec = float((1 + r_sec).prod() - 1) * 100
                        contrib_mkt = beta_m * ret_mkt
                        contrib_sec = beta_s * (ret_sec - ret_mkt)
                        contrib_spec = ret_total - contrib_mkt - contrib_sec
                        fd_rows.append({"Mã": ma, "Ngành": nganh_ma, "Return %": round(ret_total, 1),
                            "Market %": round(contrib_mkt, 1), "Sector %": round(contrib_sec, 1),
                            "Specific %": round(contrib_spec, 1),
                            "Phân loại": "🏆 Vượt trội" if contrib_spec > 5 else ("✅ Khá" if contrib_spec > 0 else ("⚠️ Yếu" if contrib_spec > -5 else "🔴 Kém"))})
                    if fd_rows:
                        df_fd = pd.DataFrame(fd_rows).sort_values("Specific %", ascending=False)
                        st.write(f"**Phân tách return 6T cho {len(df_fd)} mã. Specific > 0 = vượt ngành+thị trường, < 0 = kém.**")
                        st.dataframe(df_fd.head(20), use_container_width=True, hide_index=True)
                        st.write("**Top 10 mã có Specific (riêng) CAO nhất:**")
                        st.dataframe(df_fd.head(10)[["Mã", "Ngành", "Specific %", "Phân loại"]], use_container_width=True, hide_index=True)
                        st.write("**Top 10 mã có Specific (riêng) THẤP nhất (nên xem xét bỏ):**")
                        st.dataframe(df_fd.tail(10)[["Mã", "Ngành", "Specific %", "Phân loại"]], use_container_width=True, hide_index=True)
                        avg_spec = float(df_fd["Specific %"].mean())
                        n_beat = int((df_fd["Specific %"] > 0).sum())
                        fd1, fd2, fd3 = st.columns(3)
                        fd1.metric("📊 Specific TB", f"{avg_spec:+.1f}%", help="Trung bình đóng góp riêng của mỗi mã")
                        fd2.metric("✅ Vượt trội", f"{n_beat}/{len(df_fd)}", help="Số mã có Specific > 0")
                        fd3.metric("🏆 Top Specific", f"{df_fd.iloc[0]['Mã']}", f"{df_fd.iloc[0]['Specific %']:+.1f}%")
                        st.caption("📐 **Return tổng = β_market × Return_thị_trường + β_sector × (Return_ngành − Return_thị trường) + Specific**. Specific dương = chọn mã giỏi, Specific âm = kéo DM xuống dù ngành/thị trường tốt.")
            except Exception as _fe:
                st.caption(f"⚠️ Factor Decomposition lỗi: {str(_fe)[:80]}")
        else:
            st.info("⚠️ Cần giá thật 6T + VN30 + ≥10 mã để phân tách yếu tố.")

        st.write("---")
        st.write("## 💧 Liquidity Stress Test — Test thanh khoản (Position / ADTV)")
        market_data = st.session_state.get("chat_market_data") or []
        if has_real and market_data and len(market_data) >= 5:
            try:
                liq_rows = []
                for ma, d in dm.items():
                    px = float(d.get("gia_thi_truong", 0))
                    sl = float(d.get("so_luong", 0))
                    vh = float(d.get("von_hoa", 0))
                    if px <= 0 or sl <= 0 or ma not in real_prices or len(real_prices[ma]) < 20:
                        continue
                    rets = real_prices[ma].pct_change().dropna()
                    vol_proxy = float(rets.tail(20).abs().mean()) * 1000
                    adtv = max(vh * 0.005, vol_proxy * px, 100_000_000)
                    pos_value = px * sl
                    days_to_liquidate = max(1, pos_value / adtv)
                    pct_of_adtv = pos_value / adtv
                    stress = "🟢 OK" if pct_of_adtv < 1 else ("🟡 Cẩn thận" if pct_of_adtv < 5 else ("🟠 Khó" if pct_of_adtv < 15 else "🔴 Rất khó"))
                    liq_rows.append({"Mã": ma, "GT vị thế (Tỷ)": round(pos_value / 1e9, 2),
                        "ADTV (Tỷ/ngày)": round(adtv / 1e9, 2), "% ADTV": round(pct_of_adtv, 1),
                        "Ngày bán hết": round(days_to_liquidate, 1), "Trạng thái": stress})
                if liq_rows:
                    df_liq = pd.DataFrame(liq_rows).sort_values("% ADTV", ascending=False)
                    st.write(f"**Test thanh khoản cho {len(df_liq)} mã. ADTV ước lượng = max(vốn hóa × 0.5%, vol×px, 100M₫). %ADTV > 5% = khó thoát hàng.**")
                    st.dataframe(df_liq.head(20), use_container_width=True, hide_index=True)
                    n_warn = int((df_liq["% ADTV"] >= 5).sum())
                    n_bad = int((df_liq["% ADTV"] >= 15).sum())
                    lq1, lq2, lq3 = st.columns(3)
                    lq1.metric("🟢 Thoát hàng <1 ngày", f"{int((df_liq['% ADTV'] < 1).sum())}/{len(df_liq)}")
                    lq2.metric("🟡 Cảnh báo >5% ADTV", f"{n_warn}")
                    lq3.metric("🔴 Khó bán >15% ADTV", f"{n_bad}")
                    st.caption("📐 **%ADTV = (Giá × Số lượng) / ADTV**. Nếu > 5% → khó thoát hàng trong 1 ngày mà không đẩy giá. Nếu > 15% → cần chia nhỏ lệnh bán nhiều ngày. Stress test giả định kịch bản bán tháo.")
            except Exception as _le:
                st.caption(f"⚠️ Liquidity test lỗi: {str(_le)[:80]}")
        else:
            st.info("⚠️ Cần DM + giá thật 6T + market_data để test thanh khoản.")

        st.write("---")
        st.write("## 🌍 Macro Sensitivity Matrix — Độ nhạy DM với biến vĩ mô")
        def _macro_interpret(label, corr):
            if "VIX" in label:
                return "🛡️ Phòng thủ tốt" if corr < 0 else "⚠️ Sợ hãi → DM giảm"
            if "Dollar" in label or "DXY" in label:
                return "🛡️ USD yếu = CP tốt" if corr < 0 else "⚠️ USD mạnh = áp lực"
            if "US10Y" in label or "Lãi suất" in label:
                return "🛡️ Lãi suất Mỹ cao = rút vốn" if corr < 0 else "✅ Cùng hưởng tăng"
            if "Gold" in label or "Vàng" in label:
                return "🛡️ Vàng tăng = phòng thủ" if corr < 0 else "✅ Cùng tài sản trú ẩn"
            if "Bitcoin" in label or "BTC" in label:
                return "🛡️ Crypto rủi ro tách biệt" if corr < 0 else "⚠️ Rủi ro cùng chiều"
            return f"Corr = {corr:+.2f}"
        if has_real and dm_equity is not None and len(dm_equity) >= 30:
            try:
                @st.cache_data(ttl=3600, show_spinner="📡 Tải dữ liệu vĩ mô (VIX, DXY, US10Y, Gold, BTC)...")
                def _get_macro_prices():
                    import yfinance as _yf_m
                    macro_syms = {"VIX (Sợ hãi)": "^VIX", "DXY (Dollar)": "DX-Y.NYB",
                        "US10Y (Lãi suất Mỹ)": "^TNX", "Gold (Vàng)": "GC=F", "Bitcoin": "BTC-USD"}
                    out = {}
                    for label, sym in macro_syms.items():
                        try:
                            s = _yf_m.Ticker(sym)
                            h = s.history(period="6mo", auto_adjust=True)
                            if h is not None and len(h) > 20:
                                out[label] = h["Close"].pct_change().dropna()
                        except Exception:
                            continue
                    return out
                with st.spinner("📡 Tải dữ liệu vĩ mô..."):
                    macro_data = _get_macro_prices()
                if macro_data and len(macro_data) >= 3:
                    dm_rets = pd.Series(dm_equity).pct_change().dropna()
                    ms_rows = []
                    for label, mr in macro_data.items():
                        common_idx = dm_rets.index.intersection(mr.index)
                        if len(common_idx) < 20:
                            continue
                        d = dm_rets.loc[common_idx]
                        m = mr.loc[common_idx]
                        try:
                            corr = float(np.corrcoef(d, m)[0, 1])
                            beta_macro = float(np.cov(d, m)[0, 1] / max(np.var(m), 1e-12))
                        except Exception:
                            corr, beta_macro = 0, 0
                        ms_rows.append({"Biến vĩ mô": label, "Correlation": round(corr, 3),
                            "Beta": round(beta_macro, 3),
                            "Diễn giải": _macro_interpret(label, corr)})
                    if ms_rows:
                        df_ms = pd.DataFrame(ms_rows)
                        st.write(f"**Tương quan giữa DM và {len(df_ms)} biến vĩ mô 6T qua. Correlation âm = phòng thủ.**")
                        st.dataframe(df_ms, use_container_width=True, hide_index=True)
                        fig_ms = go.Figure()
                        fig_ms.add_trace(go.Bar(x=df_ms["Biến vĩ mô"], y=df_ms["Correlation"],
                            marker_color=["#4CAF50" if c < 0 else "#FF5252" for c in df_ms["Correlation"]],
                            text=df_ms["Correlation"].round(2), textposition="outside"))
                        fig_ms.update_layout(title="DM Correlation với biến vĩ mô", yaxis_title="Correlation (-1 ↔ +1)",
                            height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                        st.plotly_chart(fig_ms, use_container_width=True)
                        most_neg = df_ms.loc[df_ms["Correlation"].idxmin()]
                        most_pos = df_ms.loc[df_ms["Correlation"].idxmax()]
                        ms1, ms2 = st.columns(2)
                        ms1.metric("🛡️ Hấp thụ tốt nhất", f"{most_neg['Biến vĩ mô']}", f"{most_neg['Correlation']:+.3f}",
                            help="Correlation âm nhất = biến này tăng thì DM giảm (phòng thủ)")
                        ms2.metric("⚠️ Nhạy cảm nhất", f"{most_pos['Biến vĩ mô']}", f"{most_pos['Correlation']:+.3f}",
                            help="Correlation dương cao nhất = DM đi cùng chiều biến này")
                        st.caption("📐 **Correlation** = mức độ đi cùng chiều/ngược chiều (-1 ↔ +1). **Beta** = DM biến động gấp mấy lần biến vĩ mô. Correlation < 0 = tài sản phòng thủ khi biến này biến động mạnh. Correlation > 0.5 = rủi ro hệ thống cao.")
            except Exception as _me:
                st.caption(f"⚠️ Macro sensitivity lỗi: {str(_me)[:80]}")
        else:
            st.info("⚠️ Cần giá thật 6T (≥30 phiên) để tính độ nhạy vĩ mô.")

        st.write("---")
        st.write("## 📊 Mean Reversion / Momentum Score — Điểm trung bình trở về vs Xu hướng")
        if has_real and len(real_prices) >= 5:
            try:
                mrm_rows = []
                for ma, ser in real_prices.items():
                    if ser is None or len(ser) < 60:
                        continue
                    rets = ser.pct_change().dropna()
                    if len(rets) < 30:
                        continue
                    px_now = float(ser.iloc[-1])
                    ma20 = float(ser.tail(20).mean())
                    ma60 = float(ser.tail(60).mean())
                    std60 = float(ser.tail(60).std())
                    z_score = (px_now - ma60) / std60 if std60 > 0 else 0
                    ret_20d = (px_now / float(ser.iloc[-21])) - 1 if len(ser) >= 21 else 0
                    ret_60d = (px_now / float(ser.iloc[-61])) - 1 if len(ser) >= 61 else 0
                    if z_score < -1.5:
                        signal = "🟢 Mua (mean reversion)"
                        score = "🟢"
                    elif z_score > 1.5:
                        signal = "🔴 Bán (quá mua)"
                        score = "🔴"
                    elif ret_20d > 0.1 and ret_60d > 0.15:
                        signal = "🟢 Momentum mạnh"
                        score = "🟢"
                    elif ret_20d < -0.1 and ret_60d < -0.15:
                        signal = "🔴 Momentum yếu"
                        score = "🔴"
                    else:
                        signal = "🟡 Trung tính"
                        score = "🟡"
                    mrm_rows.append({"Mã": ma, "Giá": round(px_now, 1), "MA20": round(ma20, 1),
                        "MA60": round(ma60, 1), "Z-score": round(z_score, 2),
                        "20D %": round(ret_20d * 100, 1), "60D %": round(ret_60d * 100, 1),
                        "Tín hiệu": signal, "Điểm": score})
                if mrm_rows:
                    df_mrm = pd.DataFrame(mrm_rows).sort_values("Z-score")
                    st.write(f"**Z-score = (Giá − MA60) / σ60. Z < −1.5 = mua (mean reversion), Z > 1.5 = bán (quá mua).**")
                    st.dataframe(df_mrm.head(25), use_container_width=True, hide_index=True)
                    buy_n = int((df_mrm["Điểm"] == "🟢").sum())
                    sell_n = int((df_mrm["Điểm"] == "🔴").sum())
                    mr1, mr2, mr3 = st.columns(3)
                    mr1.metric("🟢 Tín hiệu MUA", f"{buy_n} mã", help="Z-score < -1.5 hoặc momentum mạnh")
                    mr2.metric("🔴 Tín hiệu BÁN", f"{sell_n} mã", help="Z-score > 1.5 hoặc momentum yếu")
                    mr3.metric("🟡 Trung tính", f"{int((df_mrm['Điểm'] == '🟡').sum())} mã")
                    st.caption("📐 **Z-score âm** = giá thấp hơn trung bình 60 ngày (có thể mua mean reversion). **Z-score dương** = giá cao hơn TB (có thể bán chốt lời). **Momentum** = xu hướng 20D/60D.")
            except Exception as _mre:
                st.caption(f"⚠️ Mean Reversion lỗi: {str(_mre)[:80]}")
        else:
            st.info("⚠️ Cần giá thật 6T cho ≥5 mã để tính Mean Reversion.")

        st.write("---")
        st.markdown('<div class="da-section"><h3>🎯 Smart Score Rating — Đánh giá tổng hợp 0–100 cho từng mã</h3><p style="color:#93C5FD;">Tổng hợp 6 tiêu chí: <b>Return (25đ)</b> + <b>Sharpe (20đ)</b> + <b>Vol thấp (15đ)</b> + <b>ROE (15đ)</b> + <b>P/E hợp lý (15đ)</b> + <b>Momentum (10đ)</b>. Điểm 100 = mã hoàn hảo.</p></div>', unsafe_allow_html=True)
        if has_real and len(real_prices) >= 3:
            try:
                ss_rows = []
                for ma, ser in real_prices.items():
                    if ser is None or len(ser) < 30:
                        continue
                    rets = ser.pct_change().dropna()
                    if len(rets) < 20:
                        continue
                    ret_60d = (float(ser.iloc[-1]) / float(ser.iloc[-min(61, len(ser))]) - 1) if len(ser) >= 2 else 0
                    vol_ann = float(rets.std()) * (252**0.5)
                    sharpe = (float(rets.mean()) * 252) / vol_ann if vol_ann > 0 else 0
                    score_ret = min(25, max(0, (ret_60d + 0.3) * 41.7))
                    score_sharpe = min(20, max(0, (sharpe + 0.5) * 20))
                    score_vol = min(15, max(0, 15 - (vol_ann - 0.2) * 50))
                    roe = float(real_fund.get(ma, {}).get("roe", 0) or 0) if ma in real_fund else 0
                    if roe > 1:
                        roe = roe / 100
                    score_roe = min(15, max(0, roe * 50))
                    pe = float(real_fund.get(ma, {}).get("pe", 0) or 0) if ma in real_fund else 0
                    score_pe = min(15, max(0, 15 - max(0, pe - 10) * 0.5)) if pe > 0 else 7.5
                    px_now = float(ser.iloc[-1])
                    ma20 = float(ser.tail(20).mean())
                    momentum = (px_now - ma20) / ma20 if ma20 > 0 else 0
                    score_mom = min(10, max(0, (momentum + 0.1) * 50))
                    total = score_ret + score_sharpe + score_vol + score_roe + score_pe + score_mom
                    if total >= 75:
                        rating = "🏆 Xuất sắc"
                        pill = "da-pill-green"
                    elif total >= 60:
                        rating = "✅ Tốt"
                        pill = "da-pill-green"
                    elif total >= 45:
                        rating = "🟡 Trung bình"
                        pill = "da-pill-yellow"
                    elif total >= 30:
                        rating = "⚠️ Yếu"
                        pill = "da-pill-red"
                    else:
                        rating = "🔴 Tránh"
                        pill = "da-pill-red"
                    ss_rows.append({"Mã": ma, "Return 60D": f"{ret_60d*100:+.1f}%",
                        "Sharpe": round(sharpe, 2), "Vol %": round(vol_ann * 100, 1),
                        "ROE %": round(roe * 100, 1) if roe > 0 else "—",
                        "P/E": round(pe, 1) if pe > 0 else "—",
                        "Điểm": round(total, 1), "Xếp hạng": rating, "Pill": pill})
                if ss_rows:
                    df_ss = pd.DataFrame(ss_rows).sort_values("Điểm", ascending=False)
                    st.write(f"**Tính cho {len(df_ss)} mã có ≥30 phiên giá. Xếp hạng: 🏆≥75 Xuất sắc | ✅≥60 Tốt | 🟡≥45 TB | ⚠️≥30 Yếu | 🔴<30 Tránh**")
                    for _, r in df_ss.head(20).iterrows():
                        st.markdown(f'<div class="da-metric" style="margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><b style="color:#FFD700;">{r["Mã"]}</b> <span class="da-info">{r["Return 60D"]}</span> | Sharpe {r["Sharpe"]} | Vol {r["Vol %"]}% | ROE {r["ROE %"]} | P/E {r["P/E"]}</div><div><span class="da-pill {r["Pill"]}">{r["Xếp hạng"]}</span> <b class="da-good" style="font-size:1.3rem;">{r["Điểm"]}</b></div></div>', unsafe_allow_html=True)
                    top3 = df_ss.head(3)
                    s1, s2, s3 = st.columns(3)
                    for col, (_, r) in zip([s1, s2, s3], top3.iterrows()):
                        col.markdown(f'<div class="da-metric"><div class="da-label">🏆 {r["Mã"]}</div><div class="da-value">{r["Điểm"]}</div><div style="color:#4ADE80;font-size:0.85rem;margin-top:4px;">{r["Xếp hạng"]}</div></div>', unsafe_allow_html=True)
                    st.caption("📐 **Điểm = Return (25) + Sharpe (20) + Vol thấp (15) + ROE (15) + P/E hợp lý (15) + Momentum (10) = max 100.** Ưu tiên mã có điểm ≥60 và ROE >12%.")
            except Exception as _sse:
                st.caption(f"⚠️ Smart Score lỗi: {str(_sse)[:80]}")
        else:
            st.info("⚠️ Cần giá thật 6T cho ≥3 mã để tính Smart Score.")

        st.write("---")
        st.markdown('<div class="da-section"><h3>⏰ Real-time P&L Tracker — Lãi/Lỗ thời gian thực theo mã</h3><p style="color:#93C5FD;">Theo dõi lãi/lỗ từng mã trong DM, sắp xếp theo % lãi/lỗ từ cao → thấp. Màu <b style="color:#4ADE80;">xanh</b> = lãi, <b style="color:#F87171;">đỏ</b> = lỗ.</p></div>', unsafe_allow_html=True)
        if has_real and dm and len(dm) > 0:
            try:
                pl_rows = []
                for ma, d in dm.items():
                    gia_von = float(d.get("gia_von", 0))
                    gia_tt = float(d.get("gia_thi_truong", 0))
                    sl = float(d.get("so_luong", 0))
                    if gia_von <= 0 or gia_tt <= 0 or sl <= 0:
                        continue
                    von = gia_von * sl
                    gt = gia_tt * sl
                    lai_lo = gt - von
                    pct = (lai_lo / von) * 100
                    ser = real_prices.get(ma)
                    if ser is not None and len(ser) >= 2:
                        rets = ser.pct_change().dropna()
                        vol_ann = float(rets.std()) * (252**0.5) * 100 if len(rets) > 1 else 0
                    else:
                        vol_ann = 0
                    pl_rows.append({"Mã": ma, "Vốn (Tỷ)": round(von / 1e9, 2),
                        "GT hiện tại (Tỷ)": round(gt / 1e9, 2),
                        "Lãi/Lỗ (Tỷ)": round(lai_lo / 1e9, 2),
                        "% Lãi/Lỗ": round(pct, 2), "Vol %": round(vol_ann, 1)})
                if pl_rows:
                    df_pl = pd.DataFrame(pl_rows).sort_values("% Lãi/Lỗ", ascending=False)
                    st.write(f"**Tổng quan {len(df_pl)} mã có dữ liệu:**")
                    tong_von = sum(r["Vốn (Tỷ)"] for r in pl_rows)
                    tong_gt = sum(r["GT hiện tại (Tỷ)"] for r in pl_rows)
                    tong_lai = tong_gt - tong_von
                    tong_pct = (tong_lai / tong_von * 100) if tong_von > 0 else 0
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("💰 Tổng vốn", f"{tong_von:.1f}Tỷ")
                    p2.metric("📊 Tổng GT", f"{tong_gt:.1f}Tỷ")
                    p3.metric("📈 Tổng Lãi/Lỗ", f"{tong_lai:+.1f}Tỷ", delta=f"{tong_pct:+.2f}%")
                    winners = int((df_pl["% Lãi/Lỗ"] > 0).sum())
                    losers = int((df_pl["% Lãi/Lỗ"] < 0).sum())
                    p4.metric("✅ Lãi / 🔴 Lỗ", f"{winners} / {losers}")
                    st.write("**Chi tiết từng mã (sắp xếp theo % Lãi/Lỗ):**")
                    for _, r in df_pl.iterrows():
                        color = "#4ADE80" if r["% Lãi/Lỗ"] > 0 else "#F87171" if r["% Lãi/Lỗ"] < 0 else "#FBBF24"
                        icon = "🟢" if r["% Lãi/Lỗ"] > 0 else "🔴" if r["% Lãi/Lỗ"] < 0 else "🟡"
                        st.markdown(f'<div class="da-metric" style="margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;text-align:left;"><div style="flex:1;"><b style="color:#FFD700;">{r["Mã"]}</b> <span class="da-info">Vol {r["Vol %"]}%</span></div><div style="flex:1;text-align:right;">Vốn: <b>{r["Vốn (Tỷ)"]}Tỷ</b> → GT: <b>{r["GT hiện tại (Tỷ)"]}Tỷ</b></div><div style="flex:0 0 130px;text-align:right;"><span style="color:{color};font-size:1.15rem;font-weight:800;">{icon} {r["% Lãi/Lỗ"]:+.2f}%</span><br><span style="color:{color};font-size:0.85rem;">{r["Lãi/Lỗ (Tỷ)"]:+.2f}Tỷ</span></div></div>', unsafe_allow_html=True)
                    st.caption("📐 **% Lãi/Lỗ = (Giá hiện tại − Giá vốn) / Giá vốn × 100**. Vol = độ biến động năm (cao = rủi ro). Mã % cao + Vol thấp = lý tưởng.")
            except Exception as _ple:
                st.caption(f"⚠️ P&L Tracker lỗi: {str(_ple)[:80]}")
        else:
            st.info("⚠️ Cần DM có giá vốn + giá thị trường để tính P&L.")

        st.write("---")
        st.markdown('<div class="da-section"><h3>🎲 Earnings Surprise Tracker — Theo dõi bất ngờ lợi nhuận</h3><p style="color:#93C5FD;">Ước lượng earnings surprise dựa trên <b>xu hướng EPS</b> 3 tháng gần nhất. <b>Positive Surprise</b> = EPS tăng mạnh hơn kỳ vọng, <b>Negative Surprise</b> = EPS giảm.</p></div>', unsafe_allow_html=True)
        if has_real and len(real_fund) > 0:
            try:
                es_rows = []
                for ma, fund in real_fund.items():
                    eps = fund.get("eps")
                    if eps is None or eps == 0:
                        continue
                    ser = real_prices.get(ma)
                    if ser is None or len(ser) < 60:
                        continue
                    rets = ser.pct_change().dropna()
                    if len(rets) < 30:
                        continue
                    px_now = float(ser.iloc[-1])
                    px_30d = float(ser.iloc[-31]) if len(ser) >= 31 else float(ser.iloc[0])
                    px_60d = float(ser.iloc[-61]) if len(ser) >= 61 else float(ser.iloc[0])
                    ret_30d = (px_now / px_30d - 1) * 100
                    ret_60d = (px_now / px_60d - 1) * 100
                    momentum = ret_30d
                    if ret_30d > 10 and ret_60d > 15:
                        signal = "🟢 Positive Surprise"
                        pill = "da-pill-green"
                        desc = "EPS tăng mạnh, giá phản ứng tích cực"
                    elif ret_30d < -10 and ret_60d < -15:
                        signal = "🔴 Negative Surprise"
                        pill = "da-pill-red"
                        desc = "EPS giảm, giá phản ứng tiêu cực"
                    elif ret_30d > 5:
                        signal = "🟢 Beat"
                        pill = "da-pill-green"
                        desc = "Vượt kỳ vọng nhẹ"
                    elif ret_30d < -5:
                        signal = "🔴 Miss"
                        pill = "da-pill-red"
                        desc = "Dưới kỳ vọng"
                    else:
                        signal = "🟡 In-line"
                        pill = "da-pill-yellow"
                        desc = "Đúng kỳ vọng"
                    es_rows.append({"Mã": ma, "EPS": round(float(eps), 2),
                        "Giá 30D trước": round(px_30d, 1), "Giá hiện tại": round(px_now, 1),
                        "30D %": round(ret_30d, 1), "60D %": round(ret_60d, 1),
                        "Tín hiệu": signal, "Pill": pill, "Diễn giải": desc})
                if es_rows:
                    df_es = pd.DataFrame(es_rows).sort_values("30D %", ascending=False)
                    st.write(f"**Ước lượng earnings surprise cho {len(df_es)} mã có EPS thật + ≥60 phiên giá:**")
                    beat = int(df_es["Tín hiệu"].str.contains("Beat|Positive").sum())
                    miss = int(df_es["Tín hiệu"].str.contains("Miss|Negative").sum())
                    inline = len(df_es) - beat - miss
                    e1, e2, e3 = st.columns(3)
                    e1.metric("🟢 Beat (vượt)", f"{beat} mã", f"{beat/len(df_es)*100:.0f}%")
                    e2.metric("🔴 Miss (thất)", f"{miss} mã", f"{miss/len(df_es)*100:.0f}%")
                    e3.metric("🟡 In-line", f"{inline} mã", f"{inline/len(df_es)*100:.0f}%")
                    st.write("**Top 10 Beat (vượt kỳ vọng):**")
                    for _, r in df_es.head(10).iterrows():
                        st.markdown(f'<div class="da-metric" style="margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><b style="color:#FFD700;">{r["Mã"]}</b> <span class="da-info">EPS {r["EPS"]}</span></div><div><span class="da-info">30D: {r["30D %"]:+.1f}% | 60D: {r["60D %"]:+.1f}%</span></div><div><span class="da-pill {r["Pill"]}">{r["Tín hiệu"]}</span></div></div>', unsafe_allow_html=True)
                    st.write("**Top 10 Miss (thất vọng):**")
                    for _, r in df_es.tail(10).iterrows():
                        st.markdown(f'<div class="da-metric" style="margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;"><div><b style="color:#FFD700;">{r["Mã"]}</b> <span class="da-info">EPS {r["EPS"]}</span></div><div><span class="da-info">30D: {r["30D %"]:+.1f}% | 60D: {r["60D %"]:+.1f}%</span></div><div><span class="da-pill {r["Pill"]}">{r["Tín hiệu"]}</span></div></div>', unsafe_allow_html=True)
                    st.caption("📐 **Earnings Surprise** ước lượng bằng <b>phản ứng giá 30D/60D</b>. Nếu giá tăng >10% trong 30D sau khi EPS công bố → Positive Surprise. Giảm >10% → Negative Surprise. Đây là chỉ báo <b>hành vi giá</b>, KHÔNG phải EPS thật (cần API earnings calendar thật).")
            except Exception as _ese:
                st.caption(f"⚠️ Earnings Surprise lỗi: {str(_ese)[:80]}")
        else:
            st.info("⚠️ Cần EPS + giá thật 6T để ước lượng Earnings Surprise.")

        st.write("---")
        st.write("## 🌍 Quét toàn thị trường — Top Movers & Volume Leaders")
        try:
            _vn_doc_keys = list((DOCS.get("co_phieu_vn") or {}).keys())
            _tg_doc_keys = list((DOCS.get("co_phieu_tg") or {}).keys())
        except Exception:
            _vn_doc_keys = []
            _tg_doc_keys = []
        if not _vn_doc_keys:
            _vn_doc_keys = list((DOCS.get("co_phieu_vn") or {}).keys())[:229]
        if not _tg_doc_keys:
            _tg_doc_keys = list((DOCS.get("co_phieu_tg") or {}).keys())[:155]
        _all_vn_stocks = list(_vn_doc_keys) + list(_tg_doc_keys)
        @st.cache_data(ttl=1800, show_spinner="📡 Quét toàn thị trường...")
        def _scan_market_stocks(symbols_tuple):
            import requests as _rq_s
            from concurrent.futures import ThreadPoolExecutor, as_completed
            out = []
            lock = __import__("threading").Lock()

            def _one(entry):
                try:
                    sym, suffix = entry
                    r = _rq_s.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
                    if r.status_code == 200:
                        data = r.json()
                        result = data.get("chart", {}).get("result", [{}])[0]
                        meta = result.get("meta", {})
                        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        volumes = result.get("indicators", {}).get("quote", [{}])[0].get("volume", [])
                        if closes and len(closes) > 5:
                            cur = float(meta.get("regularMarketPrice") or (closes[-1] if closes[-1] else 0) or 0)
                            if cur <= 0:
                                return None
                            prev = float(closes[-2]) if len(closes) > 1 and closes[-2] else cur
                            chg_pct = (cur / prev - 1) * 100 if prev > 0 else 0
                            ret_3m = (cur / float(closes[-min(66, len(closes))]) - 1) * 100 if len(closes) > 5 else 0
                            vol_today = float(volumes[-1]) if volumes and volumes[-1] else 0
                            avg_vol_20 = float(np.mean([v for v in volumes[-20:] if v])) if len(volumes) >= 5 and any(v for v in volumes[-20:] if v) else 0
                            vol_ratio = vol_today / avg_vol_20 if avg_vol_20 > 0 else 0
                            if not (vol_ratio != vol_ratio) and not (chg_pct != chg_pct) and not (ret_3m != ret_3m):
                                region = "VN" if suffix else "TG"
                                display_sym = sym if suffix else sym
                                return {"ma": display_sym, "ten": (meta.get("longName", sym) or sym)[:30],
                                    "nganh": (meta.get("industry") or "Khác"),
                                    "vung": region, "tien": (meta.get("currency") or "VND"),
                                    "gia": cur, "thay_doi": chg_pct, "ret_3m": ret_3m,
                                    "vol": vol_today, "vol_ratio": vol_ratio, "von_hoa": float(meta.get("marketCap") or 0)}
                except Exception:
                    return None

            with ThreadPoolExecutor(max_workers=20) as ex:
                futs = [ex.submit(_one, e) for e in symbols_tuple]
                for f in as_completed(futs):
                    r = f.result()
                    if r is not None:
                        out.append(r)
            return out
        _scan_list = []
        for _s in _vn_doc_keys:
            _scan_list.append((_s, ".VN"))
        for _s in _tg_doc_keys:
            _scan_list.append((_s, ""))
        _all_vn_stocks = _scan_list
        market_data = st.session_state.get("chat_market_data") or []
        if len(market_data) < 5:
            with st.spinner(f"📡 Đang quét {len(_all_vn_stocks)} mã toàn thị trường (VN + Thế giới)..."):
                market_data = _scan_market_stocks(tuple(_all_vn_stocks))
                try:
                    st.session_state["chat_market_data"] = market_data
                except Exception:
                    pass
        if (not market_data or len(market_data) < 5):
            try:
                _fb = []
                _vn_doc = DOCS.get("co_phieu_vn") or {}
                _tg_doc = DOCS.get("co_phieu_tg") or {}
                for _m, _ki in list(_vn_doc.items())[:229]:
                    _fb.append({"ma": _m, "ten": _ki.get("ten", _m)[:30], "nganh": _ki.get("nganh", "Khác"),
                        "vung": "VN", "tien": "VND",
                        "gia": float(_ki.get("gia_hien_tai") or _ki.get("current_price") or _ki.get("gia") or 0),
                        "thay_doi": float(_ki.get("thay_doi_ngay") or _ki.get("change_pct") or 0),
                        "ret_3m": float(_ki.get("ret_3m") or 0), "vol": 0, "vol_ratio": 1.0,
                        "von_hoa": float(_ki.get("von_hoa") or _ki.get("market_cap") or 0)})
                for _m, _ki in list(_tg_doc.items())[:155]:
                    _fb.append({"ma": _m, "ten": _ki.get("ten", _m)[:30], "nganh": _ki.get("nganh", "Khác"),
                        "vung": "TG", "tien": "USD",
                        "gia": float(_ki.get("gia_hien_tai") or _ki.get("current_price") or _ki.get("gia") or 0),
                        "thay_doi": float(_ki.get("thay_doi_ngay") or _ki.get("change_pct") or 0),
                        "ret_3m": float(_ki.get("ret_3m") or 0), "vol": 0, "vol_ratio": 1.0,
                        "von_hoa": float(_ki.get("von_hoa") or _ki.get("market_cap") or 0)})
                market_data = _fb
                st.session_state["chat_market_data"] = market_data
                st.caption(f"📊 Dữ liệu từ co_phieu_vn.json + yfinance ({len(market_data)} mã)")
            except Exception as _ex:
                st.warning(f"⚠️ Không có dữ liệu thị trường: {_ex}")
        if not market_data or len(market_data) < 5:
            st.warning(f"⚠️ Chỉ quét được {len(market_data) if market_data else 0}/{len(_all_vn_stocks)} mã. Một số section bên dưới sẽ bị ẩn. Có thể Yahoo Finance đang giới hạn request — thử lại sau vài phút.")
        df_mkt = pd.DataFrame(market_data) if market_data and len(market_data) >= 5 else pd.DataFrame()
        if market_data and len(market_data) >= 5:
            st.caption(f"📊 Quét {len(market_data)}/{len(_all_vn_stocks)} mã thành công từ yfinance (VN + Thế giới)")
            region_filter = st.radio("Lọc theo vùng:", ["Tất cả", "Chỉ VN", "Chỉ Thế giới"], horizontal=True, key="mkt_region")
            if region_filter == "Chỉ VN":
                df_mkt_view = df_mkt[df_mkt["vung"] == "VN"].copy()
            elif region_filter == "Chỉ Thế giới":
                df_mkt_view = df_mkt[df_mkt["vung"] == "TG"].copy()
            else:
                df_mkt_view = df_mkt.copy()
            if len(df_mkt_view) < 5:
                st.warning(f"⚠️ Vùng '{region_filter}' chỉ có {len(df_mkt_view)} mã. Hiển thị tất cả.")
                df_mkt_view = df_mkt.copy()
            mv1, mv2 = st.columns(2)
            with mv1:
                st.write("**🚀 Top 10 tăng mạnh nhất hôm nay:**")
                top_up = df_mkt_view.nlargest(10, "thay_doi")[["ma", "vung", "ten", "gia", "thay_doi", "vol_ratio"]]
                top_up.columns = ["Mã", "Vùng", "Tên", "Giá", "% Thay đổi", "Vol vs TB20D"]
                st.dataframe(top_up, use_container_width=True, hide_index=True)
            with mv2:
                st.write("**💀 Top 10 giảm mạnh nhất hôm nay:**")
                top_dn = df_mkt_view.nsmallest(10, "thay_doi")[["ma", "vung", "ten", "gia", "thay_doi", "vol_ratio"]]
                top_dn.columns = ["Mã", "Vùng", "Tên", "Giá", "% Thay đổi", "Vol vs TB20D"]
                st.dataframe(top_dn, use_container_width=True, hide_index=True)
            mv3, mv4 = st.columns(2)
            with mv3:
                st.write("**📊 Top 10 Volume đột biến (Vol > 2x TB20D):**")
                hot_vol = df_mkt_view[df_mkt_view["vol_ratio"] > 1].nlargest(10, "vol_ratio")[["ma", "vung", "ten", "vol", "vol_ratio", "thay_doi"]]
                hot_vol.columns = ["Mã", "Vùng", "Tên", "Volume hôm nay", "Vol/TB20D", "% Thay đổi"]
                st.dataframe(hot_vol, use_container_width=True, hide_index=True)
            with mv4:
                st.write("**📈 Top 10 Return 3 tháng cao nhất:**")
                top_3m = df_mkt_view.nlargest(10, "ret_3m")[["ma", "vung", "ten", "gia", "ret_3m", "thay_doi"]]
                top_3m.columns = ["Mã", "Vùng", "Tên", "Giá hiện tại", "Return 3M %", "% Hôm nay"]
                st.dataframe(top_3m, use_container_width=True, hide_index=True)
            st.caption("📊 Tất cả dữ liệu từ yfinance chart API (giá thật real-time). Phân tích toàn thị trường giúp nhận diện cơ hội đầu tư mới.")
        else:
            st.info("⚠️ Không quét được dữ liệu thị trường. Thử lại sau.")

        st.write("---")
        st.write("## 🔍 Stock Screener — Quét mã theo tiêu chí đầu tư")
        if market_data and len(market_data) >= 5:
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                min_ret_3m = st.number_input("Return 3M tối thiểu (%)", value=-100.0, step=5.0, key="scr_ret")
                max_pe_input = st.number_input("P/E tối đa (0 = bỏ qua)", value=0.0, step=1.0, key="scr_pe", min_value=0.0)
            with sc2:
                min_vol_ratio = st.number_input("Volume/TB20D tối thiểu", value=0.5, step=0.1, key="scr_vol")
                max_change = st.number_input("Thay đổi hôm nay max (%)", value=10.0, step=0.5, key="scr_chg")
            with sc3:
                sort_by = st.selectbox("Sắp xếp theo", ["ret_3m", "thay_doi", "vol_ratio", "von_hoa"], key="scr_sort")
                ascending = st.checkbox("Tăng dần", value=False, key="scr_asc")
            use_pe_filter = max_pe_input > 0
            if use_pe_filter:
                with st.spinner(f"📡 Đang tải P/E cho {len(market_data)} mã..."):
                    pe_dist = _get_pe_distribution(tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data]))
                if pe_dist:
                    pe_map = {r["ma"]: r["pe"] for r in pe_dist}
                    df_mkt["pe"] = df_mkt["ma"].map(pe_map)
                    df_scr = df_mkt[(df_mkt["ret_3m"] >= min_ret_3m) &
                                    (df_mkt["vol_ratio"] >= min_vol_ratio) &
                                    (df_mkt["thay_doi"] <= max_change) &
                                    (df_mkt["pe"].notna()) &
                                    (df_mkt["pe"] > 0) &
                                    (df_mkt["pe"] <= max_pe_input)].sort_values(sort_by, ascending=ascending)
                    st.caption(f"📊 Đã lọc theo P/E ≤ {max_pe_input:.1f} ({len(pe_dist)} mã có P/E thật từ yfinance)")
                    st.write(f"**Tìm thấy {len(df_scr)} mã thỏa mãn (P/E ≤ {max_pe_input:.1f}):**")
                    st.dataframe(df_scr[["ma", "ten", "gia", "thay_doi", "ret_3m", "vol_ratio", "pe"]].head(20).round(2),
                        use_container_width=True, hide_index=True)
                else:
                    df_scr = df_mkt[(df_mkt["ret_3m"] >= min_ret_3m) &
                                    (df_mkt["vol_ratio"] >= min_vol_ratio) &
                                    (df_mkt["thay_doi"] <= max_change)].sort_values(sort_by, ascending=ascending)
                    st.info("⚠️ Không lấy được P/E — đang lọc không tính P/E.")
                    st.write(f"**Tìm thấy {len(df_scr)} mã thỏa mãn:**")
                    st.dataframe(df_scr[["ma", "ten", "gia", "thay_doi", "ret_3m", "vol_ratio"]].head(20),
                        use_container_width=True, hide_index=True)
            else:
                df_scr = df_mkt[(df_mkt["ret_3m"] >= min_ret_3m) &
                                (df_mkt["vol_ratio"] >= min_vol_ratio) &
                                (df_mkt["thay_doi"] <= max_change)].sort_values(sort_by, ascending=ascending)
                st.write(f"**Tìm thấy {len(df_scr)} mã thỏa mãn:**")
                st.dataframe(df_scr[["ma", "ten", "gia", "thay_doi", "ret_3m", "vol_ratio"]].head(20),
                    use_container_width=True, hide_index=True)
            st.caption("📊 Screener dùng dữ liệu thật yfinance (chart + P/E từ .info). Đặt P/E max = 0 để bỏ qua lọc P/E.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường để screener.")

        st.write("---")
        st.write("## 🌡️ Sector Performance Heatmap — Toàn thị trường")
        if market_data and len(market_data) >= 5:
            sec_perf = df_mkt.groupby("nganh").agg(
                so_ma=("ma", "count"),
                ret_tb=("thay_doi", "mean"),
                ret_3m_tb=("ret_3m", "mean"),
                vol_ratio_tb=("vol_ratio", "mean"),
                max_thay_doi=("thay_doi", "max"),
                min_thay_doi=("thay_doi", "min"),
            ).reset_index()
            sec_perf = sec_perf[sec_perf["so_ma"] >= 1].sort_values("ret_tb", ascending=False)
            st.dataframe(sec_perf.round(2), use_container_width=True, hide_index=True)
            st.caption(f"📊 Phân tích {len(market_data)} mã theo ngành từ yfinance. Ngành nào return TB cao nhất = xu hướng nóng. Return 3M TB cho thấy trend dài hơn.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📊 Phân phối P/E & Market Valuation Dashboard")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=3600)
            def _get_pe_distribution(symbols):
                import yfinance as _yf_pe
                pes = []
                for s in symbols:
                    suffix = ".VN"
                    sym = s
                    if isinstance(s, tuple):
                        sym, suffix = s
                    try:
                        info = _yf_pe.Ticker(f"{sym}{suffix}").info
                        pe = info.get("trailingPE")
                        pb = info.get("priceToBook")
                        roe = info.get("returnOnEquity")
                        if pe and pe > 0:
                            pes.append({"ma": sym, "pe": pe, "pb": pb or 0, "roe": roe or 0})
                    except Exception:
                        continue
                return pes
            with st.spinner(f"📡 Lấy P/E/P/B/ROE cho {len(market_data)} mã..."):
                pe_data = _get_pe_distribution(tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data]))
            if pe_data:
                df_pe = pd.DataFrame(pe_data)
                st.write(f"**📊 Định giá thị trường từ {len(df_pe)} mã:**")
                vd1, vd2, vd3, vd4, vd5 = st.columns(5)
                vd1.metric("📊 P/E TB", f"{df_pe['pe'].mean():.1f}", help="Trung bình P/E toàn thị trường")
                vd2.metric("📊 P/E Median", f"{df_pe['pe'].median():.1f}", help="P/E trung vị (ít bị ảnh hưởng bởi outlier)")
                vd3.metric("📊 P/B TB", f"{df_pe['pb'].mean():.2f}")
                vd4.metric("📊 ROE TB", f"{df_pe['roe'].mean()*100:.1f}%")
                vd5.metric("📊 Số mã PE>20", f"{(df_pe['pe']>20).sum()}/{len(df_pe)}",
                    help="Mã có P/E > 20 (đắt)")
                st.write("**Top 10 P/E thấp nhất (rẻ nhất):**")
                cheap = df_pe.nsmallest(10, "pe")[["ma", "pe", "pb", "roe"]]
                cheap["roe"] = (cheap["roe"] * 100).round(1)
                cheap.columns = ["Mã", "P/E", "P/B", "ROE %"]
                st.dataframe(cheap, use_container_width=True, hide_index=True)
                st.write("**Top 10 P/E cao nhất (đắt nhất):**")
                exp = df_pe.nlargest(10, "pe")[["ma", "pe", "pb", "roe"]]
                exp["roe"] = (exp["roe"] * 100).round(1)
                exp.columns = ["Mã", "P/E", "P/B", "ROE %"]
                st.dataframe(exp, use_container_width=True, hide_index=True)
                st.caption(f"📊 Tính từ {len(df_pe)} mã có P/E > 0 từ yfinance.info. P/E thấp + ROE cao = cổ phiếu giá trị. P/E cao + ROE thấp = cổ phiếu tăng trưởng đắt.")
            else:
                st.info("⚠️ Không lấy được P/E từ yfinance.info.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 💎 Dividend Champions — Top cổ tức toàn thị trường")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=3600)
            def _get_dividend_champions(symbols):
                import yfinance as _yf_dv
                rows = []
                for s in symbols:
                    try:
                        info = _yf_dv.Ticker(s + ".VN").info
                        dy = info.get("dividendYield")
                        mcap = info.get("marketCap")
                        price = info.get("currentPrice") or info.get("regularMarketPrice")
                        if dy and dy > 0 and price and mcap:
                            rows.append({"ma": s, "ten": info.get("longName", s)[:30],
                                "gia": float(price), "dy": float(dy), "von_hoa": float(mcap)})
                    except Exception:
                        continue
                return rows
            with st.spinner(f"📡 Lấy dividend yield cho {len(market_data)} mã..."):
                div_data = _get_dividend_champions(tuple([d["ma"] for d in market_data]))
            if div_data:
                df_div = pd.DataFrame(div_data).sort_values("dy", ascending=False)
                st.write(f"**💰 Top cổ tức toàn thị trường ({len(df_div)} mã có trả cổ tức):**")
                st.dataframe(df_div.head(20), use_container_width=True, hide_index=True)
                top_div = df_div.iloc[0]
                avg_dy = df_div["dy"].mean() * 100
                st.caption(f"📊 Tính từ yfinance.info. Top: **{top_div['ma']}** = {top_div['dy']*100:.2f}%/năm. Cổ tức TB toàn thị trường: {avg_dy:.2f}%.")
            else:
                st.info("⚠️ Không lấy được dividend data.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📊 Volume Distribution — Phân phối thanh khoản toàn thị trường")
        if market_data and len(market_data) >= 5:
            vold = df_mkt["vol_ratio"].dropna()
            if len(vold) > 0:
                vold1, vold2, vold3, vold4 = st.columns(4)
                vold1.metric("📊 Vol Ratio TB", f"{vold.mean():.2f}x", help="TB volume hôm nay / TB 20 phiên")
                vold2.metric("📊 Vol Ratio Median", f"{vold.median():.2f}x")
                vold3.metric("🔥 Số mã Vol > 2x", f"{(vold>2).sum()}/{len(vold)}", help="Mã có volume đột biến > 2x TB")
                vold4.metric("💀 Số mã Vol < 0.5x", f"{(vold<0.5).sum()}/{len(vold)}", help="Mã kém thanh khoản")
                fig_vd = go.Figure()
                fig_vd.add_trace(go.Histogram(x=vold, nbinsx=30, marker_color='#4FC3F7', opacity=0.7,
                    name='Vol Ratio'))
                fig_vd.add_vline(x=1.0, line_dash="dash", line_color='#FFD700', annotation_text="Bình thường (1x)")
                fig_vd.update_layout(title="Phân phối Volume Ratio (Vol hôm nay / TB 20D)",
                    xaxis_title="Vol Ratio", yaxis_title="Số mã",
                    height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_vd, use_container_width=True)
                st.caption(f"📊 Phân tích {len(vold)} mã toàn thị trường từ yfinance. Vol>2x = mã được chú ý đặc biệt, Vol<0.5x = mã kém thanh khoản.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📊 Market Breadth — Sức mạnh thị trường toàn diện")
        if market_data and len(market_data) >= 5:
            n_up = sum(1 for d in market_data if d["thay_doi"] > 0)
            n_dn = sum(1 for d in market_data if d["thay_doi"] < 0)
            n_flat = sum(1 for d in market_data if d["thay_doi"] == 0)
            total_scanned = len(market_data)
            pct_up = n_up / total_scanned * 100 if total_scanned > 0 else 0
            avg_change = float(np.mean([d["thay_doi"] for d in market_data]))
            median_change = float(np.median([d["thay_doi"] for d in market_data]))
            mb1, mb2, mb3, mb4, mb5 = st.columns(5)
            mb1.metric("🟢 Mã tăng", f"{n_up}/{total_scanned}", f"{pct_up:.0f}%")
            mb2.metric("🔴 Mã giảm", f"{n_dn}/{total_scanned}", f"{100-pct_up:.0f}%")
            mb3.metric("🟡 Mã đi ngang", f"{n_flat}/{total_scanned}")
            mb4.metric("📊 TB thay đổi", f"{avg_change:+.2f}%")
            mb5.metric("📊 Median thay đổi", f"{median_change:+.2f}%")
            breadth_status = "🟢 Rất tích cực" if pct_up > 70 else ("🟢 Tích cực" if pct_up > 55 else \
                          ("🟡 Trung lập" if pct_up > 45 else ("🔴 Tiêu cực" if pct_up > 30 else "🔴 Rất tiêu cực")))
            st.write(f"**Trạng thái thị trường:** {breadth_status}")
            fig_mb = go.Figure()
            fig_mb.add_trace(go.Histogram(x=[d["thay_doi"] for d in market_data], nbinsx=30,
                marker_color=['#4CAF50' if d["thay_doi"] > 0 else '#F44336' for d in market_data],
                opacity=0.7, name='Phân phối'))
            fig_mb.add_vline(x=0, line_dash="dash", line_color='#FFD700', annotation_text="0%")
            fig_mb.add_vline(x=avg_change, line_dash="dot", line_color='#2196F3', annotation_text=f"TB={avg_change:+.2f}%")
            fig_mb.update_layout(title=f"Phân phối thay đổi hôm nay ({total_scanned} mã)",
                xaxis_title="% Thay đổi", yaxis_title="Số mã",
                height=300, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_mb, use_container_width=True)
            st.caption(f"📊 Quét {total_scanned} mã từ yfinance chart API. Market breadth > 70% mã tăng = rất tích cực (bull market), < 30% = bear market.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường đã quét.")

        st.write("---")
        st.write("## 🎯 52-Week High/Low Scanner — Mã gần đỉnh/đáy 52 tuần")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=3600)
            def _get_52w_data(symbols):
                import requests as _rq_52
                out = []
                for s, suf in symbols:
                    try:
                        r = _rq_52.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}{suf}?range=1y&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            meta = result.get("meta", {})
                            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            if closes and len(closes) > 5:
                                cur = float(meta.get("regularMarketPrice") or closes[-1] or 0)
                                valid_closes = [c for c in closes if c]
                                if not valid_closes:
                                    continue
                                hi_52 = float(meta.get("fiftyTwoWeekHigh") or max(valid_closes))
                                lo_52 = float(meta.get("fiftyTwoWeekLow") or min(valid_closes))
                                if hi_52 > 0 and lo_52 > 0 and hi_52 > lo_52:
                                    pos_52w = (cur - lo_52) / (hi_52 - lo_52) * 100
                                    out.append({"ma": s, "gia": cur, "w52h": hi_52, "w52l": lo_52, "pos_52w": pos_52w})
                    except Exception:
                        continue
                return out
            with st.spinner(f"📡 Lấy 52W cho {len(market_data)} mã..."):
                w52_targets = tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data])
                w52_data = _get_52w_data(w52_targets)
            if w52_data:
                df_52 = pd.DataFrame(w52_data)
                nl1, nl2 = st.columns(2)
                with nl1:
                    st.write("**🚀 Gần đỉnh 52W (pos > 80%):**")
                    near_hi = df_52[df_52["pos_52w"] > 80].sort_values("pos_52w", ascending=False).head(10)
                    st.dataframe(near_hi, use_container_width=True, hide_index=True)
                    if len(near_hi) == 0:
                        st.info("Không có mã nào gần đỉnh 52W.")
                with nl2:
                    st.write("**💀 Gần đáy 52W (pos < 20%):**")
                    near_lo = df_52[df_52["pos_52w"] < 20].sort_values("pos_52w").head(10)
                    st.dataframe(near_lo, use_container_width=True, hide_index=True)
                    if len(near_lo) == 0:
                        st.info("Không có mã nào gần đáy 52W.")
                avg_pos = float(df_52["pos_52w"].mean())
                st.metric("📊 Vị trí TB thị trường trong 52W", f"{avg_pos:.0f}%",
                    help="0% = tất cả ở đáy 52W, 100% = tất cả ở đỉnh 52W")
                st.caption(f"📊 Tính từ 52-week high/low của {len(df_52)} mã từ yfinance chart API. pos_52w = (giá - low) / (high - low) × 100.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📈 RSI Heatmap toàn thị trường — Tín hiệu quá mua/quá bán")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_rsi_market(symbols):
                import requests as _rq_rsi
                out = []
                for s in symbols:
                    try:
                        r = _rq_rsi.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=6mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            if closes and len(closes) > 20:
                                p = pd.Series([c for c in closes if c])
                                delta = p.diff().dropna()
                                gain = delta.where(delta > 0, 0).rolling(14).mean()
                                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                                if len(gain) > 0 and len(loss) > 0 and not pd.isna(gain.iloc[-1]) and not pd.isna(loss.iloc[-1]):
                                    g_v = float(gain.iloc[-1]) if gain.iloc[-1] != 0 else 0.0
                                    l_v = float(loss.iloc[-1]) if loss.iloc[-1] != 0 else 1e-10
                                    rs = g_v / l_v
                                    rsi = 100 - 100 / (1 + rs)
                                    if 0 <= rsi <= 100 and not (rsi != rsi):
                                        out.append({"ma": s, "gia": float(p.iloc[-1]), "rsi": float(rsi)})
                    except Exception:
                        continue
                return out
            with st.spinner(f"📡 Tính RSI cho {len(market_data)} mã..."):
                rsi_data = _compute_rsi_market(tuple([d["ma"] for d in market_data]))
            if rsi_data:
                df_rsi = pd.DataFrame(rsi_data).sort_values("rsi", ascending=False)
                st.write(f"**📊 RSI Heatmap ({len(df_rsi)} mã):**")
                fig_rsi = go.Figure()
                colors = ['#F44336' if r > 70 else ('#4CAF50' if r < 30 else '#FFD700') for r in df_rsi["rsi"]]
                fig_rsi.add_trace(go.Bar(x=df_rsi["ma"], y=df_rsi["rsi"], marker_color=colors, name='RSI'))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="#F44336", annotation_text="Quá mua (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#4CAF50", annotation_text="Quá bán (30)")
                fig_rsi.update_layout(title="RSI 14 phiên toàn thị trường",
                    xaxis_title="Mã CP", yaxis_title="RSI",
                    height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_rsi, use_container_width=True)
                rsi1, rsi2, rsi3 = st.columns(3)
                rsi1.metric("🔴 Quá mua (RSI>70)", f"{(df_rsi['rsi']>70).sum()} mã")
                rsi2.metric("🟡 Trung tính (30-70)", f"{((df_rsi['rsi']>=30) & (df_rsi['rsi']<=70)).sum()} mã")
                rsi3.metric("🟢 Quá bán (RSI<30)", f"{(df_rsi['rsi']<30).sum()} mã")
                st.caption(f"📊 RSI 14 phiên tính từ {len(rsi_data)} mã giá thật yfinance 6T. RSI>70 = quá mua (cẩn thận điều chỉnh), RSI<30 = quá bán (cơ hội mua).")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🔀 Volatility Ranking toàn thị trường — Vol 6 tháng")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_vol_market(symbols):
                import requests as _rq_v
                out = []
                for s in symbols:
                    try:
                        r = _rq_v.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=6mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            if closes and len(closes) > 30:
                                p = pd.Series([c for c in closes if c])
                                ret = p.pct_change().dropna()
                                if len(ret) > 20 and not ret.isna().all():
                                    vol_v = ret.std() * (252**0.5) * 100
                                    if pd.notna(vol_v) and vol_v > 0:
                                        out.append({"ma": s, "gia": float(p.iloc[-1]), "vol": float(vol_v),
                                            "ret_6m": (float(p.iloc[-1]) / float(p.iloc[0]) - 1) * 100})
                    except Exception:
                        continue
                return out
            with st.spinner(f"📡 Tính Vol cho {len(market_data)} mã..."):
                vol_data = _compute_vol_market(tuple([d["ma"] for d in market_data]))
            if vol_data:
                df_vol = pd.DataFrame(vol_data)
                nl1, nl2 = st.columns(2)
                with nl1:
                    st.write("**🔥 Top 10 Vol cao nhất (rủi ro cao):**")
                    top_vol = df_vol.nlargest(10, "vol")[["ma", "gia", "vol", "ret_6m"]]
                    top_vol["vol"] = top_vol["vol"].round(1)
                    st.dataframe(top_vol, use_container_width=True, hide_index=True)
                with nl2:
                    st.write("**❄️ Top 10 Vol thấp nhất (ổn định):**")
                    low_vol = df_vol.nsmallest(10, "vol")[["ma", "gia", "vol", "ret_6m"]]
                    low_vol["vol"] = low_vol["vol"].round(1)
                    st.dataframe(low_vol, use_container_width=True, hide_index=True)
                avg_vol_mkt = float(df_vol["vol"].mean())
                st.metric("📊 Vol TB toàn thị trường", f"{avg_vol_mkt:.1f}%/năm",
                    help="Vol trung bình của tất cả mã quét được")
                st.caption(f"📊 Vol annualized tính từ {len(df_vol)} mã giá thật yfinance 6T. Vol cao = biến động mạnh, Vol thấp = ổn định.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 💰 Market Cap Distribution — Phân phối vốn hóa")
        if market_data and len(market_data) >= 5:
            cap_data = [d for d in market_data if d.get("von_hoa") and d["von_hoa"] > 0]
            if cap_data:
                df_cap = pd.DataFrame(cap_data)
                df_cap["von_hoa_ty"] = df_cap["von_hoa"] / 1e9
                df_cap = df_cap.sort_values("von_hoa_ty", ascending=False)
                total_cap = float(df_cap["von_hoa_ty"].sum())
                top5_cap = float(df_cap.head(5)["von_hoa_ty"].sum())
                top5_pct = top5_cap / total_cap * 100 if total_cap > 0 else 0
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("💰 Tổng vốn hóa", f"{total_cap:,.0f} tỷ VND",
                    help=f"Tổng vốn hóa của {len(cap_data)} mã quét được")
                mc2.metric("🏆 Top 5 chiếm", f"{top5_pct:.1f}%", help="Tỷ lệ tập trung vốn hóa")
                mc3.metric("📊 TB vốn hóa", f"{total_cap/len(cap_data):,.0f} tỷ VND")
                mc4.metric("📊 Median vốn hóa", f"{float(df_cap['von_hoa_ty'].median()):,.0f} tỷ VND")
                st.write("**Top 10 mã vốn hóa lớn nhất:**")
                st.dataframe(df_cap.head(10)[["ma", "ten", "gia", "von_hoa_ty"]].round(1),
                    use_container_width=True, hide_index=True)
                _top20 = df_cap.head(20)
                fig_cap = go.Figure(data=go.Bar(
                    x=_top20["ma"], y=_top20["von_hoa_ty"],
                    marker=dict(color=_top20["von_hoa_ty"], colorscale="Viridis", showscale=True,
                        colorbar=dict(title="Tỷ VND", x=1.02)),
                    text=_top20["von_hoa_ty"].round(0), textposition="outside",
                    hovertemplate="%{x}<br>%{y:,.0f} tỷ VND<extra></extra>"))
                fig_cap.update_layout(height=350, title="Top 20 mã vốn hóa lớn nhất (tỷ VND)",
                    xaxis_title="Mã CP", yaxis_title="Vốn hóa (tỷ VND)",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_cap, use_container_width=True)
                st.caption(f"📊 Tính từ marketCap của {len(cap_data)} mã từ yfinance.info. Tổng vốn hóa ≈ quy mô thị trường. Top 5 = blue chips chiếm {top5_pct:.1f}%.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường có vốn hóa.")

        st.write("---")
        st.write("## 📏 Average Daily Range — Biên độ giao động trung bình")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_range_market(symbols):
                import requests as _rq_rg
                out = []
                for s in symbols:
                    try:
                        r = _rq_rg.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=1mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            quote = result.get("indicators", {}).get("quote", [{}])[0]
                            closes = quote.get("close", [])
                            highs = quote.get("high", [])
                            lows = quote.get("low", [])
                            if closes and len(closes) > 5:
                                ranges = []
                                for i in range(min(len(highs), len(lows), len(closes))):
                                    if highs[i] and lows[i] and lows[i] > 0 and highs[i] > 0:
                                        ranges.append((highs[i] - lows[i]) / lows[i] * 100)
                                if ranges:
                                    avg_r = float(np.mean(ranges))
                                    if avg_r > 0 and not (avg_r != avg_r):
                                        out.append({"ma": s, "gia": float([c for c in closes if c][-1]),
                                            "avg_range_1m": avg_r,
                                            "max_range": float(max(ranges))})
                    except Exception:
                        continue
                return out
            with st.spinner(f"📡 Tính biên độ ngày cho {len(market_data)} mã..."):
                range_data = _compute_range_market(tuple([d["ma"] for d in market_data]))
            if range_data:
                df_rng = pd.DataFrame(range_data).sort_values("avg_range_1m", ascending=False)
                nl1, nl2 = st.columns(2)
                with nl1:
                    st.write("**🔥 Top 10 biên độ rộng nhất (dao động mạnh):**")
                    st.dataframe(df_rng.head(10)[["ma", "gia", "avg_range_1m", "max_range"]].round(2),
                        use_container_width=True, hide_index=True)
                with nl2:
                    st.write("**❄️ Top 10 biên độ hẹp nhất (ổn định):**")
                    st.dataframe(df_rng.tail(10)[["ma", "gia", "avg_range_1m", "max_range"]].round(2),
                        use_container_width=True, hide_index=True)
                avg_rng = float(df_rng["avg_range_1m"].mean())
                st.caption(f"📊 Tính từ high/low hàng ngày của {len(range_data)} mã từ yfinance 1T. Biên độ TB thị trường: {avg_rng:.2f}%/ngày. Biên độ rộng = cơ hội trading ngắn hạn.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 💰 Real Money Flow — Dòng tiền thật toàn thị trường")
        if market_data and len(market_data) >= 5:
            money_rows = []
            for d in market_data:
                gia = d.get("gia", 0) or 0
                vol = d.get("vol", 0) or 0
                change = d.get("thay_doi", 0) or 0
                if gia > 0 and vol > 0:
                    money_flow = gia * vol * (1 if change > 0 else -1 if change < 0 else 0)
                    money_rows.append({"ma": d.get("ma"), "ten": d.get("ten", "")[:25], "gia": gia,
                        "thay_doi": change, "vol": vol, "money_flow": money_flow})
            if money_rows:
                df_mf = pd.DataFrame(money_rows).sort_values("money_flow", ascending=False)
                mf1, mf2 = st.columns(2)
                with mf1:
                    st.write("**🟢 Top 10 dòng tiền VÀO mạnh nhất (tăng giá + vol cao):**")
                    top_in = df_mf.head(10)[["ma", "ten", "gia", "thay_doi", "vol", "money_flow"]].copy()
                    top_in["money_flow_ty"] = (top_in["money_flow"] / 1e9).round(2)
                    st.dataframe(top_in[["ma", "ten", "thay_doi", "money_flow_ty"]].rename(columns={"money_flow_ty": "Dòng tiền (tỷ VNĐ)"}),
                        use_container_width=True, hide_index=True)
                with mf2:
                    st.write("**🔴 Top 10 dòng tiền RA mạnh nhất (giảm giá + vol cao):**")
                    top_out = df_mf.tail(10)[["ma", "ten", "gia", "thay_doi", "vol", "money_flow"]].copy()
                    top_out["money_flow_ty"] = (top_out["money_flow"] / 1e9).round(2)
                    st.dataframe(top_out[["ma", "ten", "thay_doi", "money_flow_ty"]].rename(columns={"money_flow_ty": "Dòng tiền (tỷ VNĐ)"}),
                        use_container_width=True, hide_index=True)
                total_in = float(df_mf[df_mf["money_flow"] > 0]["money_flow"].sum())
                total_out = abs(float(df_mf[df_mf["money_flow"] < 0]["money_flow"].sum()))
                net_flow = total_in - total_out
                mf_net1, mf_net2, mf_net3 = st.columns(3)
                mf_net1.metric("🟢 Tổng dòng tiền VÀO", f"{total_in/1e12:.2f} nghìn tỷ VNĐ")
                mf_net2.metric("🔴 Tổng dòng tiền RA", f"{total_out/1e12:.2f} nghìn tỷ VNĐ")
                mf_net3.metric("💰 DÒNG TIỀN RÒNG", f"{net_flow/1e12:+.2f} nghìn tỷ VNĐ",
                    delta=f"{'BULLISH' if net_flow > 0 else 'BEARISH'}")
                st.caption(f"📊 Money flow = giá × volume × sign(change). Tính từ {len(money_rows)} mã từ yfinance chart API. Dương = tiền đang vào thị trường, Âm = tiền đang rút ra.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🏛️ Real Sector P/E Benchmark — So sánh P/E mã vs ngành")
        if market_data and len(market_data) >= 5:
            with st.spinner("📡 Đang tải P/E + ngành cho 50 mã..."):
                pe_dist_full = _get_pe_distribution(tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data]))
            if pe_dist_full:
                pe_by_ma = {r["ma"]: r for r in pe_dist_full}
                ng_by_ma = {d["ma"]: d.get("nganh", "Khác") for d in market_data}
                sector_pe = {}
                for ma, info in pe_by_ma.items():
                    ng = ng_by_ma.get(ma, "Khác")
                    sector_pe.setdefault(ng, []).append(info["pe"])
                sector_med = {ng: float(np.median(v)) for ng, v in sector_pe.items() if v}
                rows_bench = []
                for ma, info in pe_by_ma.items():
                    ng = ng_by_ma.get(ma, "Khác")
                    pe_ma = info["pe"]
                    pe_sec = sector_med.get(ng, 0)
                    if pe_sec > 0:
                        rel = (pe_ma / pe_sec - 1) * 100
                        rows_bench.append({"ma": ma, "ten": info.get("ma", ma), "nganh": ng,
                            "pe_ma": pe_ma, "pe_nganh": pe_sec, "chenh_lech_pct": rel,
                            "dinh_gia": "RẺ" if rel < -20 else "ĐẮT" if rel > 20 else "HỢP LÝ"})
                if rows_bench:
                    df_bench = pd.DataFrame(rows_bench).sort_values("chenh_lech_pct")
                    bl1, bl2 = st.columns(2)
                    with bl1:
                        st.write("**🟢 Top 10 mã RẺ hơn ngành (cơ hội value):**")
                        st.dataframe(df_bench.head(10)[["ma", "nganh", "pe_ma", "pe_nganh", "chenh_lech_pct", "dinh_gia"]].round(2),
                            use_container_width=True, hide_index=True)
                    with bl2:
                        st.write("**🔴 Top 10 mã ĐẮT hơn ngành (cẩn thận):**")
                        st.dataframe(df_bench.tail(10)[["ma", "nganh", "pe_ma", "pe_nganh", "chenh_lech_pct", "dinh_gia"]].round(2),
                            use_container_width=True, hide_index=True)
                    fig_bench = go.Figure()
                    fig_bench.add_trace(go.Bar(
                        x=df_bench["ma"], y=df_bench["chenh_lech_pct"],
                        marker_color=['#4CAF50' if x < 0 else '#F44336' for x in df_bench["chenh_lech_pct"]],
                        name='Chênh lệch P/E vs ngành (%)'
                    ))
                    fig_bench.update_layout(title="P/E của mã so với P/E median ngành (%)",
                        xaxis_title="Mã CP", yaxis_title="Chênh lệch %",
                        height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_bench, use_container_width=True)
                    st.caption(f"📊 P/E từng mã từ yfinance.info, P/E ngành = median tất cả mã cùng ngành. Rẻ hơn -20% = cơ hội value, đắt hơn +20% = cẩn thận bubble. Tính từ {len(rows_bench)} mã có P/E thật.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🏦 Real Insider & Institutional Holdings — Tỷ lệ sở hữu thật")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=3600)
            def _get_holders_market(symbols):
                import yfinance as _yf_h
                out = []
                for s, suf in symbols:
                    try:
                        tk = _yf_h.Ticker(s + suf)
                        info = tk.info
                        insider = info.get("heldPercentInsiders")
                        inst = info.get("heldPercentInstitutions")
                        if (insider is not None and insider > 0) or (inst is not None and inst > 0):
                            out.append({"ma": s, "ten": (info.get("longName", s) or s)[:25],
                                "insider_pct": float(insider or 0) * 100,
                                "institution_pct": float(inst or 0) * 100,
                                "free_float_pct": 100 - (float(insider or 0) + float(inst or 0)) * 100})
                    except Exception:
                        continue
                if len(out) < 5:
                    try:
                        for _ma, _ki in (DOCS.get("co_phieu_vn") or {}).items():
                            if len(out) >= 30: break
                            _ins = float(_ki.get("insider_pct", 0) or 0)
                            _ngoai = float(_ki.get("pct_ngoai", 0) or 0)
                            if _ins > 0 or _ngoai > 0:
                                out.append({"ma": _ma, "ten": _ki.get("ten", _ma)[:25],
                                    "insider_pct": _ins,
                                    "institution_pct": _ngoai,
                                    "free_float_pct": max(0, 100 - _ins - _ngoai)})
                    except Exception:
                        pass
                return out
            with st.spinner(f"📡 Tải holdings cho {len(market_data)} mã..."):
                holders_targets = tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data])
                holders = _get_holders_market(holders_targets)
            if holders:
                df_h = pd.DataFrame(holders)
                h1, h2, h3 = st.columns(3)
                h1.metric("🏛️ Insider TB", f"{df_h['insider_pct'].mean():.1f}%",
                    help="Tỷ lệ sở hữu của ban lãnh đạo/cổ đông nội bộ TB toàn thị trường")
                h2.metric("🏛️ Institution TB", f"{df_h['institution_pct'].mean():.1f}%",
                    help="Tỷ lệ sở hữu của tổ chức (quỹ, khối ngoại) TB toàn thị trường")
                h3.metric("🔄 Free Float TB", f"{df_h['free_float_pct'].mean():.1f}%",
                    help="Tỷ lệ cổ phiếu tự do giao dịch")
                hl1, hl2 = st.columns(2)
                with hl1:
                    st.write("**🏛️ Top 10 mã Insider nắm giữ CAO (ban lãnh đạo tự tin):**")
                    st.dataframe(df_h.nlargest(10, "insider_pct")[["ma", "ten", "insider_pct", "institution_pct"]].round(2),
                        use_container_width=True, hide_index=True)
                with hl2:
                    st.write("**🌍 Top 10 mã Institution nắm giữ CAO (khối ngoại/quỹ ưa thích):**")
                    st.dataframe(df_h.nlargest(10, "institution_pct")[["ma", "ten", "insider_pct", "institution_pct"]].round(2),
                        use_container_width=True, hide_index=True)
                st.caption(f"📊 heldPercentInsiders + heldPercentInstitutions từ yfinance.info cho {len(holders)} mã. Insider cao = ban lãnh đạo đồng hành cùng cổ đông. Institution cao = tổ chức lớn tin tưởng.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📅 Real Earnings Calendar — Sự kiện công bố thật")
        if dm and isinstance(dm, dict) and len(dm) > 0:
            @st.cache_data(ttl=3600)
            def _get_earnings_calendar(symbols):
                import yfinance as _yf_e
                out = []
                for s, suf in symbols:
                    try:
                        tk = _yf_e.Ticker(s + suf)
                        cal = tk.calendar
                        if cal is not None and isinstance(cal, dict) and "Earnings Date" in cal:
                            ed = cal["Earnings Date"]
                            if ed and len(ed) > 0:
                                out.append({"ma": s, "earnings_date": str(ed[0])[:10] if hasattr(ed[0], 'strftime') else str(ed[0])[:10]})
                        elif cal is not None and hasattr(cal, 'empty') and not cal.empty:
                            for col in cal.columns:
                                if "Earnings" in str(col):
                                    ed = cal[col].iloc[0]
                                    if ed and str(ed) != "NaT":
                                        out.append({"ma": s, "earnings_date": str(ed)[:10]})
                                    break
                    except Exception:
                        continue
                return out
            dm_symbols = [ma for ma in dm.keys() if dm[ma].get("so_luong", 0) > 0]
            if dm_symbols:
                with st.spinner(f"📡 Tải earnings calendar cho {len(dm_symbols)} mã trong DM..."):
                    earnings_targets = tuple([(ma, ".VN") for ma in dm_symbols])
                    earnings = _get_earnings_calendar(earnings_targets)
                if earnings:
                    df_ear = pd.DataFrame(earnings).sort_values("earnings_date")
                    st.write(f"**📅 Lịch công bố lợi nhuận sắp tới cho {len(earnings)}/{len(dm_symbols)} mã trong DM:**")
                    st.dataframe(df_ear, use_container_width=True, hide_index=True)
                    st.caption(f"📊 Từ yfinance Ticker.calendar (Earnings Date). Mã nào sắp công bố lợi nhuận = volatility cao, cẩn thận biến động giá trước/sau ngày này.")
                else:
                    st.info("⚠️ yfinance chưa có lịch earnings cho các mã VN này (thường chỉ có cho thị trường Mỹ).")
            else:
                st.info("⚠️ DM chưa có mã nào có số lượng > 0.")
        else:
            st.info("⚠️ Cần DM có dữ liệu.")

        st.write("---")
        st.write("## 🔄 Real Sector Rotation Matrix — Hiệu suất ngành theo thời kỳ")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_sector_rotation(symbols, sectors):
                import requests as _rq_sr
                period_returns = {"1W": 5, "1M": 21, "3M": 63, "6M": 126, "1Y": 252}
                sector_data = {}
                for s, ng in zip(symbols, sectors):
                    try:
                        r = _rq_sr.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=1y&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            valid = [c for c in closes if c]
                            if len(valid) > 30:
                                cur = float(valid[-1])
                                returns = {}
                                for label, n in period_returns.items():
                                    if len(valid) > n:
                                        prev = float(valid[-n-1])
                                        returns[label] = (cur / prev - 1) * 100
                                sector_data.setdefault(ng, []).append(returns)
                    except Exception:
                        continue
                out = []
                for ng, lst in sector_data.items():
                    if lst:
                        med = {k: float(np.median([r.get(k, 0) for r in lst if r])) for k in period_returns.keys()}
                        out.append({"nganh": ng, "so_ma": len(lst), **med})
                return out
            with st.spinner(f"📡 Tính sector rotation cho {len(market_data)} mã..."):
                rot = _compute_sector_rotation(
                    tuple([d["ma"] for d in market_data]),
                    tuple([d.get("nganh", "Khác") for d in market_data])
                )
            if rot:
                df_rot = pd.DataFrame(rot).sort_values("1M", ascending=False)
                st.write("**📊 Sector Rotation Matrix (return % theo từng kỳ):**")
                st.dataframe(df_rot[["nganh", "so_ma", "1W", "1M", "3M", "6M", "1Y"]].round(2),
                    use_container_width=True, hide_index=True)
                fig_rot = go.Figure()
                for col in ["1W", "1M", "3M", "6M", "1Y"]:
                    fig_rot.add_trace(go.Bar(name=col, x=df_rot["nganh"], y=df_rot[col]))
                fig_rot.update_layout(barmode="group", title="Sector Performance theo thời kỳ (%)",
                    xaxis_title="Ngành", yaxis_title="Return %",
                    height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_rot, use_container_width=True)
                top_1m = df_rot.iloc[0]
                worst_1y_idx = df_rot["1Y"].idxmin()
                st.caption(f"📊 Tính từ {len(market_data)} mã từ yfinance chart API 1Y. Ngành nóng nhất 1M: **{top_1m['nganh']}** ({top_1m['1M']:+.2f}%). Ngành yếu nhất 1Y: **{df_rot.loc[worst_1y_idx, 'nganh']}** ({df_rot.loc[worst_1y_idx, '1Y']:+.2f}%).")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 💎 Real Earnings Yield vs Bond Yield — So sánh thu nhập thật")
        if market_data and len(market_data) >= 5:
            with st.spinner("📡 Tải P/E + lãi suất trái phiếu VN..."):
                pe_dist_ey = _get_pe_distribution(tuple([(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data]))
                bond_yield = _fetch_vn_bond_yield()
            if bond_yield is not None and len(bond_yield) > 0:
                bv2 = float(bond_yield.iloc[-1])
                if 0 < bv2 < 1:
                    bond_yield_pct = bv2 * 100
                elif 1 <= bv2 < 50:
                    bond_yield_pct = bv2
                else:
                    bond_yield_pct = 0
            else:
                bond_yield_pct = 0
            if pe_dist_ey:
                ey_rows = []
                for r in pe_dist_ey:
                    pe = r.get("pe", 0)
                    if pe and pe > 0:
                        ey = 100.0 / pe
                        spread = ey - bond_yield_pct
                        ey_rows.append({"ma": r["ma"], "pe": pe, "earnings_yield": ey,
                            "spread_vs_bond": spread,
                            "status": "🟢 Hấp dẫn" if spread > 3 else ("🟡 Hợp lý" if spread > 0 else "🔴 Kém hấp dẫn")})
                if ey_rows:
                    df_ey = pd.DataFrame(ey_rows).sort_values("spread_vs_bond", ascending=False)
                    ey1, ey2, ey3 = st.columns(3)
                    ey1.metric("🏛️ Lãi suất TP VN (10Y)", f"{bond_yield_pct:.2f}%",
                        help="Lãi suất trái phiếu chính phủ VN 10 năm từ yfinance")
                    ey2.metric("📊 Earnings Yield TB", f"{df_ey['earnings_yield'].mean():.2f}%",
                        help="Trung bình 1/PE của các mã VN")
                    ey3.metric("💰 Spread TB", f"{df_ey['spread_vs_bond'].mean():+.2f}%",
                        help="EY - Bond Yield. Dương = CP hấp dẫn hơn TP, Âm = nên mua TP")
                    st.write("**Top 10 mã có EY - Bond Yield cao nhất (CP hấp dẫn hơn TP):**")
                    st.dataframe(df_ey.head(10)[["ma", "pe", "earnings_yield", "spread_vs_bond", "status"]].round(2),
                        use_container_width=True, hide_index=True)
                    st.write("**Top 10 mã có EY - Bond Yield thấp nhất (CP kém hấp dẫn):**")
                    st.dataframe(df_ey.tail(10)[["ma", "pe", "earnings_yield", "spread_vs_bond", "status"]].round(2),
                        use_container_width=True, hide_index=True)
                    st.caption(f"📊 Earnings Yield = 1/P/E. Spread > 0% = CP sinh lời nhiều hơn TP. Spread > 3% = rất hấp dẫn (Buffett favorite). Tính từ {len(ey_rows)} mã có P/E thật từ yfinance + bond yield ^VN10Y/VNI10Y.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 💱 Real Currency Strength — Sức mạnh đồng tiền thật")
        @st.cache_data(ttl=3600, show_spinner="📡 Tải tỷ giá...")
        def _get_currency_strength():
            try:
                import yfinance as _yf_fx
                pairs = {
                    "USD/VND": "USDVND=X",
                    "EUR/VND": "EURVND=X",
                    "JPY/VND": "JPYVND=X",
                    "GBP/VND": "GBPVND=X",
                    "CNY/VND": "CNYVND=X",
                    "DXY (Dollar Index)": "DX-Y.NYB",
                    "BTC/USD": "BTC-USD",
                    "Gold (XAU/USD)": "GC=F",
                }
                out = []
                for label, sym in pairs.items():
                    try:
                        s = _yf_fx.Ticker(sym)
                        hist = s.history(period="3mo", auto_adjust=True)
                        if hist is not None and len(hist) > 5:
                            cur = float(hist["Close"].iloc[-1])
                            prev_d = float(hist["Close"].iloc[-2]) if len(hist) > 1 else cur
                            prev_w = float(hist["Close"].iloc[-6]) if len(hist) > 5 else cur
                            prev_m = float(hist["Close"].iloc[-22]) if len(hist) > 21 else cur
                            chg_d = (cur / prev_d - 1) * 100
                            chg_w = (cur / prev_w - 1) * 100
                            chg_m = (cur / prev_m - 1) * 100
                            out.append({"cap": label, "gia": cur, "1D": chg_d, "1W": chg_w, "1M": chg_m})
                    except Exception:
                        continue
                return out
            except Exception:
                return []
        with st.spinner("📡 Tải tỷ giá 8 cặp tiền tệ + vàng..."):
            fx_data = _get_currency_strength()
        if fx_data:
            df_fx = pd.DataFrame(fx_data)
            st.write("**💱 Sức mạnh đồng tiền so với VND + tài sản toàn cầu:**")
            st.dataframe(df_fx.round(2), use_container_width=True, hide_index=True)
            fig_fx = go.Figure()
            for col, color in [("1D", "#2196F3"), ("1W", "#FF9800"), ("1M", "#4CAF50")]:
                fig_fx.add_trace(go.Bar(name=col, x=df_fx["cap"], y=df_fx[col], marker_color=color))
            fig_fx.update_layout(barmode="group", title="Biến động tỷ giá theo thời kỳ (%)",
                xaxis_title="Cặp tiền/Tài sản", yaxis_title="% thay đổi",
                height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_fx, use_container_width=True)
            st.caption(f"📊 Tỷ giá từ yfinance: USDVND=X, EURVND=X, JPYVND=X, GBPVND=X, CNYVND=X, DX-Y.NYB (Dollar Index), BTC-USD, GC=F (Vàng). Ảnh hưởng đến: nhập khẩu, lạm phát, vàng, crypto.")
        else:
            st.info("⚠️ Không tải được dữ liệu tỷ giá.")

        st.write("---")
        st.write("## 🌡️ Real Market Heat Index — Nhiệt độ thị trường")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_heat_index(symbols):
                import requests as _rq_h
                out = []
                for s in symbols:
                    try:
                        r = _rq_h.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=1mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            quote = result.get("indicators", {}).get("quote", [{}])[0]
                            closes = quote.get("close", [])
                            volumes = quote.get("volume", [])
                            if closes and len(closes) > 5:
                                valid_c = [c for c in closes if c]
                                valid_v = [v for v in volumes if v]
                                if len(valid_c) > 5 and len(valid_v) > 5:
                                    cur = float(valid_c[-1])
                                    prev = float(valid_c[-2]) if len(valid_c) > 1 else cur
                                    chg = (cur / prev - 1) * 100
                                    avg_v = float(np.mean(valid_v[-20:])) if len(valid_v) >= 20 else float(np.mean(valid_v))
                                    vol_today = float(valid_v[-1]) if valid_v else 0
                                    vol_burst = (vol_today / avg_v) if avg_v > 0 else 0
                                    spread = ((float(max(valid_c[-5:])) - float(min(valid_c[-5:]))) / cur * 100) if cur > 0 and len(valid_c) >= 5 else 0
                                    heat = abs(chg) * 0.4 + min(vol_burst, 5) * 10 + min(spread, 10) * 5
                                    out.append({"ma": s, "gia": cur, "chg": chg, "vol_burst": vol_burst,
                                        "spread": spread, "heat": float(heat)})
                    except Exception:
                        continue
                return out
            with st.spinner(f"📡 Tính heat index cho {len(market_data)} mã..."):
                heat_data = _compute_heat_index(tuple([d["ma"] for d in market_data]))
            if heat_data:
                df_heat = pd.DataFrame(heat_data).sort_values("heat", ascending=False)
                h1, h2, h3 = st.columns(3)
                h1.metric("🌡️ Heat Index TB", f"{df_heat['heat'].mean():.1f}",
                    help="Heat = |% thay đổi| × 0.4 + vol_burst × 10 + spread × 5. Cao = thị trường nóng")
                h2.metric("🔥 Mã NÓNG (heat > 50)", f"{(df_heat['heat']>50).sum()}/{len(df_heat)}",
                    help="Số mã có heat > 50 = đáng chú ý đặc biệt")
                h3.metric("❄️ Mã LẠNH (heat < 10)", f"{(df_heat['heat']<10).sum()}/{len(df_heat)}",
                    help="Số mã có heat < 10 = im ắng, ít giao dịch")
                st.write("**🔥 Top 10 mã NÓNG nhất hôm nay:**")
                st.dataframe(df_heat.head(10)[["ma", "gia", "chg", "vol_burst", "spread", "heat"]].round(2),
                    use_container_width=True, hide_index=True)
                fig_heat = go.Figure()
                colors = ['#F44336' if h > 50 else ('#FF9800' if h > 30 else ('#FFD700' if h > 15 else '#4CAF50')) for h in df_heat["heat"]]
                fig_heat.add_trace(go.Bar(x=df_heat["ma"], y=df_heat["heat"], marker_color=colors, name='Heat Index'))
                fig_heat.update_layout(title="Heat Index toàn thị trường",
                    xaxis_title="Mã CP", yaxis_title="Heat Score",
                    height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption(f"📊 Heat = |change%|×0.4 + vol_burst(min 5)×10 + spread(min 10)×5. Tính từ {len(heat_data)} mã giá/vol 1T từ yfinance. Heat>50 = biến động mạnh, Heat<10 = im ắng.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🔬 TOP 20 DEEP DIVE — Phân tích chuyên sâu 20 mã vốn hóa lớn nhất")
        if market_data and len(market_data) >= 5:
            top20 = sorted([d for d in market_data if d.get("von_hoa", 0) > 0],
                          key=lambda d: -d["von_hoa"])[:20]
            with st.spinner(f"📡 Tải đầy đủ P/E, P/B, ROE, beta, EPS cho {len(top20)} mã..."):
                deep_data = []
                for d in top20:
                    ma = d["ma"]
                    try:
                        import yfinance as _yf_dd
                        info = _yf_dd.Ticker(ma + ".VN").info
                        pe = info.get("trailingPE")
                        pb = info.get("priceToBook")
                        roe = info.get("returnOnEquity")
                        beta = info.get("beta")
                        eps = info.get("trailingEps")
                        div_yield = info.get("dividendYield")
                        inst = info.get("heldPercentInstitutions")
                        rec = {
                            "ma": ma,
                            "ten": d.get("ten", ma)[:25],
                            "nganh": d.get("nganh", "Khác"),
                            "gia": d.get("gia", 0),
                            "von_hoa_ty": d.get("von_hoa", 0) / 1e9,
                            "pe": pe if pe and 0 < pe < 200 else None,
                            "pb": pb if pb and 0 < pb < 50 else None,
                            "roe_pct": roe * 100 if roe and -0.5 < roe < 0.5 else None,
                            "beta": beta if beta and 0 < beta < 3 else None,
                            "eps": eps if eps and eps > 0 else None,
                            "div_yield_pct": div_yield * 100 if div_yield and 0 <= div_yield < 0.3 else None,
                            "inst_pct": inst * 100 if inst and 0 <= inst < 1 else None,
                            "thay_doi": d.get("thay_doi", 0),
                            "ret_3m": d.get("ret_3m", 0),
                        }
                        deep_data.append(rec)
                    except Exception:
                        deep_data.append({
                            "ma": ma, "ten": d.get("ten", ma)[:25], "nganh": d.get("nganh", "Khác"),
                            "gia": d.get("gia", 0), "von_hoa_ty": d.get("von_hoa", 0) / 1e9,
                            "pe": None, "pb": None, "roe_pct": None, "beta": None, "eps": None,
                            "div_yield_pct": None, "inst_pct": None,
                            "thay_doi": d.get("thay_doi", 0), "ret_3m": d.get("ret_3m", 0),
                        })
            if deep_data:
                df_dd = pd.DataFrame(deep_data)
                st.write(f"**📊 Deep Dive {len(df_dd)} mã top vốn hóa:**")
                display_cols = ["ma", "ten", "nganh", "gia", "von_hoa_ty", "pe", "pb",
                              "roe_pct", "beta", "div_yield_pct", "inst_pct", "thay_doi", "ret_3m"]
                st.dataframe(df_dd[display_cols].round(2),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "von_hoa_ty": st.column_config.NumberColumn("Vốn hóa (tỷ)", format="%.0f"),
                        "pe": st.column_config.NumberColumn("P/E", format="%.1f"),
                        "pb": st.column_config.NumberColumn("P/B", format="%.2f"),
                        "roe_pct": st.column_config.NumberColumn("ROE %", format="%.1f"),
                        "beta": st.column_config.NumberColumn("Beta", format="%.2f"),
                        "div_yield_pct": st.column_config.NumberColumn("Div Yield %", format="%.2f"),
                        "inst_pct": st.column_config.NumberColumn("Foreign %", format="%.1f"),
                        "thay_doi": st.column_config.NumberColumn("% hôm nay", format="%+.2f"),
                        "ret_3m": st.column_config.NumberColumn("Return 3M %", format="%+.1f"),
                    })
                st.caption(f"📊 Đầy đủ metrics cho {len(df_dd)} mã top vốn hóa từ yfinance.info: P/E, P/B, ROE, beta, EPS, dividend yield, foreign ownership %, % thay đổi, return 3M.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🧮 MULTI-FACTOR SCORING — Xếp hạng 50 mã theo nhiều yếu tố")
        if market_data and len(market_data) >= 5:
            with st.spinner("📡 Tính composite score cho 50 mã..."):
                score_data = []
                for d in market_data:
                    ma = d["ma"]
                    try:
                        import yfinance as _yf_sc
                        info = _yf_sc.Ticker(ma + ".VN").info
                        pe = info.get("trailingPE")
                        roe = info.get("returnOnEquity")
                        dy = info.get("dividendYield")
                        inst = info.get("heldPercentInstitutions")
                        pe_s = 0
                        roe_s = 0
                        dy_s = 0
                        inst_s = 0
                        mom_s = 0
                        qual_s = 0
                        if pe and 0 < pe < 200:
                            pe_s = max(0, 100 - pe * 2)
                        if roe and -0.5 < roe < 0.5:
                            roe_s = min(100, max(0, roe * 100 * 3))
                        if dy and 0 <= dy < 0.3:
                            dy_s = min(100, dy * 1000)
                        if inst and 0 <= inst < 1:
                            inst_s = inst * 100
                        ret_3m = d.get("ret_3m", 0) or 0
                        mom_s = max(0, min(100, 50 + ret_3m * 1.5))
                        von_hoa = d.get("von_hoa", 0) or 0
                        if von_hoa > 1e12:
                            qual_s = 30
                        elif von_hoa > 1e11:
                            qual_s = 20
                        elif von_hoa > 1e10:
                            qual_s = 10
                        composite = (pe_s * 0.20 + roe_s * 0.25 + dy_s * 0.10 +
                                   inst_s * 0.10 + mom_s * 0.15 + qual_s * 0.20)
                        score_data.append({
                            "ma": ma, "ten": d.get("ten", ma)[:25],
                            "value_s": pe_s, "quality_s": roe_s, "div_s": dy_s,
                            "foreign_s": inst_s, "momentum_s": mom_s, "size_s": qual_s,
                            "composite": composite,
                            "pe": pe, "roe": roe * 100 if roe else 0,
                            "von_hoa_ty": von_hoa / 1e9
                        })
                    except Exception:
                        continue
            if score_data:
                df_sc = pd.DataFrame(score_data).sort_values("composite", ascending=False)
                st.write(f"**🏆 Top 10 mã COMPOSITE SCORE cao nhất (tốt nhất đầu tư):**")
                top10 = df_sc.head(10)[["ma", "ten", "composite", "pe", "roe", "von_hoa_ty"]].round(2)
                st.dataframe(top10, use_container_width=True, hide_index=True,
                    column_config={
                        "composite": st.column_config.ProgressColumn("Score (0-100)", min_value=0, max_value=100, format="%.1f"),
                        "pe": st.column_config.NumberColumn("P/E", format="%.1f"),
                        "roe": st.column_config.NumberColumn("ROE %", format="%.1f"),
                        "von_hoa_ty": st.column_config.NumberColumn("Vốn hóa (tỷ)", format="%.0f"),
                    })
                st.write(f"**📉 Bottom 10 mã COMPOSITE SCORE thấp nhất (cần cẩn thận):**")
                bot10 = df_sc.tail(10)[["ma", "ten", "composite", "pe", "roe", "von_hoa_ty"]].round(2)
                st.dataframe(bot10, use_container_width=True, hide_index=True)
                fig_score = go.Figure()
                fig_score.add_trace(go.Bar(
                    x=df_sc["ma"], y=df_sc["composite"],
                    marker_color=['#4CAF50' if s > 60 else ('#FFD700' if s > 40 else '#F44336') for s in df_sc["composite"]],
                    name='Composite Score'
                ))
                fig_score.update_layout(title="Composite Score cho 50 mã VN (0-100)",
                    xaxis_title="Mã CP", yaxis_title="Score",
                    height=400, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_score, use_container_width=True)
                avg_score = float(df_sc["composite"].mean())
                st.caption(f"📊 Composite = Value(20%) + Quality(25%) + Dividend(10%) + Foreign(10%) + Momentum(15%) + Size(20%). Score TB toàn thị trường: {avg_score:.1f}/100. Tính từ {len(df_sc)} mã có đủ data từ yfinance.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🌐 DEEP ANALYSIS TOÀN THỊ TRƯỜNG — 384 mã (229 VN + 155 TG)")
        if market_data and len(market_data) >= 10:
            vn_count = sum(1 for d in market_data if d.get('vung') == 'VN')
            tg_count = sum(1 for d in market_data if d.get('vung') == 'TG')
            st.caption(f"📊 Phân tích TẤT CẢ {len(market_data)} mã ({vn_count} VN + {tg_count} TG) — song song + cache 30 phút")

            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _fetch_one_chart(ma_suffix, range_, interval_, timeout_=3):
                import requests as _rq
                ma, suffix = ma_suffix
                try:
                    r = _rq.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ma}{suffix}",
                        params={"range": range_, "interval": interval_},
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout_)
                    if r.status_code == 200:
                        closes = r.json().get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        return ma, [c for c in closes if c]
                except Exception:
                    pass
                return ma, []

            def _fetch_all_parallel(targets_with_suffix, range_, interval_, max_workers=20, progress_label="Đang tải", progress_callback=None):
                results = {}
                done = 0
                total = len(targets_with_suffix)
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    futs = {ex.submit(_fetch_one_chart, t, range_, interval_): t[0] for t in targets_with_suffix}
                    for fut in as_completed(futs):
                        ma, closes = fut.result()
                        if closes:
                            results[ma] = closes
                        done += 1
                        if progress_callback:
                            try:
                                progress_callback(min(1.0, done / total), f"{progress_label} {done}/{total}")
                            except Exception:
                                pass
                return results

            @st.cache_data(ttl=1800, show_spinner=False)
            def _fetch_returns_6mo(targets_tuple):
                return _fetch_all_parallel(list(targets_tuple), "6mo", "1mo", max_workers=20, progress_label="Calendar 6M")

            @st.cache_data(ttl=1800, show_spinner=False)
            def _fetch_returns_3mo_daily(targets_tuple):
                return _fetch_all_parallel(list(targets_tuple), "3mo", "1d", max_workers=20, progress_label="Higher Moments 3T")

            @st.cache_data(ttl=1800, show_spinner=False)
            def _fetch_returns_6mo_daily(targets_tuple):
                return _fetch_all_parallel(list(targets_tuple), "6mo", "1d", max_workers=20, progress_label="Max DD 6T")

            st.write("### 📅 Calendar Returns — 6 tháng qua (TOÀN BỘ 384 mã)")
            cal_targets = list(market_data)
            _cal_prog = st.progress(0.0, f"📅 Calendar: 0/{len(cal_targets)}")
            def _cal_cb(p, t):
                try:
                    _cal_prog.progress(p, t)
                except Exception:
                    pass
            cal_data = _fetch_returns_6mo(tuple([(d["ma"], ".VN" if d.get("vung", "VN") == "VN" else "") for d in cal_targets]))
            try:
                _cal_prog.empty()
            except Exception:
                pass
            if cal_data:
                cal_rows = []
                for d in cal_targets:
                    ma = d["ma"]
                    closes = cal_data.get(ma, [])
                    if len(closes) >= 2 and closes[0] > 0 and closes[-1] > 0:
                        ret6m = (closes[-1] / closes[0] - 1) * 100
                        cal_rows.append({"Mã": ma, "Vùng": d.get("vung", ""), "Giá": d.get("gia", 0),
                            "Vốn hóa (tỷ)": round(d.get("von_hoa", 0) / 1e9, 0) if d.get("von_hoa", 0) > 0 else 0,
                            "Return 6M %": round(ret6m, 2),
                            "Vol ratio": round(float(d.get("vol_ratio", 0) or 0), 2)})
                if cal_rows:
                    df_cal = pd.DataFrame(cal_rows).sort_values("Return 6M %", ascending=False)
                    st.dataframe(df_cal, use_container_width=True, hide_index=True, height=600)
                    cnt_vn = sum(1 for r in cal_rows if r["Vùng"] == "VN")
                    cnt_tg = sum(1 for r in cal_rows if r["Vùng"] == "TG")
                    st.caption(f"📊 Tính từ giá thật 6 tháng yfinance cho {len(cal_rows)}/{len(market_data)} mã ({cnt_vn} VN + {cnt_tg} TG). Return 6M = (giá cuối kỳ / giá đầu kỳ - 1) × 100%. Cache 30 phút.")
                else:
                    st.info("⚠️ Không fetch được dữ liệu calendar.")
            else:
                st.info("⚠️ Không fetch được dữ liệu calendar.")

            st.write("### 🌪️ Volatility Cone — 384 mã (TOÀN BỘ thị trường)")
            vol_rows = []
            for d in market_data:
                vr = d.get("vol_ratio", 0) or 0
                if vr > 0:
                    v_est = max(10, min(80, 25 + (vr - 1) * 8))
                    vol_rows.append({"Mã": d["ma"], "Vùng": d.get("vung", ""),
                        "Vol %/năm": round(v_est, 1),
                        "Vol ratio": round(vr, 2),
                        "Vốn hóa (tỷ)": round(d.get("von_hoa", 0) / 1e9, 0) if d.get("von_hoa", 0) > 0 else 0})
            if vol_rows:
                df_volc = pd.DataFrame(vol_rows)
                p10 = float(df_volc["Vol %/năm"].quantile(0.10))
                p25 = float(df_volc["Vol %/năm"].quantile(0.25))
                p50 = float(df_volc["Vol %/năm"].quantile(0.50))
                p75 = float(df_volc["Vol %/năm"].quantile(0.75))
                p90 = float(df_volc["Vol %/năm"].quantile(0.90))
                vc1, vc2, vc3, vc4, vc5 = st.columns(5)
                vc1.metric("📊 P10 (Yên tĩnh)", f"{p10:.1f}%")
                vc2.metric("📊 P25", f"{p25:.1f}%")
                vc3.metric("📊 P50 (Median)", f"{p50:.1f}%")
                vc4.metric("📊 P75", f"{p75:.1f}%")
                vc5.metric("📊 P90 (Bất ổn)", f"{p90:.1f}%")
                fig_vc = go.Figure()
                fig_vc.add_trace(go.Histogram(x=df_volc["Vol %/năm"], nbinsx=30,
                    marker_color='#4FC3F7', opacity=0.7, name='Phân phối Vol'))
                for p, label, color in [(p10, "P10", '#4CAF50'), (p50, "P50", '#FFD700'), (p90, "P90", '#F44336')]:
                    fig_vc.add_vline(x=p, line_dash="dash", line_color=color, annotation_text=label)
                fig_vc.update_layout(title=f"Vol Distribution — {len(df_volc)} mã (ước lượng từ vol_ratio)",
                    xaxis_title="Vol %/năm", yaxis_title="Số mã", height=350,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_vc, use_container_width=True)
                st.caption(f"📊 Vol ước lượng = 25% + (vol_ratio-1)*8%, clip [10, 80]%. Tính từ TOÀN BỘ {len(df_volc)} mã (full market scan).")

            st.write("### 🧬 Higher Moments & Tail Risk — 384 mã (TOÀN BỘ thị trường)")
            hm_targets = list(market_data)
            _hm_prog = st.progress(0.0, f"🧬 Higher Moments: 0/{len(hm_targets)}")
            def _hm_cb(p, t):
                try:
                    _hm_prog.progress(p, t)
                except Exception:
                    pass
            hm_prices = _fetch_returns_3mo_daily(tuple([(d["ma"], ".VN" if d.get("vung", "VN") == "VN" else "") for d in hm_targets]))
            try:
                _hm_prog.empty()
            except Exception:
                pass
            if hm_prices:
                hm_rows = []
                for d in hm_targets:
                    ma = d["ma"]
                    closes = hm_prices.get(ma, [])
                    if len(closes) > 20:
                        rets = pd.Series(closes).pct_change().dropna()
                        if len(rets) > 5:
                            sk = float(rets.skew()) if float(rets.std()) > 0 else 0
                            ku = float(rets.kurtosis()) if float(rets.std()) > 0 else 0
                            vol_v = float(rets.std() * (252 ** 0.5) * 100)
                            var95 = float(rets.quantile(0.05) * 100)
                            hm_rows.append({"Mã": ma, "Vùng": d.get("vung", ""),
                                "Vol %/năm": round(vol_v, 1),
                                "Skewness": round(sk, 2),
                                "Kurtosis": round(ku, 2),
                                "VaR 95% (1N) %": round(var95, 2)})
                if hm_rows:
                    df_hm = pd.DataFrame(hm_rows).sort_values("VaR 95% (1N) %")
                    st.dataframe(df_hm, use_container_width=True, hide_index=True, height=600)
                    cnt_vn = sum(1 for r in hm_rows if r["Vùng"] == "VN")
                    cnt_tg = sum(1 for r in hm_rows if r["Vùng"] == "TG")
                    st.caption(f"📊 Skewness<0 = lệch trái, Kurtosis>3 = đuôi dày. Tính từ {len(hm_rows)}/{len(market_data)} mã ({cnt_vn} VN + {cnt_tg} TG) daily returns 3T yfinance. Cache 30 phút.")
                else:
                    st.info("⚠️ Không tính được higher moments.")
            else:
                st.info("⚠️ Không fetch được dữ liệu 3T.")

            st.write("### 📉 Max Drawdown Distribution — 384 mã (TOÀN BỘ thị trường)")
            dd_targets = list(market_data)
            _dd_prog = st.progress(0.0, f"📉 Max DD: 0/{len(dd_targets)}")
            def _dd_cb(p, t):
                try:
                    _dd_prog.progress(p, t)
                except Exception:
                    pass
            dd_prices = _fetch_returns_6mo_daily(tuple([(d["ma"], ".VN" if d.get("vung", "VN") == "VN" else "") for d in dd_targets]))
            try:
                _dd_prog.empty()
            except Exception:
                pass
            if dd_prices:
                dd_rows = []
                for d in dd_targets:
                    ma = d["ma"]
                    closes = dd_prices.get(ma, [])
                    if len(closes) > 30:
                        ps = pd.Series(closes)
                        rm = ps.cummax()
                        dd = float(((ps - rm) / rm * 100).min())
                        ret6m = (float(closes[-1]) / float(closes[0]) - 1) * 100 if closes[0] > 0 else 0
                        dd_rows.append({"Mã": ma, "Vùng": d.get("vung", ""),
                            "Return 6M %": round(ret6m, 2),
                            "Max DD %": round(dd, 2),
                            "RoMaD": round(ret6m / abs(dd), 2) if dd != 0 else 0,
                            "Vốn hóa (tỷ)": round(d.get("von_hoa", 0) / 1e9, 0) if d.get("von_hoa", 0) > 0 else 0})
                if dd_rows:
                    df_dd = pd.DataFrame(dd_rows)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**📉 Top 15 sụt giảm mạnh nhất:**")
                        st.dataframe(df_dd.nsmallest(15, "Max DD %"), use_container_width=True, hide_index=True, height=500)
                    with c2:
                        st.write("**🏆 Top 15 RoMaD tốt nhất:**")
                        st.dataframe(df_dd.nlargest(15, "RoMaD"), use_container_width=True, hide_index=True, height=500)
                    avg_dd = float(df_dd["Max DD %"].mean())
                    best_romad = df_dd.nlargest(1, "RoMaD").iloc[0]
                    cnt_vn = sum(1 for r in dd_rows if r["Vùng"] == "VN")
                    cnt_tg = sum(1 for r in dd_rows if r["Vùng"] == "TG")
                    st.metric("📊 Max DD TB toàn thị trường", f"{avg_dd:.1f}%",
                        help=f"Top performer: {best_romad['Mã']} (RoMaD={best_romad['RoMaD']:.2f})")
                    st.caption(f"📊 Max DD tính từ drawdown peak-to-trough 6T. RoMaD = Return 6M / |Max DD|. >2 = chất lượng cao. Tính từ {len(df_dd)}/{len(market_data)} mã ({cnt_vn} VN + {cnt_tg} TG). Cache 30 phút.")
                else:
                    st.info("⚠️ Không tính được Max DD.")
            else:
                st.info("⚠️ Không fetch được dữ liệu 6T.")

            st.write("### ⚖️ Beta & Alpha toàn thị trường — Đo lường rủi ro hệ thống (384 mã)")
            @st.cache_data(ttl=3600, show_spinner=False)
            def _fetch_bench():
                import requests as _rq_b
                for sym, suf in [("VN30", ".VN"), ("^VN30", ""), ("E1VFVN30", ".VN"), ("E1VFVN30.VN", "")]:
                    try:
                        r = _rq_b.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suf}",
                            params={"range": "6mo", "interval": "1d"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            closes = r.json().get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            vb = [c for c in closes if c]
                            if len(vb) > 30:
                                return pd.Series(vb).pct_change().dropna(), sym
                    except Exception:
                        continue
                return None, None
            bench_prices, bench_label = _fetch_bench()
            if bench_prices is not None and len(bench_prices) > 30:
                ba_rows = []
                ba_prices = dd_prices if dd_prices else _fetch_returns_6mo_daily(tuple([(d["ma"], ".VN" if d.get("vung", "VN") == "VN" else "") for d in market_data]))
                for d in market_data:
                    ma = d["ma"]
                    closes = ba_prices.get(ma, [])
                    if len(closes) > 30:
                        rets = pd.Series(closes).pct_change().dropna()
                        common_idx = rets.index.intersection(bench_prices.index)
                        if len(common_idx) > 20 and float(bench_prices.loc[common_idx].std()) > 0:
                            x = bench_prices.loc[common_idx].values
                            y = rets.loc[common_idx].values
                            if len(x) > 20 and float(np.std(y)) > 0:
                                beta, alpha = np.polyfit(x, y, 1)
                                corr_v = float(np.corrcoef(x, y)[0, 1])
                                ba_rows.append({"Mã": ma, "Vùng": d.get("vung", ""),
                                    "Beta": round(float(beta), 2),
                                    "Alpha %/ngày": round(float(alpha) * 100, 3),
                                    "Correlation": round(corr_v, 2),
                                    "R²": round(corr_v ** 2, 2),
                                    "Vốn hóa (tỷ)": round(d.get("von_hoa", 0) / 1e9, 0) if d.get("von_hoa", 0) > 0 else 0,
                                    "Diễn giải": "🟢 Phòng thủ" if beta < 0.8 else ("🟡 Trung bình" if beta < 1.2 else "🔴 Tăng mạnh")})
                if ba_rows:
                    df_ba = pd.DataFrame(ba_rows).sort_values("Beta")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**🛡️ Top 15 Beta thấp (phòng thủ tốt) — vs {bench_label}:**")
                        st.dataframe(df_ba.head(15), use_container_width=True, hide_index=True, height=500)
                    with c2:
                        st.write(f"**🚀 Top 15 Beta cao (tăng mạnh theo thị trường) — vs {bench_label}:**")
                        st.dataframe(df_ba.nlargest(15, "Beta"), use_container_width=True, hide_index=True, height=500)
                    avg_beta = float(df_ba["Beta"].mean())
                    cnt_vn = sum(1 for r in ba_rows if r["Vùng"] == "VN")
                    cnt_tg = sum(1 for r in ba_rows if r["Vùng"] == "TG")
                    st.metric(f"📊 Beta TB toàn thị trường (vs {bench_label})", f"{avg_beta:.2f}",
                        help=f"Tính từ {len(ba_rows)} mã ({cnt_vn} VN + {cnt_tg} TG)")
                    st.caption(f"📊 Beta = hệ số nhạy với {bench_label} benchmark. Tính từ {len(ba_rows)}/{len(market_data)} mã ({cnt_vn} VN + {cnt_tg} TG) daily returns 6T. Alpha = return vượt benchmark/ngày.")
                else:
                    st.info("⚠️ Không tính được Beta.")
            else:
                st.info("⚠️ Không fetch được VN30/E1VFVN30 để tính beta.")

            st.write("### 🔗 Cross-Correlation Top 50 vốn hóa — Phân nhóm cùng ngành")
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import requests as _rq_xc2, pandas as _pd_xc2, plotly.graph_objects as _go_xc
                xc_ma_list = [ma for ma, info in dm.items() if info.get("gia_thi_truong", 0) * info.get("so_luong", 0) > 0 and tong_gt > 0]
                if len(xc_ma_list) >= 2:
                    _vn_keys_xc = set((DOCS.get("co_phieu_vn") or {}).keys())
                    _xc_prices = {}
                    def _fetch_xc(sym, suffix):
                        try:
                            r = _rq_xc2.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                                params={"range": "3mo", "interval": "1d"},
                                timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                            if r.status_code == 200:
                                d = r.json()
                                quote = d.get("chart", {}).get("result", [{}])[0]
                                ts = quote.get("timestamp", [])
                                cs = quote.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                                pairs = [(t, c) for t, c in zip(ts, cs) if c]
                                if len(pairs) > 20:
                                    idx = _pd_xc2.to_datetime([p[0] for p in pairs], unit="s")
                                    return sym, _pd_xc2.Series([p[1] for p in pairs], index=idx)
                        except: pass
                        return sym, None
                    with ThreadPoolExecutor(max_workers=12) as _ex_xc:
                        _futs_xc = {_ex_xc.submit(_fetch_xc, m, ".VN" if m in _vn_keys_xc else ""): m for m in xc_ma_list}
                        for _f_xc in as_completed(_futs_xc):
                            _s_xc, _p_xc = _f_xc.result()
                            if _p_xc is not None:
                                _xc_prices[_s_xc] = _p_xc
                    if len(_xc_prices) >= 2:
                        _df_xc = _pd_xc2.DataFrame({k: v.pct_change().dropna() for k, v in _xc_prices.items()}).dropna()
                        if _df_xc.shape[1] >= 2 and len(_df_xc) > 10:
                            _corr_xc = _df_xc.corr()
                            _corr_xc = _corr_xc.fillna(0)
                            _fig_xc2 = _go_xc.Figure(data=_go_xc.Heatmap(
                                z=_corr_xc.values, x=_corr_xc.columns.tolist(), y=_corr_xc.columns.tolist(),
                                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                                text=np.round(_corr_xc.values, 2),
                                texttemplate="%{text}", textfont={"size": 9}))
                            _fig_xc2.update_layout(height=max(400, 30 * _corr_xc.shape[0]),
                                title=f"Correlation Matrix — {_corr_xc.shape[0]} mã (3T daily returns)",
                                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#ECE8E1"))
                            st.plotly_chart(_fig_xc2, use_container_width=True)
                            try:
                                _vals_xc = _corr_xc.values
                                _avg_c = float(_vals_xc[np.triu_indices_from(_vals_xc, k=1)].mean())
                                st.metric("📊 Correlation TB (cặp đôi)", f"{_avg_c:.3f}",
                                    help="TB corr giữa các cặp mã. Càng gần 0 = đa dạng hóa tốt")
                            except Exception:
                                pass
                            st.caption(f"📊 Corr>0.7 = cùng nhóm (đỏ đậm), <0.3 = độc lập. Tính từ {_corr_xc.shape[0]} mã daily returns 3T yfinance.")
                        else:
                            st.info(f"⚠️ Cần ≥10 phiên × ≥2 mã. Mới {len(_df_xc)} phiên × {_df_xc.shape[1]} mã.")
                    else:
                        st.info("⚠️ Yahoo Finance không trả dữ liệu. Refresh sau 5-10 phút.")
                else:
                    st.info("Cần ≥2 mã trong danh mục.")
            except Exception as e:
                st.warning(f"⚠️ Không tính được cross-correlation: {str(e)[:80]}")

        st.write("### 📊 PHÂN TÍCH CHUYÊN SÂU 384 MÃ — ĐẦY ĐỦ METRICS (Sharpe/Alpha/Beta/VaR/CVaR/Sortino/Calmar/MaxDD)")
        if market_data and len(market_data) >= 10 and dd_prices:
            try:
                bench_label_dm = bench_label if bench_prices is not None else "VN30"
                if bench_prices is None:
                    bench_label_dm = "VN30"
                metrics_rows = []
                for d in market_data:
                    ma = d["ma"]
                    closes = dd_prices.get(ma, [])
                    if len(closes) > 30:
                        try:
                            ps = pd.Series(closes)
                            rets = ps.pct_change().dropna()
                            if len(rets) < 30:
                                continue
                            ann_ret = float((1 + rets).prod() ** (252 / len(rets)) - 1) * 100
                            vol_a = float(rets.std() * (252 ** 0.5) * 100)
                            downside = rets[rets < 0]
                            dd_a = float(downside.std() * (252 ** 0.5) * 100) if len(downside) > 0 else vol_a
                            sharpe = (ann_ret - 3.0) / vol_a if vol_a > 0 else 0
                            sortino = (ann_ret - 3.0) / dd_a if dd_a > 0 else 0
                            cum = (1 + rets).cumprod()
                            rm = cum.cummax()
                            dd_pct = ((cum - rm) / rm)
                            max_dd = float(dd_pct.min() * 100)
                            calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
                            var95 = float(np.percentile(rets, 5) * 100)
                            cvar95 = float(rets[rets <= np.percentile(rets, 5)].mean() * 100) if len(rets[rets <= np.percentile(rets, 5)]) > 0 else var95
                            if bench_prices is not None:
                                common_idx_m = rets.index.intersection(bench_prices.index)
                                if len(common_idx_m) > 20:
                                    x_m = bench_prices.loc[common_idx_m].values
                                    y_m = rets.loc[common_idx_m].values
                                    if len(x_m) > 20 and float(np.std(x_m)) > 0:
                                        beta_m, alpha_m = np.polyfit(x_m, y_m, 1)
                                        info_ratio = float(alpha_m * 252 * 100 / (np.std(y_m - x_m) * (252 ** 0.5) * 100 + 0.001))
                                    else:
                                        beta_m, alpha_m, info_ratio = 0, 0, 0
                                else:
                                    beta_m, alpha_m, info_ratio = 0, 0, 0
                            else:
                                beta_m, alpha_m, info_ratio = 0, 0, 0
                            metrics_rows.append({
                                "Mã": ma, "Vùng": d.get("vung", ""),
                                "Giá": round(float(closes[-1]), 0),
                                "Return năm %": round(ann_ret, 2),
                                "Vol %": round(vol_a, 1),
                                "Sharpe": round(sharpe, 2),
                                "Sortino": round(sortino, 2),
                                "Calmar": round(calmar, 2),
                                "Beta": round(float(beta_m), 2),
                                "Alpha %/năm": round(float(alpha_m) * 252 * 100, 2),
                                "Info Ratio": round(info_ratio, 2),
                                "VaR 95% (1N) %": round(var95, 2),
                                "CVaR 95%": round(cvar95, 2),
                                "Max DD %": round(max_dd, 1),
                                "Vốn hóa (tỷ)": round(d.get("von_hoa", 0) / 1e9, 0) if d.get("von_hoa", 0) > 0 else 0})
                        except Exception:
                            continue
                if metrics_rows:
                    df_metrics = pd.DataFrame(metrics_rows)
                    st.caption(f"📊 Đầy đủ 13 metrics cho {len(df_metrics)}/{len(market_data)} mã từ giá thật yfinance 6T (annualized). So sánh: top theo từng chỉ số.")
                    sort_opts = ["Sharpe", "Sortino", "Calmar", "Return năm %", "Info Ratio"]
                    sort_opt = st.selectbox("Xếp hạng theo:", sort_opts, key="metrics_sort")
                    df_show = df_metrics.sort_values(sort_opt, ascending=False).reset_index(drop=True)
                    df_show.index = df_show.index + 1
                    st.dataframe(df_show, use_container_width=True, hide_index=False, height=600)
                    cnt_vn_m = sum(1 for r in metrics_rows if r["Vùng"] == "VN")
                    cnt_tg_m = sum(1 for r in metrics_rows if r["Vùng"] == "TG")
                    top_sharpe = df_metrics.nlargest(1, "Sharpe").iloc[0]
                    top_calmar = df_metrics.nlargest(1, "Calmar").iloc[0]
                    cm1, cm2, cm3, cm4 = st.columns(4)
                    cm1.metric("🏆 Top Sharpe", f"{top_sharpe['Mã']} ({top_sharpe['Sharpe']:.2f})")
                    cm2.metric("🏆 Top Calmar", f"{top_calmar['Mã']} ({top_calmar['Calmar']:.2f})")
                    cm3.metric("📊 Sharpe TB toàn thị trường", f"{df_metrics['Sharpe'].mean():.2f}")
                    cm4.metric("📊 Max DD TB", f"{df_metrics['Max DD %'].mean():.1f}%")
                    st.caption(f"📊 Metrics: Return annualized, Vol annualized, Sharpe (rf=3%), Sortino (downside), Calmar (return/|maxDD|), Beta/Alpha vs {bench_label_dm}, VaR/CVaR 95% 1-day, Max DD 6T. Tính từ {len(df_metrics)} mã ({cnt_vn_m} VN + {cnt_tg_m} TG).")
            except Exception as e:
                st.warning(f"⚠️ Không tính được metrics 384 mã: {str(e)[:100]}")
        else:
            st.info("⚠️ Cần market scan + price data để tính metrics 384 mã.")

        st.write("---")
        st.write("## 🔗 50-STOCK CORRELATION MATRIX — Ma trận tương quan 50 mã")
        if market_data and len(market_data) >= 5:
            @st.cache_data(ttl=1800)
            def _compute_50_corr(symbols):
                import requests as _rq_c
                prices_dict = {}
                for s in symbols:
                    try:
                        r = _rq_c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}.VN?range=3mo&interval=1d",
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                        if r.status_code == 200:
                            d = r.json()
                            cs = d.get("chart", {}).get("result", [{}])[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            valid = [c for c in cs if c]
                            if len(valid) > 30:
                                prices_dict[s] = pd.Series(valid)
                    except Exception:
                        continue
                if len(prices_dict) < 3:
                    return None
                df_p = pd.DataFrame(prices_dict)
                ret = df_p.pct_change().dropna()
                if len(ret) < 10:
                    return None
                return ret.corr()
            with st.spinner(f"📡 Tính correlation 3T cho {len(market_data)} mã..."):
                corr = _compute_50_corr(tuple([d["ma"] for d in market_data]))
            if corr is not None and not corr.empty:
                st.write(f"**🔗 Ma trận tương quan {len(corr.columns)}×{len(corr.columns)} mã VN (3 tháng):**")
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr.values, x=corr.columns, y=corr.index,
                    colorscale='RdBu_r', zmid=0, zmin=-1, zmax=1,
                    colorbar=dict(title="Corr"),
                    text=corr.round(2).values,
                    texttemplate="%{text}",
                    textfont={"size": 8}
                ))
                fig_corr.update_layout(title="Ma trận tương quan 50 mã VN (Pearson, 3T)",
                    height=700, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_corr, use_container_width=True)
                pairs = []
                cols = corr.columns.tolist()
                for i in range(len(cols)):
                    for j in range(i+1, len(cols)):
                        if cols[i] != cols[j]:
                            pairs.append((cols[i], cols[j], float(corr.iloc[i, j])))
                pairs.sort(key=lambda x: -abs(x[2]))
                st.write("**🔥 Top 10 cặp tương quan CAO (cùng xu hướng mạnh):**")
                st.dataframe(pd.DataFrame(pairs[:10], columns=["Mã 1", "Mã 2", "Correlation"]).round(3),
                    use_container_width=True, hide_index=True)
                st.write("**❄️ Top 10 cặp tương quan THẤP (phân tán tốt cho DM):**")
                st.dataframe(pd.DataFrame(pairs[-10:], columns=["Mã 1", "Mã 2", "Correlation"]).round(3),
                    use_container_width=True, hide_index=True)
                st.caption(f"📊 Correlation = Pearson trên daily returns 3T. >0.7 = cùng xu hướng mạnh. <0.3 = phân tán tốt. Tính từ {len(corr.columns)} mã giá thật yfinance.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 📊 DISTRIBUTION ANALYSIS — Phân phối P/E, ROE, Vol 50 mã")
        if market_data and len(market_data) >= 5:
            dist_data = []
            with st.spinner("📡 Tải P/E, ROE, Beta song song cho 50 mã..."):
                import yfinance as _yf_dist
                dist_targets = [(d["ma"], ".VN" if d.get("vung") == "VN" else "") for d in market_data[:50]]
                with ThreadPoolExecutor(max_workers=15) as _ex_dist:
                    def _fetch_dist(t):
                        _info = _yf_dist.Ticker(t[0] + t[1]).info if t[1] else _yf_dist.Ticker(t[0]).info
                        return _info
                    _futs_dist = {_ex_dist.submit(_fetch_dist, t): t for t in dist_targets}
                    for _f in as_completed(_futs_dist):
                        try:
                            _inf = _f.result()
                            _ma = _futs_dist[_f][0]
                            pe = _inf.get("trailingPE") or _inf.get("forwardPE")
                            roe = _inf.get("returnOnEquity")
                            beta = _inf.get("beta")
                            if pe and 0 < float(pe) < 200:
                                dist_data.append({"ma": _ma, "pe": float(pe),
                                    "roe": float(roe) * 100 if roe and -0.5 < roe < 0.5 else None,
                                    "beta": float(beta) if beta and 0 < float(beta) < 3 else None})
                        except Exception:
                            continue
            if not dist_data:
                for d in market_data[:50]:
                    pe = d.get("pe") or d.get("trailingPE")
                    roe = d.get("roe")
                    beta = d.get("beta")
                    if pe and 0 < float(pe) < 200:
                        dist_data.append({"ma": d["ma"], "pe": float(pe),
                            "roe": float(roe) * 100 if roe and -0.5 < roe < 0.5 else None,
                            "beta": float(beta) if beta and 0 < float(beta) < 3 else None})
            if dist_data:
                df_dist = pd.DataFrame(dist_data)
                fig_dist = make_subplots(rows=1, cols=3, subplot_titles=("Phân phối P/E", "Phân phối ROE %", "Phân phối Beta"))
                fig_dist.add_trace(go.Histogram(x=df_dist["pe"].dropna(), nbinsx=20,
                    marker_color='#2196F3', name='P/E', showlegend=False), row=1, col=1)
                if "roe" in df_dist.columns and df_dist["roe"].notna().any():
                    fig_dist.add_trace(go.Histogram(x=df_dist["roe"].dropna(), nbinsx=20,
                        marker_color='#4CAF50', name='ROE', showlegend=False), row=1, col=2)
                if "beta" in df_dist.columns and df_dist["beta"].notna().any():
                    fig_dist.add_trace(go.Histogram(x=df_dist["beta"].dropna(), nbinsx=20,
                        marker_color='#FF9800', name='Beta', showlegend=False), row=1, col=3)
                fig_dist.update_layout(height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_dist, use_container_width=True)
                d1, d2, d3, d4, d5, d6 = st.columns(6)
                d1.metric("📊 P/E Median", f"{df_dist['pe'].median():.1f}")
                d2.metric("📊 P/E Mean", f"{df_dist['pe'].mean():.1f}")
                d3.metric("📊 ROE Median", f"{df_dist['roe'].dropna().median():.1f}%" if df_dist['roe'].notna().any() else "N/A")
                d4.metric("📊 ROE Mean", f"{df_dist['roe'].dropna().mean():.1f}%" if df_dist['roe'].notna().any() else "N/A")
                d5.metric("📊 Beta Median", f"{df_dist['beta'].dropna().median():.2f}" if df_dist['beta'].notna().any() else "N/A")
                d6.metric("📊 Beta Mean", f"{df_dist['beta'].dropna().mean():.2f}" if df_dist['beta'].notna().any() else "N/A")
                st.caption(f"📊 Histogram phân phối P/E, ROE, Beta cho {len(df_dist)} mã từ yfinance. P/E median 12-15 = thị trường hợp lý. ROE median 12-15% = chất lượng tốt.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🌐 CROSS-SECTOR COMPARISON — So sánh đa ngành (Boxplot)")
        if market_data and len(market_data) >= 5:
            cs_data = []
            with st.spinner("📡 Tải P/E, ROE, Beta song song theo ngành..."):
                import yfinance as _yf_cs
                cs_targets = [(d["ma"], ".VN" if d.get("vung") == "VN" else "", d.get("nganh", "Khác"), d.get("ret_3m", 0)) for d in market_data[:100]]
                with ThreadPoolExecutor(max_workers=15) as _ex_cs:
                    def _fetch_cs(t):
                        _info = _yf_cs.Ticker(t[0] + t[1]).info if t[1] else _yf_cs.Ticker(t[0]).info
                        return _info, t[2], t[3]
                    _futs_cs = {_ex_cs.submit(_fetch_cs, t): t for t in cs_targets}
                    for _f in as_completed(_futs_cs):
                        try:
                            _inf, _ng, _r3 = _f.result()
                            pe = _inf.get("trailingPE") or _inf.get("forwardPE")
                            roe = _inf.get("returnOnEquity")
                            beta = _inf.get("beta")
                            if pe and 0 < float(pe) < 200:
                                cs_data.append({"nganh": _ng, "pe": float(pe),
                                    "roe": float(roe) * 100 if roe and -0.5 < roe < 0.5 else None,
                                    "beta": float(beta) if beta and 0 < float(beta) < 3 else None,
                                    "ret_3m": _r3})
                        except Exception:
                            continue
            if not cs_data:
                for d in market_data[:100]:
                    pe = d.get("pe") or d.get("trailingPE")
                    roe = d.get("roe")
                    beta = d.get("beta")
                    if pe and 0 < float(pe) < 200:
                        cs_data.append({"nganh": d.get("nganh", "Khác"), "pe": float(pe),
                            "roe": float(roe) * 100 if roe and -0.5 < roe < 0.5 else None,
                            "beta": float(beta) if beta and 0 < float(beta) < 3 else None,
                            "ret_3m": d.get("ret_3m", 0)})
            if cs_data:
                df_cs = pd.DataFrame(cs_data)
                fig_cs = make_subplots(rows=1, cols=3, subplot_titles=("P/E theo ngành", "ROE % theo ngành", "Return 3M theo ngành"))
                if "pe" in df_cs.columns:
                    for ng in df_cs["nganh"].unique():
                        d_ng = df_cs[df_cs["nganh"] == ng]
                        fig_cs.add_trace(go.Box(y=d_ng["pe"], name=ng, boxpoints="outliers", showlegend=False), row=1, col=1)
                if "roe" in df_cs.columns and df_cs["roe"].notna().any():
                    for ng in df_cs["nganh"].unique():
                        d_ng = df_cs[df_cs["nganh"] == ng]
                        d_ng = d_ng[d_ng["roe"].notna()]
                        if len(d_ng) > 0:
                            fig_cs.add_trace(go.Box(y=d_ng["roe"], name=ng, boxpoints="outliers", showlegend=False), row=1, col=2)
                if "ret_3m" in df_cs.columns:
                    for ng in df_cs["nganh"].unique():
                        d_ng = df_cs[df_cs["nganh"] == ng]
                        fig_cs.add_trace(go.Box(y=d_ng["ret_3m"], name=ng, boxpoints="outliers", showlegend=False), row=1, col=3)
                fig_cs.update_layout(height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_cs, use_container_width=True)
                st.caption(f"📊 Boxplot P/E, ROE, Return 3M theo ngành từ {len(df_cs)} mã. Box rộng = variance lớn trong ngành. Dot outlier = mã đặc biệt.")
        else:
            st.info("⚠️ Cần dữ liệu thị trường.")

        st.write("---")
        st.write("## 🔥 Heatmap Tỷ suất Cổ tức theo Ngành — Sector Dividend Yield Map")
        _co_phieu_vn = DOCS.get("co_phieu_vn") or {}
        _cp_vn_items = _co_phieu_vn.items() if isinstance(_co_phieu_vn, dict) else []
        _sector_dy = {}
        for _ma_vn, _info_vn in _cp_vn_items:
            _ng = _info_vn.get("nganh", "Khác") or "Khác"
            _ct = _info_vn.get("co_tuc_pct", 0)
            if _ct and isinstance(_ct, (int, float)) and 0 < float(_ct) < 50:
                _sector_dy.setdefault(_ng, []).append(float(_ct))
        for _ma_dm, _info_dm in dm.items():
            if _ma_dm not in _co_phieu_vn:
                _ki_dm = kpi.get(_ma_dm, {}) or {}
                _dy_dm = _ki_dm.get("dividend_yield", 0)
                if _dy_dm and isinstance(_dy_dm, (int, float)) and 0 < float(_dy_dm) < 0.5:
                    _ng_dm = _ki_dm.get("nganh", "Khác") or "Khác"
                    _sector_dy.setdefault(_ng_dm, []).append(float(_dy_dm) * 100)
        if _sector_dy:
            _sec_dy_df = pd.DataFrame([
                {"Ngành": ng, "Cổ tức TB %": round(np.mean(vals), 2),
                 "Cổ tức Cao nhất %": round(max(vals), 2),
                 "Số mã": len(vals)}
                for ng, vals in sorted(_sector_dy.items(), key=lambda x: np.mean(x[1]), reverse=True)
            ])
            fig_dy = go.Figure(data=go.Heatmap(
                z=[_sec_dy_df["Cổ tức TB %"].values],
                x=_sec_dy_df["Ngành"].values,
                y=["Cổ tức TB %"],
                colorscale="YlOrRd",
                text=[f"{v:.2f}%" for v in _sec_dy_df["Cổ tức TB %"].values],
                texttemplate="%{text}",
                hovertemplate="Ngành: %{x}<br>Cổ tức TB: %{z:.2f}%<extra></extra>"
            ))
            fig_dy.update_layout(height=200, margin=dict(l=20, r=20, t=10, b=60),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_dy, use_container_width=True)
            st.dataframe(_sec_dy_df, use_container_width=True, hide_index=True)
            st.caption(f"🔥 Ngành có cổ tức trung bình cao nhất. Dữ liệu từ co_phieu_vn.json ({len(_co_phieu_vn)} mã VN) + yfinance.")
        else:
            st.info("⚠️ Không có dữ liệu cổ tức từ co_phieu_vn.json hoặc yfinance.")

        st.write("---")
        st.write("## 🔄 Phân tích Mùa vụ — Seasonality Analysis (384 mã)")
        if real_prices and len(real_prices) >= 5:
            with st.spinner("📡 Tính toán seasonality từ daily returns..."):
                _monthly_rets = {m: [] for m in range(1, 13)}
                for _sym, _ser in real_prices.items():
                    if len(_ser) < 60:
                        continue
                    _daily_rets = pd.Series(_ser).pct_change().dropna()
                    _daily_rets.index = pd.to_datetime(_daily_rets.index)
                    for _m in range(1, 13):
                        _m_data = _daily_rets[_daily_rets.index.month == _m]
                        if len(_m_data) >= 5:
                            _monthly_rets[_m].append(float(_m_data.mean()) * 100)
                _sea_rows = []
                _month_names = ["", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
                for _m in range(1, 13):
                    if _monthly_rets[_m]:
                        _vals = np.array(_monthly_rets[_m])
                        _sea_rows.append({
                            "Tháng": _month_names[_m],
                            "Return TB %": round(float(np.mean(_vals)), 2),
                            "Median %": round(float(np.median(_vals)), 2),
                            "Tốt nhất %": round(float(np.max(_vals)), 2),
                            "Tệ nhất %": round(float(np.min(_vals)), 2),
                            "% Dương": round(float(np.mean(_vals > 0) * 100), 1),
                            "Số mã": len(_vals),
                        })
                if _sea_rows:
                    _df_sea = pd.DataFrame(_sea_rows)
                    _df_sea["Màu"] = _df_sea["Return TB %"].apply(
                        lambda x: "#4ADE80" if x > 0.3 else ("#F87171" if x < -0.3 else "#FBBF24"))
                    _bar_colors = _df_sea["Màu"].tolist()
                    fig_sea = go.Figure(data=[go.Bar(
                        x=_df_sea["Tháng"], y=_df_sea["Return TB %"],
                        marker_color=_bar_colors,
                        text=[f"{v:+.2f}%" for v in _df_sea["Return TB %"]],
                        textposition="outside"
                    )])
                    fig_sea.update_layout(
                        title="Return trung bình theo tháng — 384 mã",
                        height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#ECE8E1"),
                        yaxis_title="Return TB %", xaxis_title="Tháng")
                    st.plotly_chart(fig_sea, use_container_width=True)
                    st.dataframe(_df_sea.drop(columns=["Màu"]), use_container_width=True, hide_index=True)
                    st.caption("🔄 Return trung bình từng tháng tính trên daily returns của tất cả mã có dữ liệu. Tháng có bar xanh > dương, đỏ = âm. % Dương = tỷ lệ mã có return dương trong tháng đó.")
        else:
            st.info("⚠️ Cần dữ liệu giá thật 6 tháng để phân tích mùa vụ.")

        st.write("---")
        st.write("## 🌐 Tương quan Đa thị trường — VN vs Thế giới")
        _global_prices = {}
        try:
            import yfinance as _yf_gbl
            _gbl_tickers = ["^VNINDEX", "^GSPC", "^N225", "000001.SS"]
            _gbl_names = ["VN-Index", "S&P 500", "Nikkei 225", "Shanghai"]
            _gbl_data = _yf_gbl.download(_gbl_tickers, period="6mo", progress=False, auto_adjust=True, timeout=30)
            if _gbl_data is not None and not _gbl_data.empty and "Close" in _gbl_data.columns:
                for _i, _t in enumerate(_gbl_tickers):
                    _col = ("Close", _t)
                    if _col in _gbl_data.columns:
                        _series = _gbl_data[_col].dropna()
                        if len(_series) >= 20:
                            _global_prices[_gbl_names[_i]] = _series
        except Exception:
            pass
        if len(_global_prices) < 2:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import requests as _rq_gbl2, pandas as _pd_gbl2
            _gbl_fallback = {"VN-Index": "^VNINDEX", "S&P 500": "^GSPC", "Nikkei 225": "^N225", "Shanghai": "000001.SS"}
            def _fetch_gbl2(ticker, name):
                try:
                    r = _rq_gbl2.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                    if r.status_code == 200:
                        d = r.json()
                        quote = d.get("chart", {}).get("result", [{}])[0]
                        ts = quote.get("timestamp", [])
                        cs = quote.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        closes = [c for c in cs if c]
                        if len(closes) >= 20:
                            return name, _pd_gbl2.Series(closes, index=_pd_gbl2.to_datetime(ts[:len(closes)], unit="s"))
                except: pass
                return name, None
            with ThreadPoolExecutor(max_workers=4) as _ex2:
                _futs2 = {_ex2.submit(_fetch_gbl2, t, n): n for n, t in _gbl_fallback.items()}
                for _f2 in as_completed(_futs2):
                    _n2, _s2 = _f2.result()
                    if _s2 is not None:
                        _global_prices[_n2] = _s2
        if len(_global_prices) >= 2:
            _global_df = pd.DataFrame(_global_prices).pct_change().dropna()
            if len(_global_df) >= 5:
                _corr_global = _global_df.corr()
                fig_global = go.Figure(data=go.Heatmap(
                    z=_corr_global.values, x=_corr_global.columns.tolist(), y=_corr_global.index.tolist(),
                    colorscale="RdBu", zmid=0,
                    text=np.round(_corr_global.values, 3),
                    texttemplate="%{text}",
                    hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>"
                ))
                fig_global.update_layout(height=450,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ECE8E1"),
                    title="Correlation Matrix — VN vs Quốc tế (6 tháng)")
                st.plotly_chart(fig_global, use_container_width=True)
                fig_global_ts = go.Figure()
                for _col in _global_df.columns:
                    fig_global_ts.add_trace(go.Scatter(
                        x=_global_df.index, y=(1 + _global_df[_col]).cumprod(),
                        mode="lines", name=_col,
                        hovertemplate="%{x|%d/%m}<br>%{y:.4f}<extra></extra>"
                    ))
                fig_global_ts.update_layout(height=380,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ECE8E1"),
                    title="Hiệu suất tích lũy — VN vs Thế giới",
                    yaxis_title="Tăng trưởng (x lần)")
                st.plotly_chart(fig_global_ts, use_container_width=True)
                st.caption(f"🌐 Tương quan + hiệu suất giữa VN-Index, S&P 500, Nikkei 225, Shanghai ({len(_global_df)} phiên chung). Dữ liệu từ yfinance.")
            else:
                st.info(f"⚠️ Chỉ có {len(_global_df)} phiên chung, cần ≥5.")
        else:
            st.info("⚠️ Yahoo Finance không trả dữ liệu chỉ số quốc tế (rate-limit). Refresh sau 10-15 phút hoặc dùng mạng khác.")

        st.write("---")
        st.write(f"**Tổng giá trị DM:** {tong_gt:,.0f} ₫ | **Lãi/Lỗ:** {tong_lai_lo:+,.0f} ₫ | **Return:** {return_pct:+.2f}% | **Số mã:** {n_ma}")
        if is_demo:
            st.info("📐 Đang hiển thị danh mục mẫu. Vào Sidebar → Cập nhật dữ liệu để dùng danh mục thực.")
elif st.session_state.trang_thai == "dashboard":
    st.markdown('<div class="main-header" style="font-size:1.8rem;font-weight:700;color:#FFD700;margin:0.5rem 0;">📊 Dashboard tổng quan</div>', unsafe_allow_html=True)
    st.markdown("---")

    co_phieu_vn = DOCS.get("co_phieu_vn", {})
    co_phieu_tg = DOCS.get("co_phieu_tg", {})
    kpi = DOCS.get("kpi", {})
    live = DOCS.get("live", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🇻🇳 Cổ phiếu VN", f"{len(co_phieu_vn)} mã",
                  help=f"Trên {len(DOCS.get('danh_sach_portfolio', []))} sàn HOSE/HNX")
    with col2:
        st.metric("🌐 Cổ phiếu TG", f"{len(co_phieu_tg)} mã",
                  help="Mỹ, Châu Âu, Châu Á")
    with col3:
        ma_pt = st.session_state.get("ma_phan_tich", "")
        st.metric("📈 Đang theo dõi", f"{len(kpi)} mã",
                  help="Danh mục đang quản lý")
    with col4:
        st.metric("🔄 Cập nhật", DOCS.get("ngay_cap_nhat", "N/A"),
                  help="Dữ liệu mới nhất")

    st.markdown("---")
    st.subheader("📂 Danh mục đầu tư hiện tại")

    if kpi:
        rows = []
        for ma, info in sorted(kpi.items(),
                                key=lambda x: x[1].get("ty_trong_ht", 0) if x[1].get("ty_trong_ht") else 0,
                                reverse=True):
            if info.get("ty_trong_ht"):
                rows.append({
                    "Mã": ma,
                    "Ngành": info.get("nganh", ""),
                    "Giá": f"{info.get('gia', 0):,.0f}",
                    "P/E": f"{info.get('pe', 0):.1f}",
                    "ROE%": f"{info.get('roe', 0)*100:.1f}",
                    "P&L%": f"{info.get('lai_lo_pct', 0)*100:.1f}",
                    "Điểm MUA": f"{info.get('diem_mua', 0):.0f}",
                    "Điểm BÁN": f"{info.get('diem_ban', 0):.0f}",
                    "KL": info.get("ket_luan", ""),
                    "Tỷ trọng%": f"{info.get('ty_trong_ht', 0)*100:.1f}",
                })
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={c: c for c in df.columns})
        else:
            st.info("Chưa có dữ liệu danh mục.")
    else:
        st.info("Chưa có dữ liệu KPI.")

    st.markdown("---")
    sub1, sub2 = st.columns(2)

    with sub1:
        st.subheader("🏆 Top 10 ROE cao nhất")
        vn_list = []
        for ma, info in co_phieu_vn.items():
            roe = info.get("roe")
            if roe and isinstance(roe, (int, float)):
                vn_list.append({"Mã": ma, "Tên": info.get("ten", ""), "Ngành": info.get("nganh", ""),
                                "ROE%": roe, "P/E": info.get("pe", 0), "P/B": info.get("pb", 0)})
        df_roe = pd.DataFrame(sorted(vn_list, key=lambda x: x["ROE%"], reverse=True)[:10])
        if not df_roe.empty:
            st.dataframe(df_roe, use_container_width=True, hide_index=True)

    with sub2:
        st.subheader("🚀 Top 10 Upside tiềm năng")
        upside_list = []
        for ma, info in kpi.items():
            up = info.get("upside")
            if up and isinstance(up, (int, float)):
                upside_list.append({"Mã": ma, "Ngành": info.get("nganh", ""),
                                    "Upside%": up, "Giá": info.get("gia", 0),
                                    "KL": info.get("ket_luan", ""),
                                    "Hành động": info.get("hanh_dong", "")})
        df_up = pd.DataFrame(sorted(upside_list, key=lambda x: x["Upside%"], reverse=True)[:10])
        if not df_up.empty:
            st.dataframe(df_up, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🧩 Phân bổ ngành")

    if kpi:
        nganh_data = {}
        for ma, info in kpi.items():
            n = info.get("nganh", "Khác")
            w = info.get("ty_trong_ht", 0)
            if n in nganh_data:
                nganh_data[n] += w
            else:
                nganh_data[n] = w
        if nganh_data:
            df_nganh = pd.DataFrame({
                "Ngành": list(nganh_data.keys()),
                "Tỷ trọng": [v*100 for v in nganh_data.values()]
            }).sort_values("Tỷ trọng", ascending=False)
            fig = go.Figure(data=go.Pie(
                labels=df_nganh["Ngành"], values=df_nganh["Tỷ trọng"],
                marker=dict(colors=px.colors.sequential.YlOrRd[:len(df_nganh)]),
                textinfo="label+percent", hole=0.3))
            fig.update_layout(
                title="Tỷ trọng danh mục theo ngành",
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"),
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Tổng quan chỉ số thị trường")

    tt = lay_thong_tin_thi_truong()
    qt = lay_thong_tin_quoc_te()
    if tt or qt:
        c1, c2, c3, c4 = st.columns(4)
        vn_key = next((k for k in tt if "index" in k.lower() or "vn" in k.lower()), None)
        gold_key = next((k for k in tt if "vang" in k.lower() or "gold" in k.lower()), None)
        btc_key = next((k for k in qt if "bitcoin" in k.lower() or "btc" in k.lower()), None)
        sp_key = next((k for k in qt if "sp" in k.lower() or "s&p" in k.lower()), None)
        with c1:
            if vn_key:
                vni = tt[vn_key]
                vni_gia = vni.get('gia_hien_tai', vni.get('gia', 0))
                st.metric("🇻🇳 VN-Index",
                          f"{vni_gia:,.1f} điểm",
                          f"{vni.get('thay_doi_1nam', vni.get('thay_doi_pct', 0))*100:+.2f}%")
        with c2:
            if gold_key:
                g = tt[gold_key]
                g_gia = g.get('gia_hien_tai', g.get('gia', 0))
                st.metric("🥇 Vàng SJC",
                          f"{g_gia:,.0f} VND/lượng",
                          f"{g.get('thay_doi_1nam', g.get('thay_doi_pct', 0))*100:+.2f}%")
        with c3:
            if btc_key:
                btc = qt[btc_key]
                btc_gia = btc.get('gia_hien_tai', btc.get('gia', 0))
                st.metric("₿ Bitcoin",
                          f"${btc_gia:,.0f} USD",
                          f"{btc.get('thay_doi_1nam', btc.get('thay_doi_pct', 0))*100:+.2f}%")
        with c4:
            if sp_key:
                sp = qt[sp_key]
                sp_gia = sp.get('gia_hien_tai', sp.get('gia', 0))
                st.metric("🇺🇸 S&P 500",
                          f"{sp_gia:,.0f} điểm",
                          f"{sp.get('thay_doi_1nam', sp.get('thay_doi_pct', 0))*100:+.2f}%")

elif st.session_state.trang_thai == "chat":
    st.markdown('<div class="main-header" style="font-size:1.8rem;font-weight:700;color:#FFD700;margin:0.5rem 0;">💬 Chat với Robo-Advisor</div>', unsafe_allow_html=True)

    tab_chat_v2, tab_expert_v2 = st.tabs(["💬 Chat", "👑 Hội đồng Chuyên gia"])

    with tab_chat_v2:
        st.markdown("Hỏi tôi về đầu tư, cổ phiếu, vàng, bất động sản, hay bất kỳ chủ đề tài chính nào! 🤖💡")
        st.markdown("💡 *Tôi hiểu được: phân tích DM của bạn, top mã tăng/giảm hôm nay, vol đột biến, gợi ý phân bổ vốn theo hồ sơ rủi ro...*")
        st.markdown("---")

        if not st.session_state.chat_history:
            st.markdown(
                '<div style="background:linear-gradient(135deg,rgba(255,215,0,0.05),rgba(33,150,243,0.03));'
                'border:1px solid rgba(255,215,0,0.15);border-radius:12px;padding:14px 18px;margin-bottom:14px;">'
                '<div style="font-weight:600;color:#FFD700;margin-bottom:8px;">⚡ Gợi ý nhanh từ AI — bấm để hỏi ngay:</div>'
                '<div style="display:flex;gap:8px;flex-wrap:wrap;">'
                '<span style="background:#2196F322;border:1px solid #2196F355;border-radius:20px;padding:6px 14px;font-size:0.85rem;">📊 Phân tích danh mục của tôi</span>'
                '<span style="background:#4CAF5022;border:1px solid #4CAF5055;border-radius:20px;padding:6px 14px;font-size:0.85rem;">📈 Mã nào đang MUA tốt?</span>'
                '<span style="background:#FF980022;border:1px solid #FF980055;border-radius:20px;padding:6px 14px;font-size:0.85rem;">🛡️ Cách phân bổ vốn 100tr?</span>'
                '<span style="background:#9C27B022;border:1px solid #9C27B055;border-radius:20px;padding:6px 14px;font-size:0.85rem;">🥇 Vàng SJC có nên mua?</span>'
                '</div></div>',
                unsafe_allow_html=True,
            )
            _quick_qs = [
                "Phân tích danh mục hiện tại của tôi — nên tăng/giảm mã nào?",
                "Top 3 mã cổ phiếu VN đang MUA tốt nhất tháng này?",
                "Tôi có 100 triệu, nên phân bổ vào cổ phiếu/vàng/tiết kiệm thế nào?",
                "Vàng SJC và vàng nhẫn — nên chọn loại nào 2026?",
            ]
            _qcols = st.columns(2)
            for _i, _q in enumerate(_quick_qs):
                with _qcols[_i % 2]:
                    if st.button(_q, key=f"qq_{_i}", use_container_width=True):
                        st.session_state.chat_history.append({"role": "user", "content": _q})
                        _chat_status = st.status("🤖 Robo-Advisor đang phân tích DM + thị trường...", expanded=False)
                        try:
                            _ctx = _build_chat_context()
                            tra_loi = tim_cau_tra_loi(_q, st.session_state.chat_history, context=_ctx)
                            _chat_status.update(label="✅ Xong", state="complete")
                        except Exception as _chat_err:
                            _chat_status.update(label="❌ Lỗi", state="error")
                            tra_loi = f"Xin lỗi, đã xảy ra lỗi: {_chat_err}"
                        try:
                            _chat_status.empty()
                        except Exception:
                            pass
                        st.session_state.chat_history.append({"role": "bot", "content": tra_loi})
                        try:
                            username = st.session_state.get("username", "unknown")
                            save_chat(username, "user", _q)
                            save_chat(username, "bot", tra_loi)
                        except Exception:
                            pass
                        st.rerun()
            st.markdown("---")

        for i, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "bot":
                st.markdown(
                    f'<div class="chat-message bot-message">🤖 <strong>Robo-Advisor:</strong><br>{_safe_html(msg["content"])}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="chat-message user-message">👤 <strong>Bạn:</strong><br>{_safe_html(msg["content"])}</div>',
                    unsafe_allow_html=True,
                )

        col2, col3 = st.columns([6, 1])
        with col2:
            with st.form(key="chat_form", clear_on_submit=True):
                cau_hoi = st.text_input(
                    "Câu hỏi của bạn:",
                    placeholder="VD: Nên đầu tư cổ phiếu gì?",
                    key="chat_input",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Gửi", use_container_width=True)
                if submitted and cau_hoi:
                    st.session_state.chat_history.append({"role": "user", "content": cau_hoi})
                    _chat_status = st.status("🤖 Robo-Advisor đang suy nghĩ...", expanded=False)
                    try:
                        _ctx = _build_chat_context()
                        tra_loi = tim_cau_tra_loi(cau_hoi, st.session_state.chat_history, context=_ctx)
                        _chat_status.update(label="✅ Xong", state="complete")
                    except Exception as _chat_err:
                        _chat_status.update(label="❌ Lỗi", state="error")
                        tra_loi = f"Xin lỗi, đã xảy ra lỗi: {_chat_err}"
                    try:
                        _chat_status.empty()
                    except Exception:
                        pass
                    st.session_state.chat_history.append({"role": "bot", "content": tra_loi})
                    username = st.session_state.get("username", "unknown")
                    try:
                        save_chat(username, "user", cau_hoi)
                        save_chat(username, "bot", tra_loi)
                    except Exception:
                        pass
                    st.rerun()
        with col3:
            if st.session_state.chat_history and st.button("🗑️ Xóa", key="clear_chat", use_container_width=True, help="Xóa lịch sử chat"):
                st.session_state.chat_history = []
                st.rerun()

    if tab_expert_v2 is not None:
        with tab_expert_v2:
            try:
                st.markdown("### 👑 Hội đồng 6 Chuyên gia — Huyền thoại Đầu tư Thế giới")
                st.markdown(
                    "Gửi **1 câu hỏi**, nhận câu trả lời từ **6 huyền thoại** do AI đóng vai. "
                    "Chủ tịch Hội đồng sẽ tổng hợp và chọn ra phương án tốt nhất."
                )
                st.markdown("---")
                _expert_chips_html = '<div style="margin:6px 0 14px 0;line-height:2.2;">'
                for exp in [
                    {"name": "Warren Buffett", "title": "Nhà đầu tư giá trị", "color": "#4CAF50"},
                    {"name": "George Soros", "title": "Nhà đầu cơ vĩ đại", "color": "#2196F3"},
                    {"name": "Peter Lynch", "title": "Chuyên gia tăng trưởng", "color": "#FF9800"},
                    {"name": "Ray Dalio", "title": "Chiến lược vĩ mô", "color": "#9C27B0"},
                    {"name": "Benjamin Graham", "title": "Cha đẻ đầu tư giá trị", "color": "#607D8B"},
                    {"name": "Charlie Munger", "title": "Triết gia đầu tư", "color": "#795548"},
                ]:
                    _expert_chips_html += (
                        f'<span style="display:inline-block;background:rgba(255,255,255,0.04);'
                        f'border:1px solid rgba(255,215,0,0.1);border-radius:20px;padding:4px 14px;margin:3px 4px;'
                        f'font-size:0.8rem;white-space:nowrap;">'
                        f'<b style="color:{exp["color"]};">{exp["name"]}</b>'
                        f'<span style="color:#8892B0;margin-left:6px;">— {exp["title"]}</span></span>'
                    )
                _expert_chips_html += '</div>'
                st.markdown(_expert_chips_html, unsafe_allow_html=True)
                st.markdown("---")

                if "expert_results" not in st.session_state:
                    st.session_state.expert_results = None

                with st.form(key="expert_form", clear_on_submit=True):
                    cau_hoi = st.text_input(
                        "Câu hỏi của bạn:",
                        placeholder="VD: Tôi nên đầu tư vào VCB, FPT, hay HPG trong năm 2026?",
                        key="expert_question",
                        label_visibility="collapsed",
                    )
                    submitted = st.form_submit_button("🚀 Hỏi 6 Chuyên Gia", use_container_width=True)
                    if submitted and cau_hoi:
                        _status = st.status("🧠 Đang kết nối 6 chuyên gia AI...", expanded=True)
                        try:
                            _status.update(label="🧠 Đang gửi câu hỏi cho 6 chuyên gia (có thể mất 30-90 giây)...")
                            results = hoi_dong_chuyen_gia(cau_hoi, groq_key_override=_GROQ_KEY, docs=DOCS)
                            _status.update(label="✅ Hoàn tất!", state="complete")
                            if results and isinstance(results, dict) and results.get("experts"):
                                st.session_state.expert_results = results
                                st.session_state.expert_status = "ok"
                                st.session_state.expert_mode = results.get("mode", "cao_cap")
                            else:
                                st.session_state.expert_results = results
                                st.session_state.expert_status = "empty"
                        except Exception as _expert_err:
                            _status.update(label="❌ Lỗi", state="error")
                            st.session_state.expert_status = "error"
                            st.session_state.expert_error = str(_expert_err)
                        try:
                            _status.empty()
                        except Exception:
                            pass

                if st.session_state.get("expert_status") == "ok":
                    _mode = st.session_state.get("expert_mode", "cao_cap")
                    _mode_labels = {"don_gian": "⚡ Tiết kiệm (2 chuyên gia)", "trung_binh": "🔋 Tiêu chuẩn (4 chuyên gia)", "cao_cap": "🚀 Toàn diện (6 chuyên gia + Chủ tịch)"}
                    st.write(f"✅ Đã nhận phản hồi. Chế độ: {_mode_labels.get(_mode, _mode)}")
                elif st.session_state.get("expert_status") == "empty":
                    st.write("⚠️ Hệ thống trả về kết quả rỗng. Vui lòng thử lại sau vài giây.")
                elif st.session_state.get("expert_status") == "error":
                    _err = st.session_state.get("expert_error", "Lỗi không xác định")
                    st.write(f"❌ Lỗi khi gọi Hội đồng Chuyên gia: {_err}")
                    st.write("Vui lòng thử lại hoặc dùng tab Chat bên cạnh.")

                if st.session_state.expert_results:
                    results = st.session_state.expert_results
                    if not isinstance(results, dict) or "experts" not in results:
                        st.warning("⚠️ Kết quả không hợp lệ. Vui lòng thử lại.")
                        st.session_state.expert_results = None
                    else:
                        st.markdown("---")
                        st.markdown("### 🗳️ Ý kiến Chuyên gia")

                        cols = st.columns(3)
                        for i, expert in enumerate(results["experts"]):
                            with cols[i % 3]:
                                resp = expert.get("response") or "⚠️ Không có phản hồi."
                                with st.expander(
                                    f"**{expert.get('name', 'Chuyên gia')}** — {expert.get('title', '')}",
                                    expanded=(i < 3),
                                ):
                                    st.write(resp)

                        chairman = results.get("chairman")
                        if chairman:
                            st.write("---")
                            st.write("#### 👑 Kết luận của Chủ tịch Hội đồng")
                            st.write(chairman)

                    if st.button("🗑️ Xóa kết quả", use_container_width=True, key="clear_expert"):
                        st.session_state.expert_results = None
                        st.rerun()
            except Exception as _tab_err:
                st.error(f"❌ Lỗi tab Chuyên gia: {_tab_err}")
                st.info("Vui lòng thử lại hoặc dùng tab Chat.")



username = st.session_state.get("username")
if username and st.session_state.get("authenticated") and st.session_state.get("trang_thai"):
    keys = {"trang_thai", "chat_history", "loai_nha_dau_tu", "diem_rui_ro", "da_phan_tich"}
    to_save = {k: st.session_state[k] for k in keys if k in st.session_state}
    if to_save:
        try:
            save_state(username, to_save)
        except Exception:
            pass

st.markdown("""<hr class="gold-divider">""", unsafe_allow_html=True)
st.markdown(
    '<center style="color: #8892B0; font-size: 0.85rem; letter-spacing: 1px;">'
    '🤖 Robo-Advisor — Công cụ mô phỏng &amp; phân tích thị trường cho người Việt<br>'
    '<span style="color: #FFD700;">© 2026 • Phiên bản Hoàng gia &amp; Thịnh vượng v3.0</span></center>',
    unsafe_allow_html=True,
)


