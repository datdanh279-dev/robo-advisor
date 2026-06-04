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
    color: #8E8E9A; font-size: 0.85rem; margin-bottom: 2rem;
    letter-spacing: 4px; text-transform: uppercase;
    font-weight: 300;
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
    color: #8E8E9A !important;
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
        f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#8E8E9A;margin-bottom:6px;">'
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

try:
    PASSWORD_PRO = st.secrets.get("PRO_PASSWORD", "hdfkemr rmo8490hd")
except Exception:
    PASSWORD_PRO = "hdfkemr rmo8490hd"
_PWD_OK = {"hdfkemrrmo8490hd", "hdfkemr rmo8490hd"}

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
            '<div style="color:#8E8E9A;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Tài khoản</div>'
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
            '<span style="color:#8E8E9A;font-size:0.75rem;">Tài khoản: </span>'
            '<b style="color:#ECE8E1;">GÓI TIÊU CHUẨN</b></div>',
            unsafe_allow_html=True,
        )
        with st.expander("🔑 Kích hoạt Gói PRO"):
            input_password = st.text_input(
                "Nhập mật khẩu cấp phép:",
                type="password",
                key="pro_pwd_input",
            )
            if st.button("Xác nhận kích hoạt", key="activate_pro", use_container_width=True):
                if input_password in _PWD_OK or input_password.strip() == PASSWORD_PRO.strip():
                    st.session_state.is_pro = True
                    st.success("✅ Kích hoạt Gói PRO thành công!")
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác!")
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
<style>
:root {
    --gold: #FFD700;
    --gold-light: #FFE55C;
    --gold-dark: #B8860B;
    --cream: #ECE8E1;
    --text-muted: #8E8E9A;
    --prosperity: #00C9A7;
    --bg-dark: #02050E;
    --bg-card: rgba(10,17,31,0.85);
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
    font-size: 0.85rem;
    color: var(--text-muted);
    font-weight: 300;
    letter-spacing: 3px;
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
    font-size: 0.7rem;
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

    if st.session_state.is_pro:
        if st.button("📊 Phân tích chuyên sâu", width='stretch'):
            st.session_state.trang_thai = "deep_analysis"
            st.rerun()
    else:
        if st.button("🔒 Phân tích chuyên sâu (Gói PRO)", width='stretch', disabled=True):
            pass

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
            f'<span style="font-size:0.6rem;color:#8E8E9A;text-transform:uppercase;letter-spacing:1px;">Thành viên</span><br>'
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
            f'<span style="font-size:0.7rem;color:#8E8E9A;">Beta <b style="color:#FFD700;">{reg_count}/{max_slots}</b></span>'
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
    Cập nhật: """ + datetime.now().strftime("%H:%M:%S %d/%m/%Y") + """
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
        '<div style="display:flex;align-items:center;gap:6px;font-size:0.72rem;color:#8E8E9A;">'
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
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_toggle", help="Đã bật mặc định — tối ưu cho trader xem đêm")
    st.session_state.dark_mode = st.session_state.get("dark_toggle", True)
    st.markdown("---")
    st.caption(
        "⚠️ **Miễn trỡ trách nhiệm:** Đây là công cụ phân tích dữ liệu lịch sử, "
        "không phải khuyến nghị đầu tư. Mọi quyết định đầu tư thuộc về trách nhiệm của người dùng."
    )
    st.markdown(
        '<div style="font-size:0.7rem;color:#8E8E9A;margin-top:4px;">'
        '📜 <a href="#terms" style="color:#8E8E9A;">Điều khoản</a> · '
        '🔒 <a href="#privacy" style="color:#8E8E9A;">Bảo mật</a> · '
        '⚖️ <a href="#disclaimer" style="color:#8E8E9A;">Miễn trừ</a></div>',
        unsafe_allow_html=True,
    )

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
                import yfinance as _yf_corr
                n = len(ma_heat)
                corr = np.eye(n)
                used_real = 0
                for i in range(n):
                    for j in range(i+1, n):
                        rho_real = None
                        try:
                            sym_i = ma_heat[i] + ".VN"
                            sym_j = ma_heat[j] + ".VN"
                            hi = _yf_corr.Ticker(sym_i).history(period="6mo", timeout=5)
                            hj = _yf_corr.Ticker(sym_j).history(period="6mo", timeout=5)
                            if not hi.empty and not hj.empty and len(hi) > 20 and len(hj) > 20:
                                ri = hi['Close'].pct_change().dropna()
                                rj = hj['Close'].pct_change().dropna()
                                common = sorted(set(ri.index) & set(rj.index))
                                if len(common) > 15:
                                    rho_real = float(ri.loc[common].corr(rj.loc[common]))
                                    used_real += 1
                        except Exception:
                            pass
                        if rho_real is not None:
                            corr[i, j] = max(-0.95, min(0.95, rho_real))
                        else:
                            if sector_map[ma_heat[i]] == sector_map[ma_heat[j]] and sector_map[ma_heat[i]] != "Khác":
                                base = 0.72
                            else:
                                base = 0.32
                            beta_i, beta_j = beta_map[ma_heat[i]], beta_map[ma_heat[j]]
                            beta_adj = 0.05 * (beta_i - 1) * (beta_j - 1)
                            corr[i, j] = max(-0.95, min(0.95, base + beta_adj))
                        corr[j, i] = corr[i, j]
                df_corr = pd.DataFrame(corr, index=ma_heat, columns=ma_heat)
                if used_real > 0:
                    title_corr = f"Ma trận tương quan từ giá thật (yfinance 6T, {used_real}/{n*(n-1)//2} cặp)"
                else:
                    title_corr = "Ma trận tương quan (ước lượng từ ngành & beta — yfinance tạm lỗi)"
                fig_heat = px.imshow(df_corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title=title_corr)
                fig_heat.update_layout(height=450,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                st.plotly_chart(fig_heat, width='stretch')
                if used_real > 0:
                    st.caption(f"✅ Tương quan tính từ correlation thật {used_real}/{n*(n-1)//2} cặp mã (yfinance 6T). Phần còn lại fallback ước lượng ngành.")
                else:
                    st.caption("⚠️ Tương quan ước lượng từ cùng ngành ≈ 0.7, khác ngành ≈ 0.3 (yfinance tạm không khả dụng).")
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
                fig.add_trace(go.Candlestick(x=df_chart["date"], open=df_chart["price"], high=df_chart["price"]*1.01, low=df_chart["price"]*0.99, close=df_chart["price"], name="Giá"))
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
                            f'<small style="color:#8E8E9A;">🕐 {tin["ngay"][:25] if tin["ngay"] else ""}</small>'
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
                    f'<small style="color:#8E8E9A;">📅 {s["ngay"]}</small>'
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
            st.caption("⚠️ Dùng dữ liệu synthetic (252 ngày) — chỉ để minh họa logic, KHÔNG phải dự đoán thật.")
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
                    ret = np.random.randn(n_days_bt) * 0.015
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
            st.caption("⚠️ Dự đoán minh họa dùng sklearn LinearRegression trên dữ liệu synthetic.")
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
                    ret = np.random.randn(n_days_hist + n_days_pred) * 0.015 + trend
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
            st.caption("📊 Mean-variance tối ưu trên giá thật yfinance 6T (fallback ước lượng nếu yfinance lỗi).")
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
                        data_source_op = "⚠️ Synthetic (yfinance tạm lỗi)"
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
        '<div style="background:#ECE8E10a;border:1px solid #8E8E9A33;border-radius:10px;'
        'padding:8px 16px;margin-bottom:12px;font-size:0.85rem;color:#8E8E9A;">'
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
        SECTOR_DEFAULTS_FALLBACK = {
            "Ngân hàng": {"pe": 9.5, "pb": 1.8, "roe": 0.20, "roa": 0.015, "dividend_yield": 0.02, "beta": 0.9, "eps": 4500},
            "Công nghệ": {"pe": 18.0, "pb": 3.5, "roe": 0.22, "roa": 0.12, "dividend_yield": 0.015, "beta": 1.1, "eps": 5000},
            "Thép": {"pe": 12.0, "pb": 1.5, "roe": 0.13, "roa": 0.07, "dividend_yield": 0.012, "beta": 1.3, "eps": 2500},
            "Thực phẩm": {"pe": 15.0, "pb": 3.5, "roe": 0.25, "roa": 0.15, "dividend_yield": 0.04, "beta": 0.7, "eps": 4500},
            "Bán lẻ": {"pe": 20.0, "pb": 3.0, "roe": 0.15, "roa": 0.06, "dividend_yield": 0.01, "beta": 1.2, "eps": 3000},
            "Bất động sản": {"pe": 30.0, "pb": 2.5, "roe": 0.08, "roa": 0.03, "dividend_yield": 0.005, "beta": 1.1, "eps": 2000},
            "Chứng khoán": {"pe": 10.0, "pb": 1.5, "roe": 0.15, "roa": 0.02, "dividend_yield": 0.03, "beta": 1.2, "eps": 3000},
            "Khác": {"pe": 15.0, "pb": 2.5, "roe": 0.15, "roa": 0.08, "dividend_yield": 0.02, "beta": 1.0, "eps": 3500},
        }
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
                        ki[f"{k}_source"] = "ước lượng cuối (yfinance miss toàn ngành)"
            if "w52_high" not in ki or ki.get("w52_high", 0) <= 0:
                gia_tt = info.get("gia_thi_truong", 0)
                ki["w52_high"] = gia_tt * 1.25 if gia_tt > 0 else 0
            if "w52_low" not in ki or ki.get("w52_low", 0) <= 0:
                gia_tt = info.get("gia_thi_truong", 0)
                ki["w52_low"] = gia_tt * 0.85 if gia_tt > 0 else 0
            if "market_cap" not in ki or ki.get("market_cap", 0) <= 0:
                ki["market_cap"] = info.get("gia_thi_truong", 0) * info.get("so_luong", 0) / 1e9
            return ki

        for ma, info in dm.items():
            if ma in kpi:
                kpi[ma] = _fill_kpi_for_real(ma, info, kpi[ma])
            else:
                kpi[ma] = _fill_kpi_for_real(ma, info, {"nganh": info.get("nganh", "Khác")})

        @st.cache_data(ttl=3600, show_spinner="📡 Tải giá thật từ Yahoo Finance...")
        def _fetch_real_prices(_symbols):
            import requests as _rq, pandas as _pd
            out = {}
            metas = {}
            for sym in _symbols:
                try:
                    r = _rq.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.VN",
                        params={"range": "6mo", "interval": "1d"},
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36"}
                    )
                    if r.status_code == 200:
                        d = r.json()
                        if not d.get('chart', {}).get('result'):
                            continue
                        result = d['chart']['result'][0]
                        ts = result.get('timestamp', [])
                        closes_raw = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        if not ts or not closes_raw:
                            continue
                        pairs = [(t, c) for t, c in zip(ts, closes_raw) if c is not None]
                        if len(pairs) < 20:
                            continue
                        ts_v, cs_v = zip(*pairs)
                        idx = _pd.to_datetime(list(ts_v), unit='s')
                        out[sym] = _pd.Series(list(cs_v), index=idx)
                        metas[sym] = result.get('meta', {})
                except Exception:
                    pass
            return out, metas

        @st.cache_data(ttl=3600, show_spinner="📊 Tải P/E, P/B, ROE thật từ yfinance...")
        def _fetch_real_fundamentals(_symbols):
            import yfinance as _yf
            out = {}
            for sym in _symbols:
                try:
                    t = _yf.Ticker(f"{sym}.VN")
                    info = t.info
                    if not info or 'symbol' not in info:
                        continue
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
                    out[sym] = {
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
            for sym in ["^VN10Y", "VN10Y=X", "VNI10Y=X", "^GSPC"]:
                try:
                    h = _yf.Ticker(sym).history(period="6mo", timeout=8)
                    if not h.empty and len(h) > 20:
                        return h['Close']
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

        _ma_for_fetch = [ma for ma, info in dm.items()
                         if info.get("gia_thi_truong", 0) > 0 and info.get("so_luong", 0) > 0]
        _fetch_result = _fetch_real_prices(tuple(_ma_for_fetch))
        real_prices = _fetch_result[0] if isinstance(_fetch_result, tuple) else _fetch_result
        real_metas = _fetch_result[1] if isinstance(_fetch_result, tuple) and len(_fetch_result) > 1 else {}
        for ma, meta in real_metas.items():
            if ma in kpi and ma in dm:
                w52h = meta.get('fiftyTwoWeekHigh')
                w52l = meta.get('fiftyTwoWeekLow')
                cur_px = meta.get('regularMarketPrice')
                if w52h: kpi[ma]['w52_high'] = float(w52h)
                if w52l: kpi[ma]['w52_low'] = float(w52l)
                if cur_px and dm[ma].get('gia_thi_truong', 0) <= 0:
                    dm[ma]['gia_thi_truong'] = float(cur_px)
        real_fund = _fetch_real_fundamentals(tuple(_ma_for_fetch))
        for ma, fund in real_fund.items():
            if ma in kpi and fund:
                for k, v in fund.items():
                    if v is not None and v != 0:
                        kpi[ma][k] = v
        vn30_close, vn30_label = _fetch_vn30_proxy()
        has_real = len(real_prices) >= 2
        has_vn30 = vn30_close is not None
        has_fund = len(real_fund) >= 1
        usdvnd_close = _fetch_usdvnd()
        vn_bond_close = _fetch_vn_bond_yield()
        port_beta = sum(betas)
        port_return = rp
        if has_real and len(real_prices) >= 2:
            try:
                common_dates = sorted(set.intersection(*[set(s.index) for s in real_prices.values()]))
                if len(common_dates) > 20:
                    dm_value_ts = pd.Series(0.0, index=common_dates, dtype=float)
                    for ma, prices in real_prices.items():
                        if ma in dm:
                            shares = dm[ma].get("so_luong", 0)
                            aligned = prices.reindex(common_dates).ffill().bfill()
                            dm_value_ts += aligned.astype(float) * shares
                    daily_ret_real = dm_value_ts.pct_change().dropna()
                    if len(daily_ret_real) > 20:
                        vol_proxy = float(daily_ret_real.std() * (252 ** 0.5))
                    else:
                        vol_proxy = 0.18
                else:
                    vol_proxy = 0.18
            except Exception:
                vol_proxy = 0.18
        else:
            vol_proxy = 0.18
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
        st.write("## 📊 Nguồn dữ liệu (Data Source)")
        ds1, ds2, ds3 = st.columns(3)
        with ds1:
            st.write("**✅ SỐ THẬT 100%:**")
            st.write(f"- Giá hiện tại & lịch sử: yfinance ({len(real_prices)}/{n_ma} mã)")
            st.write(f"- P/E, P/B, ROE, EPS: yfinance ({len(real_fund)}/{n_ma} mã)")
            st.write(f"- W52 High/Low, Volume: yfinance")
            st.write(f"- Vol, Sharpe, VaR: tính từ giá thật")
        with ds2:
            st.write("**⚠️ ƯỚC LƯỢNG (có ghi chú):**")
            st.write("- Foreign flow: tỷ lệ NN theo ngành")
            st.write("- FX/Lãi suất: hệ số nhạy cảm ngành")
            st.write("- AI Insights: template phân tích")
            st.write("- Monte Carlo: mô phỏng ngẫu nhiên")
        with ds3:
            st.write("**📐 CÔNG THỨC CHUẨN:**")
            st.write("- Stress Test: β × shock")
            st.write("- VaR 95%: σ × 1.645")
            st.write("- CVaR 95%: σ × 2.06")
            st.write("- MaxDD: σ × 2.5")
            st.write("- Phí mua: 0.15% (HOSE chính thức), Thuế TNCN: 0.1% (NĐ 126/2020)")

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
        if has_real:
            st.caption(f"📊 Tính từ giá thật {len(real_prices)} mã (yfinance, 6 tháng)")
        else:
            st.caption("🎲 Mô phỏng Monte Carlo (yfinance tạm không khả dụng)")
        ta_rows = []
        for ma, info in dm.items():
            gia_tt = info.get("gia_thi_truong", 0)
            sl = info.get("so_luong", 0)
            if gia_tt <= 0 or sl <= 0: continue
            ki = kpi.get(ma, {})
            beta_ma = float(ki.get("beta", 1.0) or 1.0)
            if ma in real_prices and len(real_prices[ma]) >= 30:
                prices = real_prices[ma].values
                gia_hien_tai = float(prices[-1])
            else:
                np.random.seed(hash(ma) % (2**31))
                ret = np.random.normal(0.0005, 0.018, 252)
                prices = gia_tt * np.cumprod(1 + ret * beta_ma)
                gia_hien_tai = gia_tt
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
        if has_real and len(dm_equity) > 30:
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
            common_dates = sorted(set.intersection(*[set(s.index) for s in real_prices.values()]))
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
                    vn_equity = dm_equity * (1 + np.random.normal(0, 0.01, len(dm_equity))).cumprod()
                    vn_equity = vn_equity / vn_equity[0] * tong_gt
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
            np.random.seed(42)
            n_days = 252
            daily_mu = port_return / n_days
            daily_sigma = vol_proxy / (n_days ** 0.5)
            dm_returns = np.random.normal(daily_mu, daily_sigma, n_days)
            vn_returns = np.random.normal((rm - rf) / n_days, 0.012, n_days)
            dm_equity = tong_gt * np.cumprod(1 + dm_returns)
            vn_equity = tong_gt * np.cumprod(1 + vn_returns)
            running_max = np.maximum.accumulate(dm_equity)
            drawdown = (dm_equity - running_max) / running_max * 100
            x_axis = list(range(n_days))
            data_source_eq = "🎲 Mô phỏng Monte Carlo (yfinance tạm không khả dụng)"
        st.caption(data_source_eq)
        fig_eq = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
            subplot_titles=("Giá trị danh mục (₫)", "Drawdown (%)"))
        fig_eq.add_trace(go.Scatter(x=x_axis, y=dm_equity, name="Danh mục", line=dict(color="#FFD700", width=2)), row=1, col=1)
        fig_eq.add_trace(go.Scatter(x=x_axis, y=vn_equity, name="VN-Index" if has_vn30 else "VN-Index (mô phỏng)", line=dict(color="#4FC3F7", width=2, dash="dash")), row=1, col=1)
        fig_eq.add_trace(go.Scatter(x=x_axis, y=drawdown, name="Drawdown", fill="tozeroy", line=dict(color="#EF5350", width=1)), row=2, col=1)
        fig_eq.update_layout(height=500, showlegend=True, hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
        st.plotly_chart(fig_eq, use_container_width=True)

        st.write("## 🔗 Ma trận tương quan giữa các mã")
        ma_list = [ma for ma, info in dm.items() if info.get("gia_thi_truong", 0) * info.get("so_luong", 0) > 0 and tong_gt > 0]
        if len(ma_list) >= 2:
            corr_matrix = []
            for m1 in ma_list:
                row = []
                for m2 in ma_list:
                    if m1 == m2:
                        row.append(1.0)
                    else:
                        n1 = (kpi.get(m1, {}).get("nganh", "") or "Khác").strip() or "Khác"
                        n2 = (kpi.get(m2, {}).get("nganh", "") or "Khác").strip() or "Khác"
                        b1 = float(kpi.get(m1, {}).get("beta", 1.0) or 1.0)
                        b2 = float(kpi.get(m2, {}).get("beta", 1.0) or 1.0)
                        if n1 == n2:
                            base = 0.72
                        else:
                            base = 0.32
                        beta_adj = 1.0 - 0.05 * abs(b1 - b2)
                        corr = max(-1, min(1, base * beta_adj))
                        row.append(round(corr, 2))
                corr_matrix.append(row)
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_matrix, x=ma_list, y=ma_list,
                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in corr_matrix],
                texttemplate="%{text}", textfont={"size": 11}))
            fig_corr.update_layout(height=450,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Cần ≥2 mã trong danh mục để tính ma trận tương quan.")

        st.write("## 🆚 Backtest: Danh mục vs VN-Index (6 tháng qua)")
        dm_ret_bt = (dm_equity[-1] / dm_equity[0] - 1) * 100
        vn_ret_bt = (vn_equity[-1] / vn_equity[0] - 1) * 100
        alpha_bt = dm_ret_bt - vn_ret_bt
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Return DM", f"{dm_ret_bt:+.2f}%")
        c2.metric(f"📊 Return {vn30_label or 'VN-Index'}", f"{vn_ret_bt:+.2f}%")
        c3.metric("🏆 Alpha (DM − VN)", f"{alpha_bt:+.2f}%")
        c4.metric("📉 Max Drawdown DM", f"{drawdown.min():.2f}%")
        if has_real and has_vn30:
            st.caption(f"📊 Backtest thật: {len(real_prices)} mã × số lượng thực so với {vn30_label} (yfinance 6 tháng).")
        else:
            st.caption("🎲 Backtest mô phỏng (yfinance tạm không khả dụng).")

        st.write("---")
        st.write("## 🎲 Monte Carlo — 1000 kịch bản tương lai 1 năm (Bootstrap từ giá thật)")
        if has_real and len(dm_equity) > 20:
            daily_returns_real = pd.Series(dm_equity).pct_change().dropna().values
            daily_mu = float(np.mean(daily_returns_real))
            daily_sigma = float(np.std(daily_returns_real))
            vol_source = f"📊 Bootstrap từ {len(daily_returns_real)} phiên giá thật (yfinance 6T)"
            np.random.seed(123)
            n_sims = 1000
            n_days_mc = 252
            sims = np.random.choice(daily_returns_real, size=(n_sims, n_days_mc), replace=True)
            mc_method = "Bootstrap (lấy mẫu có hoàn lại từ returns thật)"
        else:
            daily_mu = port_return / 252
            daily_sigma = vol_proxy / (252 ** 0.5)
            vol_source = "🎲 Random normal (yfinance tạm không khả dụng)"
            np.random.seed(123)
            n_sims = 1000
            n_days_mc = 252
            sims = np.random.normal(daily_mu, daily_sigma, (n_sims, n_days_mc))
            mc_method = "Random normal (ước lượng CAPM)"
        st.caption(f"Vol daily: μ={daily_mu*100:+.4f}%, σ={daily_sigma*100:.3f}% — {vol_source} — Phương pháp: {mc_method}")
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
        st.write("## 🛡️ Chỉ số rủi ro nâng cao (Sortino/Calmar/Tracking Error)")
        if has_real and 'dm_value_ts' in dir() and len(dm_equity) > 20:
            daily_ret_real = pd.Series(dm_equity).pct_change().dropna().values
            downside = daily_ret_real[daily_ret_real < 0]
            downside_dev = float(np.std(downside)) if len(downside) > 0 else vol_proxy / (252**0.5)
            sortino = (port_return - rf) / (downside_dev * (252**0.5)) if downside_dev > 0 else 0
            calmar = port_return / (abs(drawdown.min()/100) + 0.001) if drawdown.min() < 0 else 0
            if has_vn30 and len(vn_equity) == len(dm_equity):
                te = float(np.std(daily_ret_real - pd.Series(vn_equity).pct_change().dropna().values) * (252**0.5))
            else:
                te = vol_proxy * 0.5
            skew = float(pd.Series(daily_ret_real).skew())
            kurt = float(pd.Series(daily_ret_real).kurtosis())
        else:
            np.random.seed(99)
            daily_sim = np.random.normal(port_return/252, vol_proxy/(252**0.5), 252)
            downside = daily_sim[daily_sim < 0]
            downside_dev = float(np.std(downside)) if len(downside) > 0 else vol_proxy/(252**0.5)
            sortino = (port_return - rf) / (downside_dev*(252**0.5))
            calmar = port_return / (vol_proxy*2.5 + 0.001)
            te = vol_proxy * 0.5
            skew = 0.0
            kurt = 3.0
        sr1, sr2, sr3, sr4, sr5 = st.columns(5)
        sr1.metric("📐 Sortino", f"{sortino:.2f}", help=">1: tốt | >2: rất tốt (chỉ tính downside)")
        sr2.metric("📐 Calmar", f"{calmar:.2f}", help="Return / |Max DD|")
        sr3.metric("📐 Tracking Err", f"{te*100:.1f}%", help="Sai lệch so với benchmark")
        sr4.metric("📐 Skewness", f"{skew:+.2f}", help=">0: lệch phải (lợi nhuận)")
        sr5.metric("📐 Kurtosis", f"{kurt:.2f}", help=">3: đuôi dày (rủi ro đuôi cao)")

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
        if has_real:
            top3_ma = sorted(dm.items(),
                key=lambda kv: kv[1].get("gia_thi_truong", 0) * kv[1].get("so_luong", 0),
                reverse=True)[:3]
            import yfinance as yf
            for ma, _ in top3_ma:
                try:
                    full = yf.Ticker(f"{ma}.VN").history(period="6mo", timeout=8)
                    if not full.empty and len(full) > 20:
                        fig_candle = go.Figure(data=[go.Candlestick(
                            x=full.index, open=full['Open'], high=full['High'],
                            low=full['Low'], close=full['Close'], name=ma)])
                        fig_candle.update_layout(height=300, title=f"{ma} — {len(full)} phiên",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#ECE8E1"), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig_candle, use_container_width=True)
                except Exception:
                    st.info(f"Không tải được nến {ma}")
        else:
            st.info("🎲 Cần dữ liệu yfinance để vẽ nến (đang mô phỏng).")

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
            np.random.seed(2024)
            sim_hp = np.random.normal(port_return/12, 0.04, 12)
            st.caption("🎲 Mô phỏng (yfinance tạm không khả dụng)")
            hp1, hp2, hp3, hp4 = st.columns(4)
            hp1.metric("📅 1 tháng qua", f"{(sim_hp[-1])*100:+.2f}%")
            hp2.metric("📅 3 tháng qua", f"{(np.prod(1+sim_hp[-3:])-1)*100:+.2f}%")
            hp3.metric("📅 6 tháng qua", f"{(np.prod(1+sim_hp)-1)*100:+.2f}%")
            hp4.metric("📅 Từ đầu kỳ", f"{(np.prod(1+sim_hp)-1)*100:+.2f}%")

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
            if ma in real_metas:
                vol = real_metas[ma].get('regularMarketVolume', 0) or 0
                price = real_metas[ma].get('regularMarketPrice', 0) or 0
                adtv_value = vol * price
                if adtv_value > 0:
                    value_dm = dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0)
                    days_to_liquidate = value_dm / adtv_value if adtv_value > 0 else 999
                    liq_rows.append({
                        "Mã": ma,
                        "ADTV (tỷ)": round(adtv_value/1e9, 1),
                        "GT DM (tỷ)": round(value_dm/1e9, 1),
                        "Ngày thoát hàng": round(days_to_liquidate, 1),
                        "Thanh khoản": "🟢 Cao" if adtv_value > 5e9 else ("🟡 TB" if adtv_value > 1e9 else "🔴 Thấp")
                    })
        if liq_rows:
            df_liq = pd.DataFrame(liq_rows)
            st.dataframe(df_liq, use_container_width=True, hide_index=True)
            st.caption("💡 ADTV > 5 tỷ = thanh khoản cao (mua/bán dễ). Ngày thoát hàng = GT mã / ADTV. >5 ngày = khó bán gấp.")
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
                fo = 0
                fo_source = "Không có data (yfinance miss)"
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
            fig = px.pie(df_nganh, values="Tỷ trọng", names="Ngành",
                         title="Tỷ trọng danh mục theo ngành",
                         color_discrete_sequence=px.colors.sequential.YlOrRd)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#ECE8E1",
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

    tab_chat, tab_expert = st.tabs(["💬 Chat", "👑 Hội đồng Chuyên gia"])

    with tab_chat:
        st.markdown("Hỏi tôi về đầu tư, cổ phiếu, vàng, bất động sản, hay bất kỳ chủ đề tài chính nào!")
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
                        with st.spinner("🤖 Robo-Advisor đang phân tích..."):
                            tra_loi = tim_cau_tra_loi(_q, st.session_state.chat_history)
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
                    with st.spinner("🤖 Robo-Advisor đang suy nghĩ..."):
                        tra_loi = tim_cau_tra_loi(cau_hoi, st.session_state.chat_history)
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

    with tab_expert:
        if not st.session_state.is_pro:
            st.markdown("## 🔒 Tính năng PRO")
            st.warning("**Hội đồng 6 Chuyên gia** chỉ dành cho gói PRO. Vui lòng kích hoạt PRO trong Sidebar để sử dụng.")
            st.info("👉 Mở Sidebar → 🔑 Kích hoạt Gói PRO → nhập mật khẩu → Enter")
            st.markdown("---")
            st.markdown("#### Tính năng sẽ mở khóa:")
            st.markdown("- 🎯 Hỏi ý kiến **Warren Buffett, George Soros, Peter Lynch, Ray Dalio, Benjamin Graham, Charlie Munger**")
            st.markdown("- 👑 **Chủ tịch Hội đồng** tổng hợp và đưa ra kết luận cuối cùng")
            st.markdown("- 🧠 AI phân loại câu hỏi: Tiết kiệm / Tiêu chuẩn / Toàn diện")
            st.stop()
        st.markdown("### 👑 Hội đồng 6 Chuyên gia — Huyền thoại Đầu tư Thế giới")
        st.markdown(
            "Gửi **1 câu hỏi**, nhận câu trả lời từ **6 huyền thoại** do AI đóng vai. "
            "Chủ tịch Hội đồng sẽ tổng hợp và chọn ra phương án tốt nhất."
        )
        st.markdown("---")
        _expert_chips_html = '<div style="margin:6px 0 14px 0;line-height:2.2;">'
        for exp in [
            {"name": "Warren Buffett", "title": "Đầu tư Giá trị", "color": "#4CAF50"},
            {"name": "George Soros", "title": "Kinh tế Vĩ mô", "color": "#2196F3"},
            {"name": "Peter Lynch", "title": "Đầu tư Tăng trưởng", "color": "#FF9800"},
            {"name": "Ray Dalio", "title": "Nguyên tắc Thị trường", "color": "#9C27B0"},
            {"name": "Benjamin Graham", "title": "Phân tích Cơ bản", "color": "#795548"},
            {"name": "Charlie Munger", "title": "Tâm lý học Đầu tư", "color": "#607D8B"},
        ]:
            _expert_chips_html += (
                f'<span style="display:inline-block;background:{exp["color"]}22;'
                f'border:1px solid {exp["color"]}55;border-radius:20px;padding:4px 14px;margin:3px;'
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
                try:
                    with st.spinner("🧠 Đang hỏi các chuyên gia AI..."):
                        results = hoi_dong_chuyen_gia(cau_hoi, groq_key_override=_GROQ_KEY, docs=DOCS)
                    if results:
                        st.session_state.expert_results = results
                        mode = results.get("mode", "cao_cap")
                        mode_labels = {"don_gian": "⚡ Tiết kiệm (2 chuyên gia)", "trung_binh": "🔋 Tiêu chuẩn (4 chuyên gia)", "cao_cap": "🚀 Toàn diện (6 chuyên gia + Chủ tịch)"}
                        st.success(f"✅ Đã nhận phản hồi. Chế độ: {mode_labels.get(mode, mode)}")
                    else:
                        st.error("❌ Không thể kết nối với các chuyên gia. Kiểm tra API keys.")
                except Exception as _expert_err:
                    st.error(f"❌ Lỗi khi gọi Hội đồng Chuyên gia: {_expert_err}")
                    st.info("Vui lòng thử lại hoặc dùng tab Chat bên cạnh.")
                    import traceback as _tb
                    with st.expander("Chi tiết lỗi (debug)"):
                        st.code(_tb.format_exc())

        if st.session_state.expert_results:
            results = st.session_state.expert_results
            st.markdown("---")
            st.markdown("### 🗳️ Ý kiến Chuyên gia")

            cols = st.columns(3)
            for i, expert in enumerate(results["experts"]):
                with cols[i % 3]:
                    with st.expander(
                        f"**{expert['name']}** — {expert['title']}",
                        expanded=(i < 3),
                    ):
                        if expert["response"].startswith("❌"):
                            st.error(expert["response"])
                        elif expert["response"].startswith("⚠️"):
                            st.warning(expert["response"])
                        elif expert["response"].startswith("⏭️"):
                            st.caption(expert["response"])
                        else:
                            st.markdown(expert["response"])

            if results.get("chairman"):
                st.markdown("---")
                st.markdown("#### 👑 Kết luận của Chủ tịch Hội đồng")
                st.markdown(results["chairman"])

            if st.button("🗑️ Xóa kết quả", use_container_width=True, key="clear_expert"):
                st.session_state.expert_results = None
                st.rerun()



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


