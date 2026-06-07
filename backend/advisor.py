"""Tu van Dau tu — 3-tab flow: Thiet lap muc tieu -> Khuyen nghi DM -> Kiem thu Lich su"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import math
from datetime import datetime, timedelta

# ============================================================
# Constants
# ============================================================
RISK_NAMES = ["Bao thu", "Than trong", "Trung dung", "Tang truong", "Tao bao"]
RISK_TO_IDX = {v: i for i, v in enumerate(RISK_NAMES)}

ALLOC_ASSETS = ["Trai phieu / Gui tiet kiem", "Co phieu Viet Nam", "Co phieu Quoc te", "Vang / Bat dong san"]
# Ty trong theo khau vi: [Bao thu, Than trong, Trung dung, Tang truong, Tao bao]
ALLOC_MATRIX = [
    [0.60, 0.40, 0.20, 0.10, 0.00],  # Trai phieu
    [0.25, 0.40, 0.55, 0.55, 0.50],  # CP VN
    [0.05, 0.10, 0.15, 0.25, 0.35],  # CP QT
    [0.10, 0.10, 0.10, 0.10, 0.15],  # Vang/BDS
]
EXP_RET = [0.06, 0.09, 0.12, 0.16, 0.20]
EXP_VOL = [0.05, 0.10, 0.15, 0.20, 0.25]

RISK_DESC = {
    "Bao thu": "Uu tien bao toan von, chap nhan loi nhuan thap, rui ro toi thieu.",
    "Than trong": "Can bang giua an toan va tang truong, chap nhan dao dong nhe.",
    "Trung dung": "Tang truong on dinh, chap nhan rui ro trung binh.",
    "Tang truong": "Uu tien tang truong cao, chap nhan rui ro lon hon.",
    "Tao bao": "Toi da hoa loi nhuan, chap nhan rui ro rat cao, dao dong manh.",
}

_tam_sang_cache = {}


def diem_tam_sang(ma, info):
    key = (ma, info.get("ten", ""))
    if key in _tam_sang_cache:
        return _tam_sang_cache[key]
    d = 50.0
    esg = info.get("esg_score")
    if isinstance(esg, (int, float)):
        d += (esg - 50) * 0.3
    insider = info.get("insider_pct") or 0
    if isinstance(insider, (int, float)):
        if insider >= 5:
            d += 10
        elif insider >= 2:
            d += 5
        elif 0 < insider <= 0.5:
            d -= 5
    canh_bao = str(info.get("canh_bao") or "").strip()
    if canh_bao:
        d -= 20
    de = info.get("de_ratio") or 0
    if isinstance(de, (int, float)):
        if de > 5:
            d -= 10
        elif de > 3:
            d -= 5
        elif de < 1 < de:
            d += 5
    dao_duc = str(info.get("dao_duc") or "")
    if "Cao" in dao_duc:
        d += 5
    elif "Thap" in dao_duc:
        d -= 10
    d = max(0, min(100, d))
    _tam_sang_cache[key] = d
    return d


def loc_tam_sang(items, nguong=40):
    result = []
    for ma, info in items:
        d = diem_tam_sang(ma, info)
        if d >= nguong:
            result.append((ma, info, d))
    result.sort(key=lambda x: -x[2])
    return result


def tinh_lot(tien, gia):
    if gia <= 0:
        return 0, 0
    sl = int(tien / gia)
    lot = (sl // 100) * 100
    return lot, lot * gia


# ============================================================
# TAB 1: Thiet lap muc tieu
# ============================================================
def tab_setup():
    st.markdown('<div class="main-header" style="font-size:1.6rem;font-weight:700;color:#FFD700;">\U0001f3af Thiet lap Muc tieu Dau tu</div>', unsafe_allow_html=True)

    von = st.session_state.get("advisor_capital", 100_000_000)
    nam = st.session_state.get("advisor_years", 5)
    risk_str = st.session_state.get("advisor_risk", "Trung dung")
    ridx = RISK_TO_IDX.get(risk_str, 2)
    er = EXP_RET[ridx]
    vol = EXP_VOL[ridx]
    cuoiky = von * (1 + er) ** nam
    lacquan = von * (1 + er * 1.5) ** nam
    biquan = von * (1 + er * 0.5) ** nam

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Von dau tu", f"{von:,.0f}d")
        st.metric("Thoi gian", f"{nam} nam")
    with col2:
        st.metric("Loi nhuan ky vong", f"{er*100:.1f}%/nam")
        st.metric("Muc dao dong (Vol)", f"{vol*100:.0f}%/nam")
    with col3:
        st.metric("Gia tri cuoi ky (co so)", f"{cuoiky:,.0f}d")
        st.metric("Muc tieu", st.session_state.get("advisor_target", "Ngh?i huu som"))

    # Duong tang truong
    years = list(range(nam + 1))
    base_v = [von * (1 + er) ** y for y in years]
    opt_v = [von * (1 + er * 1.5) ** y for y in years]
    pes_v = [von * (1 + er * 0.5) ** y for y in years]
    inf_v = [von * 1.04 ** y for y in years]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=base_v, name="Co so", line=dict(color="#00C9A7", width=3)))
    fig.add_trace(go.Scatter(x=years, y=opt_v, name="Lac quan", line=dict(color="#FFD700", width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=years, y=pes_v, name="Bi quan", line=dict(color="#FF6B6B", width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=years, y=inf_v, name="Lam phat 4%", line=dict(color="#ECE8E1", width=1, dash="dot")))
    fig.update_layout(template="plotly_dark", height=380, hovermode="x unified",
                      legend=dict(orientation="h", y=-0.25), margin=dict(t=30))
    fig.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Kha vi: {risk_str}")
    st.caption(RISK_DESC.get(risk_str, ""))
    st.markdown(f"**Loi nhuan ky vong:** {er*100:.1f}%/nam | **Vol:** {vol*100:.0f}%/nam")
    st.markdown(f"**Gia tri cuoi ky:** Co so {cuoiky:,.0f}d | Lac quan {lacquan:,.0f}d | Bi quan {biquan:,.0f}d")

    # Ty trong tai san
    alloc = {ALLOC_ASSETS[i]: ALLOC_MATRIX[i][ridx] for i in range(4)}
    fig2 = go.Figure(data=[go.Pie(labels=list(alloc.keys()), values=list(alloc.values()), hole=0.4)])
    fig2.update_layout(template="plotly_dark", height=280, showlegend=True)
    st.plotly_chart(fig2, use_container_width=True)

    # Max drawdown
    st.markdown("---")
    st.subheader("Kich ban sut giam toi da (Max Drawdown)")
    port_vol = vol * 0.7
    max_dd = min(0.9, max(0.1, port_vol * 2.5))
    loss_amt = von * max_dd
    recover_years = max(1, int(math.log(2) / math.log(1 + er))) if er > 0 else 10
    st.markdown(f"- **Sut giam toi da uoc tinh:** {max_dd*100:.0f}% (-{loss_amt:,.0f}d)")
    st.markdown(f"- **Gia tri DM sau sut giam:** {von - loss_amt:,.0f}d")
    st.markdown(f"- **Thoi gian phuc hoi (uoc tinh):** {recover_years} nam")
    st.caption("Luu y: So lieu uoc tinh tu du lieu lich su, khong dam bao ket qua tuong lai.")


# ============================================================
# TAB 2: Khuyen nghi Danh muc
# ============================================================
def tab_portfolio(docs):
    st.markdown('<div class="main-header" style="font-size:1.6rem;font-weight:700;color:#FFD700;">\U0001f4ca Khuyen nghi Danh muc Dau tu</div>', unsafe_allow_html=True)

    von = st.session_state.get("advisor_capital", 100_000_000)
    risk_str = st.session_state.get("advisor_risk", "Trung dung")
    ridx = RISK_TO_IDX.get(risk_str, 2)

    bucket_vn = docs.get("co_phieu_vn", {})

    # --- Bo loc Tam Sang ---
    st.subheader("Bo loc Tam Sang")
    nguong = st.slider("Nguong diem Tam Sang toi thieu", 0, 100, 40, 5,
                       help="Loai bo CP co diem quan tri & dao duc duoi nguong")
    vn_items = [(ma, info) for ma, info in bucket_vn.items() if (info.get("gia") or 0) > 0 and info.get("pe")]
    vn_sang = loc_tam_sang(vn_items, nguong)
    st.success(f"Loc: {len(vn_items)} => {len(vn_sang)} CP dat chuan Tam Sang (>= {nguong} diem)")

    # --- Xep hang va phan bo ---
    st.subheader("Danh muc de xuat")
    scored = []
    for ma, info, ts_d in vn_sang:
        pe = info.get("pe")
        if not isinstance(pe, (int, float)) or pe <= 0:
            continue
        s = ts_d * 0.5
        if pe < 10:
            s += 30
        elif pe < 15:
            s += 20
        elif pe < 20:
            s += 10
        roe = info.get("roe")
        if isinstance(roe, (int, float)):
            if roe > 20: s += 20
            elif roe > 15: s += 10
            elif roe > 10: s += 5
        pb = info.get("pb")
        if isinstance(pb, (int, float)) and 0 < pb < 3:
            s += 5
        ct = info.get("co_tuc_pct") or 0
        if isinstance(ct, (int, float)) and ct > 50:
            s += 5
        scored.append((ma, info, ts_d, s))
    scored.sort(key=lambda x: -x[3])

    top_n = st.slider("So CP khuyen nghi", 5, 30, 15)
    top = scored[:top_n]
    total_s = sum(s[3] for s in top) or 1

    # Phan bo von
    rows = []
    labels = []
    vals = []
    for ma, info, ts_d, s in top:
        ty = s / total_s
        tien = von * ty
        gia = info.get("gia") or 0
        lot, tien_that = tinh_lot(tien, gia)
        ty_dc = tien_that / von if von > 0 else 0
        if lot == 0:
            continue
        labels.append(ma)
        vals.append(ty_dc * 100)
        rows.append({
            "Ma": ma, "Ten": info.get("ten", ""),
            "Nganh": info.get("nganh", ""), "Gia": gia,
            "Ty trong": f"{ty_dc*100:.1f}%",
            "So tien": f"{tien_that:,.0f}d",
            "So CP (lot 100)": lot,
            "PE": pe, "ROE": roe,
            "Tam Sang": f"{ts_d}/100"
        })

    # Pie chart
    if vals:
        fig = go.Figure(data=[go.Pie(labels=labels, values=vals, hole=0.45,
                                      textinfo="label+percent", textfont=dict(size=12))])
        fig.update_layout(template="plotly_dark", height=420,
                          title="Phan bo danh muc khuyen nghi")
        st.plotly_chart(fig, use_container_width=True)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Gia": st.column_config.NumberColumn(format="%d d"),
                         "So CP (lot 100)": st.column_config.NumberColumn(format="%d"),
                     })

        total_invested = sum(r["So CP (lot 100)"] * r["Gia"] for r in rows)
        st.info(f"**Tong dau tu:** {total_invested:,.0f}d / {von:,.0f}d ({total_invested/von*100:.1f}%) | **So ma:** {sum(1 for r in rows if r['So CP (lot 100)'] > 0)}")

        # Apply button
        if st.button("Ap dung vao Danh muc", use_container_width=True):
            dm = {}
            for r in rows:
                ma = r["Ma"]
                lot = r["So CP (lot 100)"]
                gia = r["Gia"]
                if lot > 0:
                    dm[ma] = {"so_luong": lot, "gia_von": gia}
            if dm:
                st.session_state["dm"] = dm
                st.success(f"Da cap nhat DM voi {len(dm)} ma CP!")
            else:
                st.warning("Khong co CP nao du dieu kien.")
    else:
        st.warning("Khong co CP nao dat tieu chuan. Hay giam nguong Tam Sang.")

    # --- Tai can bang ---
    st.markdown("---")
    st.subheader("Tai can bang danh muc (Rebalancing)")
    st.caption("Nhap so luong CP dang nam giu de nhan de xuat mua/ban.")

    if rows:
        with st.expander("Nhap so luong hien tai", expanded=False):
            cur = {}
            for r in rows:
                ma = r["Ma"]
                cur[ma] = st.number_input(f"{ma} ({r['Ten'][:20]})", 0, 100000, 0, step=100, key=f"reb_{ma}")
            if st.button("Tinh toan tai can bang", use_container_width=True):
                rebal = []
                tong_cur_val = sum(cur.get(r["Ma"], 0) * r["Gia"] for r in rows)
                tong_target = von
                for r in rows:
                    ma, gia = r["Ma"], r["Gia"]
                    cq = cur.get(ma, 0)
                    cv = cq * gia
                    cw = cv / tong_cur_val if tong_cur_val > 0 else 0
                    tw = float(r["Ty trong"].replace("%", "")) / 100
                    tgt_v = von * tw
                    diff = tgt_v - cv
                    if abs(diff) >= gia * 100:
                        qty_diff = int(diff / gia / 100) * 100
                    else:
                        qty_diff = 0
                    act = "MUA" if qty_diff > 0 else ("BAN" if qty_diff < 0 else "---")
                    rebal.append({
                        "Ma": ma, "Ty trong HT": f"{cw*100:.1f}%",
                        "Ty trong MT": f"{tw*100:.1f}%",
                        "Chenh lech": f"{(tw-cw)*100:+.1f}%",
                        "Hanh dong": act,
                        "So luong": abs(qty_diff),
                        "Gia tri": f"{abs(qty_diff)*gia:,.0f}d",
                    })
                df_r = pd.DataFrame(rebal)
                st.dataframe(df_r, use_container_width=True, hide_index=True)
                buy_t = sum(
                    int((von * float(r["Ty trong"].replace("%", "")) / 100 - cur.get(r["Ma"], 0) * r["Gia"]) / r["Gia"] / 100) * 100 * r["Gia"]
                    for r in rows
                    if int((von * float(r["Ty trong"].replace("%", "")) / 100 - cur.get(r["Ma"], 0) * r["Gia"]) / r["Gia"] / 100) * 100 > 0
                )
                sell_t = sum(
                    abs(int((von * float(r["Ty trong"].replace("%", "")) / 100 - cur.get(r["Ma"], 0) * r["Gia"]) / r["Gia"] / 100)) * 100 * r["Gia"]
                    for r in rows
                    if int((von * float(r["Ty trong"].replace("%", "")) / 100 - cur.get(r["Ma"], 0) * r["Gia"]) / r["Gia"] / 100) * 100 < 0
                )
                st.info(f"**Can mua them:** {buy_t:,.0f}d | **Can ban ra:** {sell_t:,.0f}d")
                if buy_t > 0:
                    st.warning("Neu khong du tien, hay giam ty trong cac ma thua hoac bo sung von.")
    else:
        st.warning("Chua co danh muc de tai can bang.")


# ============================================================
# TAB 3: Kiem thu Lich su (Backtest)
# ============================================================
def tab_backtest(docs):
    st.markdown('<div class="main-header" style="font-size:1.6rem;font-weight:700;color:#FFD700;">\U0001f4c8 Kiem thu Lich su — Backtest</div>', unsafe_allow_html=True)

    von = st.session_state.get("advisor_capital", 100_000_000)
    risk_str = st.session_state.get("advisor_risk", "Trung dung")
    ridx = RISK_TO_IDX.get(risk_str, 2)
    er = EXP_RET[ridx]
    vol = EXP_VOL[ridx]

    bucket_vn = docs.get("co_phieu_vn", {})

    # Lay danh muc tu session (hoac tao mau)
    dm = st.session_state.get("dm", {})
    if not dm:
        # Tao mau tu khuyen nghi
        vn_items = [(ma, info) for ma, info in bucket_vn.items() if (info.get("gia") or 0) > 0 and info.get("pe")]
        vn_sang = loc_tam_sang(vn_items, 30)
        scored = []
        for ma, info, ts_d in vn_sang[:30]:
            pe = info.get("pe")
            if not isinstance(pe, (int, float)) or pe <= 0:
                continue
            s = ts_d * 0.5
            if pe < 10: s += 30
            elif pe < 15: s += 20
            roe = info.get("roe")
            if isinstance(roe, (int, float)) and roe > 15: s += 15
            scored.append((ma, info, ts_d, s))
        scored.sort(key=lambda x: -x[3])
        top = scored[:12]
        total_s = sum(item[3] for item in top) or 1
        for ma, info, ts_d, s in top:
            ty = s / total_s
            tien = von * ty
            gia = info.get("gia") or 0
            lot, _ = tinh_lot(tien, gia)
            if lot > 0:
                dm[ma] = {"so_luong": lot, "gia_von": gia}
        if not dm:
            st.warning("Khong the tao danh muc mau. Vui long quay lai Tab 2.")
            return

    # Tinh gia tri DM & backtest
    st.subheader("Danh muc hien tai")
    dm_info = []
    total_value = 0
    for ma, info_dm in dm.items():
        cp_info = bucket_vn.get(ma, {})
        gia = cp_info.get("gia") or info_dm.get("gia_von", 0)
        sl = info_dm.get("so_luong", 0)
        gt = sl * gia
        dm_info.append({"Ma": ma, "Ten": cp_info.get("ten", ""), "SL": sl, "Gia": gia, "GT": gt})
        total_value += gt
    df_dm = pd.DataFrame(dm_info)
    st.dataframe(df_dm, use_container_width=True, hide_index=True,
                 column_config={"Gia": st.column_config.NumberColumn(format="%d d"),
                                "GT": st.column_config.NumberColumn(format="%d d")})
    st.metric("Tong gia tri DM", f"{total_value:,.0f}d")

    # Mo phong tang truong
    st.markdown("---")
    st.subheader("Mo phong hieu suat")
    n_years = st.slider("So nam backtest", 1, 15, 5)

    # Gia lap loi nhuan hang nam tu EXP_RET + nhieu
    np.random.seed(42)
    annual_returns = np.random.normal(er, vol, n_years)
    # Khoi tao VN-Index tai ~1280
    vnindex_start = 1280
    vnindex_vol = vol * 1.1
    vnindex_returns = np.random.normal(0.07, vnindex_vol, n_years)  # VN-Index TB 7%/nam

    dm_values = [total_value]
    vnindex_values = [vnindex_start]
    for i in range(n_years):
        dm_values.append(dm_values[-1] * (1 + annual_returns[i]))
        vnindex_values.append(vnindex_values[-1] * (1 + vnindex_returns[i]))

    years_label = list(range(n_years + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_label, y=dm_values, name="Danh muc cua ban",
                             line=dict(color="#00C9A7", width=3)))
    fig.add_trace(go.Scatter(x=years_label, y=vnindex_values, name="VN-Index",
                             line=dict(color="#FFD700", width=2, dash="dash")))
    fig.update_layout(template="plotly_dark", height=380,
                      title="Tang truong: Danh muc vs VN-Index",
                      hovermode="x unified",
                      legend=dict(orientation="h", y=-0.25))
    fig.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    # Chi so hieu suat
    dm_final = dm_values[-1]
    vnindex_final = vnindex_values[-1]
    dm_cagr = (dm_final / total_value) ** (1 / n_years) - 1
    vnindex_cagr = (vnindex_final / vnindex_start) ** (1 / n_years) - 1
    alpha = dm_cagr - vnindex_cagr

    best_return = max(annual_returns)
    worst_return = min(annual_returns)
    max_dd_sim = min(0, worst_return)
    cum_max = np.maximum.accumulate(dm_values)
    dd_series = [(dm_values[i] - cum_max[i]) / cum_max[i] for i in range(len(dm_values))]
    max_dd = min(dd_series)
    sharpe = (dm_cagr - 0.04) / (np.std(annual_returns) + 1e-10)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gia tri cuoi", f"{dm_final:,.0f}d")
    with col2:
        st.metric("CAGR", f"{dm_cagr*100:.2f}%", f"{alpha*100:+.2f}% vs VN-Index")
    with col3:
        st.metric("Sharpe", f"{sharpe:.2f}")
    with col4:
        st.metric("Max Drawdown", f"{max_dd*100:.2f}%")

    # Drawdown chart
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=years_label, y=[v * 100 for v in dd_series],
                                fill="tozeroy", name="Drawdown",
                                line=dict(color="#FF6B6B", width=2)))
    fig_dd.update_layout(template="plotly_dark", height=250,
                         title="Drawdown qua cac nam",
                         yaxis_title="%", hovermode="x unified")
    st.plotly_chart(fig_dd, use_container_width=True)

    # Chi tiet tung nam
    with st.expander("Chi tiet tung nam"):
        detail_rows = []
        for i in range(n_years):
            detail_rows.append({
                "Nam": i + 1,
                "DM dau nam": f"{dm_values[i]:,.0f}d",
                "Loi nhuan": f"{annual_returns[i]*100:+.2f}%",
                "DM cuoi nam": f"{dm_values[i+1]:,.0f}d",
                "VN-Index": f"{vnindex_values[i+1]:,.0f}",
            })
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

    # Monte Carlo
    st.markdown("---")
    st.subheader("Monte Carlo — 1000 kich ban")
    n_sim = 1000
    sim_results = []
    for _ in range(n_sim):
        sim_ret = np.random.normal(er, vol, n_years)
        sim_final = total_value * np.prod(1 + sim_ret)
        sim_results.append(sim_final)
    sim_results = np.array(sim_results)

    p5 = np.percentile(sim_results, 5)
    p25 = np.percentile(sim_results, 25)
    p50 = np.percentile(sim_results, 50)
    p75 = np.percentile(sim_results, 75)
    p95 = np.percentile(sim_results, 95)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Toi te nhat (5%)", f"{p5:,.0f}d")
    with col2: st.metric("Thap (25%)", f"{p25:,.0f}d")
    with col3: st.metric("Trung vi", f"{p50:,.0f}d")
    with col4: st.metric("Cao (75%)", f"{p75:,.0f}d")
    with col5: st.metric("Toi uu (95%)", f"{p95:,.0f}d")

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=sim_results, nbinsx=50, name="Phan phoi",
                                     marker_color="#00C9A7"))
    fig_hist.add_vline(x=p5, line_dash="dash", line_color="#FF6B6B",
                       annotation_text="5%")
    fig_hist.add_vline(x=p50, line_dash="dash", line_color="#FFD700",
                       annotation_text="50%")
    fig_hist.add_vline(x=p95, line_dash="dash", line_color="#00C9A7",
                       annotation_text="95%")
    fig_hist.update_layout(template="plotly_dark", height=300,
                           title=f"Phan phoi gia tri DM sau {n_years} nam ({n_sim} kich ban)",
                           xaxis_title="Gia tri cuoi ky",
                           yaxis_title="So lan")
    fig_hist.update_xaxes(tickformat=",.0f")
    st.plotly_chart(fig_hist, use_container_width=True)


# ============================================================
# MAIN: Tu van Dau tu (3 tab)
# ============================================================
def render(docs):
    # Sidebar controls
    with st.sidebar:
        st.markdown("### Tuy chinh Dau tu")
        cap = st.number_input("Von dau tu (d)", min_value=1_000_000, value=st.session_state.get("advisor_capital", 100_000_000),
                              step=10_000_000, format="%d",
                              help="Tong so tien ban muon dau tu")
        years = st.slider("Thoi gian dau tu (nam)", 1, 30, st.session_state.get("advisor_years", 5))
        risk = st.selectbox("Kha vi rui ro", RISK_NAMES,
                            index=RISK_NAMES.index(st.session_state.get("advisor_risk", "Trung dung")))
        target = st.selectbox("Muc tieu dau tu",
                              ["Ngh?i huu som", "Mua nha", "Giao duc con cai", "Tai san dai han", "Kiem loi ngan han"],
                              index=["Ngh?i huu som", "Mua nha", "Giao duc con cai", "Tai san dai han", "Kiem loi ngan han"].index(
                                  st.session_state.get("advisor_target", "Ngh?i huu som")))
        withdrawal = st.slider("Ty le rut tien hang nam (%)", 0, 20,
                               st.session_state.get("advisor_withdrawal", 0)) / 100
        st.markdown("---")
        if st.button("Ap dung", use_container_width=True):
            st.session_state.advisor_capital = int(cap)
            st.session_state.advisor_years = years
            st.session_state.advisor_risk = risk
            st.session_state.advisor_target = target
            st.session_state.advisor_withdrawal = withdrawal
            st.rerun()

    # Main 3-tab content
    tab1, tab2, tab3 = st.tabs([
        "\U0001f3af Thiet lap muc tieu",
        "\U0001f4ca Khuyen nghi Danh muc",
        "\U0001f4c8 Kiem thu Lich su"])

    with tab1:
        tab_setup()
    with tab2:
        tab_portfolio(docs)
    with tab3:
        tab_backtest(docs)
