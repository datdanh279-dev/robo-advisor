import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

_T0 = datetime.now()

from backend.risk_profile import (
    CAU_HOI_KHAO_SAT,
    LOAI_NHA_DAU_TU,
    danh_gia_rui_ro,
    phan_bo_danh_muc,
)
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
)
from backend.chat_advisor import tim_cau_tra_loi
from backend.calculations import (
    phan_tich_lich_su,
    phan_tich_danh_muc_nang_cao,
    tinh_tuong_quan,
)
from backend.database import save_state, load_state, save_chat, load_chat, ensure_user, count_users, register_beta_user, verify_user, is_founding_member, get_beta_progress, BETA_MAX, reset_password
_T1 = datetime.now(); print(f"[TRACE] backend imports: {(_T1-_T0).total_seconds():.3f}s", file=__import__('sys').stderr)

st.set_page_config(
    page_title="Robo-Advisor AI - Đầu tư thông minh",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
_T2 = datetime.now(); print(f"[TRACE] set_page_config: {(_T2-_T1).total_seconds():.3f}s", file=__import__('sys').stderr)

import random
import json
import os as os_mod
from dotenv import load_dotenv
load_dotenv()
import streamlit.components.v1 as components
import sys, traceback
_T3 = datetime.now(); print(f"[TRACE] stdlib/dotenv: {(_T3-_T2).total_seconds():.3f}s", file=__import__('sys').stderr)
try:
    from backend.data_loader import DOCS, load_all
except Exception:
    print("=" * 60, file=sys.stderr)
    print("ERROR importing backend.data_loader:", file=sys.stderr)
    traceback.print_exc()
    print("=" * 60, file=sys.stderr)
    DOCS = {}
    def load_all():
        pass
_T4 = datetime.now(); print(f"[TRACE] data_loader import: {(_T4-_T3).total_seconds():.3f}s", file=__import__('sys').stderr)

@st.cache_data(ttl=3600, show_spinner="Đang tải dữ liệu thị trường...")
def _khoi_tao_dulieu():
    print("[TRACE] _khoi_tao_dulieu called", file=__import__('sys').stderr)
    load_all()
    print("[TRACE] _khoi_tao_dulieu done", file=__import__('sys').stderr)
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
    user = st.secrets.get("auth", {}).get("username") or os_mod.environ.get("KGU_USER")
    pwd  = st.secrets.get("auth", {}).get("password") or os_mod.environ.get("KGU_PASS")
    if user and pwd:
        return username == user and password == pwd
    return False

def tao_ma_otp():
    return f"{random.randint(100000, 999999)}"

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

#root { background: linear-gradient(135deg, #02050E, #070B19, #0A111F); }
.stApp { background: linear-gradient(135deg, #02050E, #070B19, #0A111F); }
header[data-testid="stHeader"] { display: none; }
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
</style>
"""

def hien_thi_login():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
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
        f'<div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#FFD700,#C9A84C);border-radius:4px;transition:width 0.5s;"></div></div>'
        f'</div>'
        '<div class="login-box">',
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
                    ok = kiem_tra_dang_nhap(username, password) or verify_user(username, password)
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
            with st.form("reset_form"):
                reset_user = st.text_input("Tên đăng nhập", placeholder="Nhập username...", key="reset_user")
                reset_pass = st.text_input("Mật khẩu mới", type="password", placeholder="Nhập mật khẩu mới...", key="reset_pass")
                reset_submit = st.form_submit_button("🔄 Đặt lại mật khẩu")
                if reset_submit:
                    if len(reset_user) < 3:
                        st.error("Tên đăng nhập ít nhất 3 ký tự")
                    elif len(reset_pass) < 6:
                        st.error("Mật khẩu ít nhất 6 ký tự")
                    else:
                        try:
                            if reset_password(reset_user, reset_pass):
                                st.success("✅ Đặt lại mật khẩu thành công! Đăng nhập với mật khẩu mới.")
                            else:
                                st.error("Tên đăng nhập không tồn tại trong hệ thống Beta")
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
    st.markdown("</div></div>", unsafe_allow_html=True)

def hien_thi_otp():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="login-container">'
        f'<div class="login-title">🔐 Xác thực 2 lớp</div>'
        f'<div class="login-subtitle">Mã OTP đã gửi đến số điện thoại của bạn</div>'
        f'<div class="login-box">',
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
    st.markdown("</div></div>", unsafe_allow_html=True)

if not st.session_state.authenticated:
    if not st.session_state.password_ok:
        hien_thi_login()
    else:
        hien_thi_otp()
    _T5 = datetime.now(); print(f"[TRACE] login rendered: {(_T5-_T0).total_seconds():.3f}s", file=__import__('sys').stderr)
    st.stop()


_T6 = datetime.now(); print(f"[TRACE] past login, calling _khoi_tao_dulieu: {(_T6-_T0).total_seconds():.3f}s", file=__import__('sys').stderr)
_khoi_tao_dulieu()
_T7 = datetime.now(); print(f"[TRACE] _khoi_tao_dulieu returned: {(_T7-_T0).total_seconds():.3f}s", file=__import__('sys').stderr)


@st.cache_data(show_spinner=False)
def mo_phong_monte_carlo_cached(so_lan=1000):
    """Cache kết quả Monte Carlo — hàm tất định (seed=42) nên không cần tính lại mỗi lần rerun."""
    return mo_phong_monte_carlo(so_lan)



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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "da_phan_tich" not in st.session_state:
    st.session_state.da_phan_tich = False


sidebar = st.sidebar
with sidebar:
    st.markdown("## 🤖 Robo-Advisor")
    st.markdown("---")

    if st.button("🏠 Homepage", width='stretch'):
        st.session_state.trang_thai = "dashboard"
        st.rerun()

    if st.button("📝 Khảo sát rủi ro", width='stretch'):
        st.session_state.trang_thai = "survey"
        st.rerun()

    if st.button("📊 Danh mục đầu tư", width='stretch'):
        if st.session_state.get("da_phan_tich"):
            st.session_state.trang_thai = "portfolio"
        else:
            st.session_state.trang_thai = "portfolio"
            st.info("💡 Bạn chưa làm khảo sát rủi ro. Trang sẽ hiện danh mục thực tế và đề xuất mặc định.")
        st.rerun()

    if st.button("💬 Chat tư vấn", width='stretch'):
        st.session_state.trang_thai = "chat"
        st.rerun()

    if st.button("📊 Phân tích chuyên sâu", width='stretch'):
        st.session_state.trang_thai = "deep_analysis"
        st.rerun()

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
    Phí quản lý: <b style="color:#FFD700;">0,3%/năm</b><br>
    Đầu tư từ: <b style="color:#FFD700;">100.000 VNĐ</b><br>
    Cập nhật: """ + datetime.now().strftime("%H:%M %d/%m/%Y") + """
    </small>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("da_phan_tich"):
        loai = st.session_state.get("loai_nha_dau_tu", "")
        st.markdown("---")
        st.markdown(f"**Hồ sơ của bạn:** {loai}")
        st.markdown(f"**Điểm rủi ro:** {st.session_state.get('diem_rui_ro', 0)}/60")



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
        tt_qt = {"S&P 500": {"mieu_ta": "500 công ty lớn nhất Mỹ", "gia_hien_tai": 5430, "thay_doi_1nam": 0.12},"Dow Jones": {"mieu_ta": "30 công ty công nghiệp Mỹ", "gia_hien_tai": 38800, "thay_doi_1nam": 0.08},"Nasdaq": {"mieu_ta": "Chỉ số công nghệ Mỹ", "gia_hien_tai": 17600, "thay_doi_1nam": 0.18},"Nikkei 225": {"mieu_ta": "Chỉ số chính Nhật Bản", "gia_hien_tai": 38500, "thay_doi_1nam": 0.14},"HSI": {"mieu_ta": "Hang Seng - Hong Kong", "gia_hien_tai": 17800, "thay_doi_1nam": -0.05},"Vàng/XAU": {"mieu_ta": "Giá vàng thế giới (USD/oz)", "gia_hien_tai": 2350, "thay_doi_1nam": 0.22},"Dầu WTI": {"mieu_ta": "Dầu thô WTI (USD/thùng)", "gia_hien_tai": 78, "thay_doi_1nam": 0.06},"Bitcoin": {"mieu_ta": "Tiền điện tử lớn nhất", "gia_hien_tai": 67000, "thay_doi_1nam": 0.85},"Ethereum": {"mieu_ta": "Tiền điện tử lớn thứ 2", "gia_hien_tai": 3500, "thay_doi_1nam": 0.65}}
    cols = st.columns(3)
    for i, (ten, info) in enumerate(tt_qt.items()):
        with cols[i % 3]:
            change_color = "green" if info.get("thay_doi_1nam", 0) > 0 else "red"
            change_sign = "+" if info.get("thay_doi_1nam", 0) > 0 else ""
            gia = info.get("gia_hien_tai", 0)
            gia_str = f"{gia:,.2f}" if isinstance(gia, (int, float)) and gia > 100 else f"{gia:.2f}"
            st.markdown(f'<div class="card" style="text-align:center;padding:1rem;"><h4 style="color:var(--gold);margin:0;">{ten}</h4><h2 style="margin:0.5rem 0;">{gia_str}</h2><h4 style="color:{change_color};margin:0;">{change_sign}{info.get("thay_doi_1nam",0)*100:.1f}%</h4><small style="color:var(--text-muted);">{info.get("mieu_ta","")[:60]}</small></div>', unsafe_allow_html=True)
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
        auto_refresh = st.checkbox("🔄 Tự động cập nhật (60s)", value=False, key="th_auto")
        if auto_refresh:
            if "refresh_time" not in st.session_state:
                st.session_state.refresh_time = datetime.now()
            elapsed = (datetime.now() - st.session_state.refresh_time).total_seconds()
            remaining = max(0, 60 - int(elapsed))
            st.caption(f"⏳ Tự động làm mới sau {remaining}s")
            if elapsed >= 60:
                st.session_state.refresh_time = datetime.now()
                st.rerun()
    st.markdown("---")
    kpi = DOCS["kpi"]
    dm = DOCS["danh_muc"]
    perf = DOCS["performance"]
    tong_gt = sum(dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0) if ma in dm else 0 for ma in kpi)
    tong_lai_lo = sum(kpi[ma].get("lai_lo_pct", 0) * dm[ma].get("gia_von", 0) * dm[ma].get("so_luong", 0) / 100 if ma in dm else 0 for ma in kpi)
    return_pct = (perf.get("Rp", 0) * 100) or (tong_lai_lo / tong_gt * 100 if tong_gt else 0)
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
    tab_kpi, tab_vn, tab_tg, tab_port, tab_liquid, tab_esg, tab_stress, tab_perf, tab_analytics = st.tabs(["📈 KPI Scorecard", "🇻🇳 Cổ phiếu VN", "🌐 Cổ phiếu TG","📊 Danh mục","💧 Thanh khoản","🌱 ESG","🌪️ Stress Test","📊 Performance","📈 Phân tích nâng cao"])

    with tab_kpi:
        col_save_kpi, col_csv_kpi = st.columns([1, 1])
        with col_save_kpi:
            if st.button("💾 Lưu session", key="save_kpi"):
                import json, os
                path = os.path.join(os.path.dirname(__file__), "data", "session_kpi.json")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(kpi, f, ensure_ascii=False, indent=2)
                st.success("Đã lưu KPI vào data/session_kpi.json")
        with col_csv_kpi:
            pass

        st.markdown("### 🎯 SCORECARD DANH MỤC")
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
            st.download_button("📥 Export CSV", data=csv_kpi, file_name="kpi_scorecard.csv", mime="text/csv", width='stretch')

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
        st.markdown("Nguồn: **TONG_HOP_v44** — snapshot 29/05/2026 | BCTC Q1/2026")

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
            st.download_button("📥 Export CSV", data=csv_vn, file_name="co_phieu_vn.csv", mime="text/csv", width='stretch')
        else:
            st.info("Không tìm thấy mã nào phù hợp.")

    with tab_tg:
        st.markdown(f"### 🌐 Cổ phiếu thế giới ({len(DOCS['co_phieu_tg'])} mã)")
        st.markdown("Nguồn: **TONG_HOP_v44** — yfinance snapshot")
        rows_tg = []
        for ma, info in DOCS["co_phieu_tg"].items():
            rows_tg.append({
                "Ticker": ma, "Tên": info.get("ten", ""), "Sàn": info.get("san", ""),
                "Giá ($)": f"{info.get('gia', 0):,.2f}",
                "P/E": f"{info.get('pe', 0):.1f}" if info.get("pe") else "-",
                "P/B": f"{info.get('pb', 0):.2f}" if info.get("pb") else "-",
                "ROE%": f"{info.get('roe', 0)*100:.1f}" if info.get("roe") else "-",
                "Vốn hóa (tỷ$)": f"{info.get('von_hoa', 0):,.1f}" if info.get("von_hoa") else "-",
                "%YTD": f"{info.get('ytd', 0)*100:+.1f}" if info.get("ytd") else "-",
                "Tín hiệu": info.get("tin_hieu", ""), "Ngành": info.get("nganh", ""),
            })
        if rows_tg:
            df_tg = pd.DataFrame(rows_tg)
            st.dataframe(df_tg, width='stretch', hide_index=True)
            csv_tg = df_tg.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("📥 Export CSV", data=csv_tg, file_name="co_phieu_tg.csv", mime="text/csv", width='stretch')

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
            st.download_button("📥 Export CSV", data=csv_dm, file_name="danh_muc.csv", mime="text/csv", width='stretch')

        st.markdown("### 📈 Biểu đồ phân bổ danh mục")
        labels_dm = list(dm.keys())
        values_dm = [dm[ma].get("ty_trong_muc_tieu", 0) * 100 for ma in dm]
        fig_dm = go.Figure(data=[go.Pie(labels=labels_dm, values=values_dm, hole=0.4)])
        fig_dm.update_layout(title="Tỷ trọng mục tiêu (%)", height=400,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
        st.plotly_chart(fig_dm, width='stretch')

        st.markdown("### 🔥 Heatmap tương quan")
        try:
            import yfinance as yf, contextlib, io
            ma_heat = [m for m in dm.keys() if m in DOCS["live"]]
            if len(ma_heat) >= 2:
                prices = {}
                for ma in ma_heat:
                    t = yf.Ticker(ma + ".VN")
                    with contextlib.redirect_stderr(io.StringIO()):
                        h = t.history(period="1y")
                    if not h.empty:
                        prices[ma] = h["Close"].pct_change().dropna()
                if len(prices) >= 2:
                    df_corr = pd.DataFrame(prices).corr()
                    fig_heat = px.imshow(df_corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        title="Ma trận tương quan giữa các mã")
                    fig_heat.update_layout(height=450,
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE8E1"))
                    st.plotly_chart(fig_heat, width='stretch')
                else:
                    st.info("Không đủ dữ liệu giá để tính tương quan.")
            else:
                st.info("Cần ít nhất 2 mã để vẽ heatmap.")
        except Exception:
            st.info("Không thể tải dữ liệu tương quan.")

    with tab_liquid:
        st.markdown("### 💧 Rủi ro thanh khoản — ADTV")
        st.markdown("ADTV 20 phiên gần nhất, Days to Liquidate, cảnh báo kẹt hàng")
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
            st.download_button("📥 Export CSV", data=csv_liq, file_name="thanh_khoan.csv", mime="text/csv", width='stretch')

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
            st.download_button("📥 Export CSV", data=csv_esg, file_name="esg_scoring.csv", mime="text/csv", width='stretch')

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
        st.markdown("### 🌪️ STRESS TEST VĨ MÔ")
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
        st.markdown("### 📊 PHÂN RÃ HIỆU SUẤT & BENCHMARK")
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
        rp = perf.get("Rp", 0.168)
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
            if st.button("💾 Lưu session (JSON)", key="save_perf"):
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
                    st.markdown("### 📊 Drawdown history")
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

if st.session_state.trang_thai == "home":
    st.session_state.trang_thai = "dashboard"
    st.rerun()

if st.session_state.trang_thai == "survey":
    st.markdown('<p class="main-header">📝 Khảo sát khẩu vị rủi ro</p>', unsafe_allow_html=True)
    st.markdown(
        "Trả lời 12 câu hỏi để chúng tôi đánh giá mức độ chấp nhận rủi ro và mục tiêu tài chính của bạn!"
    )
    st.markdown("---")

    progress = st.progress(st.session_state.cau_hoi_index / len(CAU_HOI_KHAO_SAT))

    if st.session_state.cau_hoi_index < len(CAU_HOI_KHAO_SAT):
        cau = CAU_HOI_KHAO_SAT[st.session_state.cau_hoi_index]
        st.markdown(f"### Câu {st.session_state.cau_hoi_index + 1}/{len(CAU_HOI_KHAO_SAT)}")
        st.markdown(f"**{cau['cau_hoi']}**")

        lua_chon_nhan = [opt["nhan"] for opt in cau["lua_chon"]]
        lua_chon_diem = {opt["nhan"]: opt["diem"] for opt in cau["lua_chon"]}

        selected = st.radio(
            "Chọn câu trả lời:",
            lua_chon_nhan,
            key=f"q_{st.session_state.cau_hoi_index}",
            index=None,
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Tiếp theo", disabled=selected is None, width='stretch'):
                if selected:
                    st.session_state.cau_tra_loi[cau["y"]] = lua_chon_diem[selected]
                    st.session_state.cau_hoi_index += 1
                    st.rerun()

        with col2:
            if st.button("🔙 Quay lại trang chủ", width='stretch'):
                st.session_state.cau_hoi_index = 0
                st.session_state.cau_tra_loi = {}
                st.session_state.trang_thai = "home"
                st.rerun()
    else:
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
                st.session_state.cau_hoi_index = 0
                st.session_state.cau_tra_loi = {}
                st.session_state.da_phan_tich = False
                st.rerun()

        with col3:
            if st.button("🏠 Về trang chủ", width='stretch'):
                st.session_state.cau_hoi_index = 0
                st.session_state.trang_thai = "home"
                st.rerun()


elif st.session_state.trang_thai == "portfolio":
    st.markdown('<p class="main-header">📊 Danh mục đầu tư</p>', unsafe_allow_html=True)
    st.markdown("---")
    dm = DOCS.get("danh_muc", {})
    kpi = DOCS.get("kpi", {})
    tong_gt = sum(dm[ma].get("gia_thi_truong", 0) * dm[ma].get("so_luong", 0) for ma in dm)
    tong_phi = sum(abs(dm[ma].get("gia_thi_truong", 0) - dm[ma].get("gia_von", 0)) * dm[ma].get("so_luong", 0) for ma in dm)
    tong_lai_lo = sum((dm[ma].get("gia_thi_truong", 0) - dm[ma].get("gia_von", 0)) * dm[ma].get("so_luong", 0) for ma in dm)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng giá trị", f"{tong_gt:,.0f}₫")
    with col2:
        st.metric("Tổng lãi/lỗ", f"{tong_lai_lo:+,.0f}₫", delta=f"{tong_lai_lo/tong_gt*100 if tong_gt else 0:.1f}%")
    with col3:
        st.metric("Số mã", f"{len(dm)}")
    with col4:
        st.metric("Tỷ suất", f"{tong_lai_lo/tong_gt*100 if tong_gt else 0:+.1f}%")

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
    _render_market()
    _render_quoc_te()
    _render_tonghop()
elif st.session_state.trang_thai == "dashboard":
    st.markdown('<p class="main-header">📊 Dashboard tổng quan</p>', unsafe_allow_html=True)
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
                  help="Portfolio đang quản lý")
    with col4:
        st.metric("🔄 Cập nhật", DOCS.get("ngay_cap_nhat", "N/A"),
                  help="Dữ liệu Excel mới nhất")

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
                    "ROE%": f"{info.get('roe', 0):.1f}",
                    "P&L%": f"{info.get('lai_lo_pct', 0):.1f}",
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
                st.metric("🇻🇳 VN-Index",
                          f"{vni.get('gia', 0):,.1f}",
                          f"{vni.get('thay_doi_pct', 0):+.2f}%")
        with c2:
            if gold_key:
                g = tt[gold_key]
                st.metric("🥇 Vàng SJC",
                          f"{g.get('gia', 0):,.0f}₫",
                          f"{g.get('thay_doi_pct', 0):+.2f}%")
        with c3:
            if btc_key:
                btc = qt[btc_key]
                st.metric("₿ Bitcoin",
                          f"${btc.get('gia', 0):,.0f}",
                          f"{btc.get('thay_doi_pct', 0):+.2f}%")
        with c4:
            if sp_key:
                sp = qt[sp_key]
                st.metric("🇺🇸 S&P 500",
                          f"{sp.get('gia', 0):,.0f}",
                          f"{sp.get('thay_doi_pct', 0):+.2f}%")

elif st.session_state.trang_thai == "chat":
    st.markdown('<p class="main-header">💬 Chat với Robo-Advisor</p>', unsafe_allow_html=True)
    st.markdown(
        "Hỏi tôi về đầu tư, cổ phiếu, vàng, bất động sản, hay bất kỳ chủ đề tài chính nào!"
    )
    st.markdown("---")

    for i, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "bot":
            st.markdown(
                f'<div class="chat-message bot-message">🤖 <strong>Robo-Advisor:</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
            if st.button("🔊 Đọc", key=f"tts_{i}", use_container_width=True):
                st.session_state.tts_msg = msg["content"]
                st.rerun()
        else:
            st.markdown(
                f'<div class="chat-message user-message">👤 <strong>Bạn:</strong><br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    def _exec_js(js_code, height=1):
        html = f"<script>{js_code}</script>"
        try:
            components.html(html, height=height)
        except Exception:
            import html as _h
            st.markdown(
                f'<iframe srcdoc="{_h.escape(html)}" '
                f'style="width:0;height:1px;border:none;overflow:hidden;" '
                f'sandbox="allow-scripts"></iframe>',
                unsafe_allow_html=True,
            )

    if tts_text := st.session_state.pop("tts_msg", None):
        safe = json.dumps(tts_text, ensure_ascii=False)
        _exec_js(
            f"window.speechSynthesis.cancel();"
            f"var u=new SpeechSynthesisUtterance({safe});"
            f"u.lang='vi-VN';u.rate=1.0;u.pitch=1.0;u.volume=1.0;"
            f"window.speechSynthesis.speak(u);"
        )

    if "show_mic" not in st.session_state:
        st.session_state.show_mic = False

    col1, col2, col3 = st.columns([1, 6, 4])
    with col1:
        if st.button("🎤", use_container_width=True, help="Nhập bằng giọng nói"):
            st.session_state.show_mic = not st.session_state.show_mic
            st.rerun()
    with col2:
        with st.form(key="chat_form", clear_on_submit=True):
            cau_hoi = st.text_input(
                "Nhập câu hỏi của bạn:",
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
        if st.session_state.chat_history and st.button("🗑️", use_container_width=True, help="Xóa lịch sử"):
            st.session_state.chat_history = []
            st.rerun()

    if st.session_state.show_mic:
        mic_html = """
            <div style="text-align:center;padding:12px;background:linear-gradient(135deg,#0a0e27,#1a1040);border-radius:12px;border:1px solid #FFD70044;">
                <div style="color:#8892B0;font-size:13px;margin-bottom:6px;">Bam micro, noi xong tu dong gui</div>
                <div id="mic_status" style="color:#8892B0;font-size:12px;margin-bottom:6px;">Bam vao micro de bat dau</div>
                <button id="mic_btn"
                    style="font-size:30px;padding:10px 20px;border-radius:50%;border:2px solid #FFD700;background:#FFD70011;color:#FFD700;cursor:pointer;">
                    🎤
                </button>
            </div>
            <script>
            document.getElementById('mic_btn').onclick = function() {
                var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) { alert('Trinh duyet khong ho tro'); return; }
                var r = new SR();
                r.lang = 'vi-VN';
                r.continuous = false;
                r.interimResults = false;
                document.getElementById('mic_status').innerText = 'Dang nghe...';
                this.style.background = '#FFD700';
                this.style.color = '#02050E';
                r.onresult = function(e) {
                    var text = e.results[0][0].transcript;
                    document.getElementById('mic_status').innerText = 'Da nhan: ' + text;
                    try {
                        var doc = window.parent.document;
                        var inp = doc.querySelector('input[type="text"]');
                        if (inp) {
                            var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                            setter.call(inp, text);
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                            setTimeout(function() {
                                var btns = doc.querySelectorAll('button');
                                for (var b of btns) {
                                    if (b.textContent.trim() === 'Gui' || b.textContent.trim() === 'Gửi') {
                                        b.click();
                                        break;
                                    }
                                }
                            }, 400);
                        }
                    } catch(e) { alert('Loi: ' + e.message); }
                };
                r.onerror = function(e) {
                    document.getElementById('mic_status').innerText = 'Loi: ' + e.error;
                    this.style.background = '#FFD70011';
                    this.style.color = '#FFD700';
                };
                r.start();
            };
            </script>
        """
        try:
            components.html(mic_html, height=130)
        except Exception:
            import html as _h
            st.markdown(
                f'<iframe srcdoc="{_h.escape(mic_html)}" '
                f'style="width:100%;height:130px;border:none;border-radius:12px;" '
                f'sandbox="allow-scripts allow-same-origin allow-microphone"></iframe>',
                unsafe_allow_html=True,
            )



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
    '🤖 Robo-Advisor — Tư vấn đầu tư thông minh cho người Việt<br>'
    '<span style="color: #FFD700;">© 2026 • Phiên bản Hoàng gia &amp; Thịnh vượng v3.0</span></center>',
    unsafe_allow_html=True,
)


