import numpy as np
import pandas as pd
import logging
import time
from datetime import datetime
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)

def tinh_cagr(gia_dau, gia_cuoi, so_nam):
    if gia_dau <= 0 or so_nam <= 0:
        return 0
    return (gia_cuoi / gia_dau) ** (1 / so_nam) - 1

def tinh_max_drawdown(gia_lich_su):
    if gia_lich_su is None or len(gia_lich_su) < 2:
        return 0, None
    peak = gia_lich_su[0]
    max_dd = 0
    dd_from_idx = dd_to_idx = 0
    peak_idx = 0
    for i, gia in enumerate(gia_lich_su):
        if gia > peak:
            peak = gia
            peak_idx = i
        dd = (gia - peak) / peak
        if dd < max_dd:
            max_dd = dd
            dd_from_idx = peak_idx
            dd_to_idx = i
    return max_dd, (gia_lich_su[dd_from_idx], gia_lich_su[dd_to_idx])

def tinh_drawdown_series(gia_lich_su):
    if gia_lich_su is None or len(gia_lich_su) < 2:
        return np.array([])
    peak = np.maximum.accumulate(gia_lich_su)
    return (gia_lich_su - peak) / peak

def tinh_var(loi_nhuan_hang_ngay, confidence=0.95):
    if loi_nhuan_hang_ngay is None or len(loi_nhuan_hang_ngay) < 20:
        return -0.02
    return np.percentile(loi_nhuan_hang_ngay, (1 - confidence) * 100)

def tinh_cvar(loi_nhuan_hang_ngay, confidence=0.95):
    if loi_nhuan_hang_ngay is None or len(loi_nhuan_hang_ngay) < 20:
        return -0.03
    var = tinh_var(loi_nhuan_hang_ngay, confidence)
    losses = loi_nhuan_hang_ngay[loi_nhuan_hang_ngay <= var]
    return np.mean(losses) if len(losses) > 0 else var

def tinh_sortino(loi_nhuan_lich_su, ty_suat_phi_rui_ro=0.05):
    if loi_nhuan_lich_su is None or len(loi_nhuan_lich_su) < 2:
        return 0
    loi_nhuan_tb = np.mean(loi_nhuan_lich_su)
    loi_nhuan_du_thua = loi_nhuan_tb - ty_suat_phi_rui_ro
    down_returns = loi_nhuan_lich_su[loi_nhuan_lich_su < 0]
    if len(down_returns) == 0:
        return 10
    down_vol = np.sqrt(np.mean(down_returns ** 2))
    return loi_nhuan_du_thua / down_vol if down_vol > 0 else 0

def tinh_sharpe_ratio(loi_nhuan_tb, rui_ro, ty_suat_phi_rui_ro=0.05):
    if rui_ro <= 0:
        return 0
    return (loi_nhuan_tb - ty_suat_phi_rui_ro) / rui_ro

def tinh_rolling_sharpe(loi_nhuan_hang_ngay, window=63):
    if loi_nhuan_hang_ngay is None or len(loi_nhuan_hang_ngay) < window:
        return np.array([])
    rs = pd.Series(loi_nhuan_hang_ngay).rolling(window).apply(
        lambda x: tinh_sharpe_ratio(np.mean(x) * 252, np.std(x) * np.sqrt(252), 0.05)
    )
    return rs.values

def tinh_rsi(gia, window=14):
    if gia is None or len(gia) < window + 1:
        return np.array([])
    delta = np.diff(gia)
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)
    avg_gain = np.convolve(gains, np.ones(window)/window, mode='valid')
    avg_loss = np.convolve(losses, np.ones(window)/window, mode='valid')
    rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
    rsi = 100 - (100 / (1 + rs))
    pad = np.full(window - 1, np.nan)
    rsi_full = np.concatenate([pad, rsi, [np.nan]]) if len(rsi) < len(gia) else rsi[:len(gia)]
    if len(rsi_full) < len(gia):
        rsi_full = np.concatenate([rsi_full, np.full(len(gia) - len(rsi_full), np.nan)])
    return rsi_full[:len(gia)]

def tinh_macd(gia, fast=12, slow=26, signal=9):
    if gia is None or len(gia) < slow + signal:
        return np.array([]), np.array([]), np.array([])
    ema_fast = pd.Series(gia).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(gia).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.values, signal_line.values, histogram.values

def tinh_beta(ma_yahoo, benchmark="^VNINDEX", ky_han="2y"):
    try:
        import yfinance as yf, contextlib, io
        ticker = yf.Ticker(ma_yahoo)
        bench = yf.Ticker(benchmark)
        with contextlib.redirect_stderr(io.StringIO()):
            h1 = ticker.history(period=ky_han)
            h2 = bench.history(period=ky_han)
        if h1.empty or h2.empty or len(h1) < 10 or len(h2) < 10:
            return None, None
        r1 = h1['Close'].pct_change().dropna()
        r2 = h2['Close'].pct_change().dropna()
        df = pd.concat([r1, r2], axis=1, join='inner')
        if len(df) < 5:
            return None, None
        cov = np.cov(df.iloc[:, 0], df.iloc[:, 1])
        beta = cov[0, 1] / cov[1, 1]
        alpha = np.mean(df.iloc[:, 0]) - beta * np.mean(df.iloc[:, 1])
        alpha_annual = alpha * 252
        return round(beta, 3), round(alpha_annual, 4)
    except Exception as e:
        logger.debug("tinh_beta(%s): %s", ma_yahoo, e)
        return None, None

def tinh_treynor_ratio(loi_nhuan_nam, beta, rf=0.05):
    if beta is None or beta == 0:
        return None
    return (loi_nhuan_nam - rf) / beta

def tinh_calmar_ratio(cagr, max_dd):
    if max_dd is None or max_dd >= 0:
        return None
    return cagr / abs(max_dd)

def tinh_information_ratio(loi_nhuan_ngay, benchmark_ngay):
    if len(loi_nhuan_ngay) < 2 or len(benchmark_ngay) < 2:
        return None
    min_len = min(len(loi_nhuan_ngay), len(benchmark_ngay))
    td = loi_nhuan_ngay[-min_len:] - benchmark_ngay[-min_len:]
    if np.std(td) == 0:
        return None
    return np.mean(td) / np.std(td) * np.sqrt(252)

def tinh_omega_ratio(loi_nhuan_ngay, threshold=0):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < 2:
        return None
    gains = loi_nhuan_ngay[loi_nhuan_ngay > threshold].sum()
    losses = abs(loi_nhuan_ngay[loi_nhuan_ngay < threshold].sum())
    return gains / losses if losses > 0 else None

def tinh_profit_factor(loi_nhuan_ngay):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < 2:
        return None
    gross_profit = loi_nhuan_ngay[loi_nhuan_ngay > 0].sum()
    gross_loss = abs(loi_nhuan_ngay[loi_nhuan_ngay < 0].sum())
    return gross_profit / gross_loss if gross_loss > 0 else None

def tinh_win_rate(loi_nhuan_ngay):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < 2:
        return None
    return np.sum(loi_nhuan_ngay > 0) / len(loi_nhuan_ngay)

def tinh_ulcer_index(gia):
    if gia is None or len(gia) < 2:
        return None
    peak = np.maximum.accumulate(gia)
    dd_pct = (gia - peak) / peak * 100
    return np.sqrt(np.mean(dd_pct ** 2))

def tinh_tracking_error(loi_nhuan_ngay, benchmark_ngay):
    if len(loi_nhuan_ngay) < 2 or len(benchmark_ngay) < 2:
        return None
    min_len = min(len(loi_nhuan_ngay), len(benchmark_ngay))
    diff = loi_nhuan_ngay[-min_len:] - benchmark_ngay[-min_len:]
    return np.std(diff) * np.sqrt(252)

def tinh_downside_deviation(loi_nhuan_ngay, mar=0):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < 2:
        return None
    downside = loi_nhuan_ngay[loi_nhuan_ngay < mar]
    return np.sqrt(np.mean((downside - mar) ** 2)) if len(downside) > 0 else 0

def tinh_autocorrelation(loi_nhuan_ngay, lag=1):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < lag + 2:
        return None
    return float(pd.Series(loi_nhuan_ngay).autocorr(lag=lag))

def tinh_jarque_bera(loi_nhuan_ngay):
    if loi_nhuan_ngay is None or len(loi_nhuan_ngay) < 10:
        return None, None
    try:
        stat, pval = scipy_stats.jarque_bera(loi_nhuan_ngay)
        return round(stat, 2), round(pval, 4)
    except Exception:
        return None, None

def tinh_bollinger(gia, window=20, n_std=2):
    if gia is None or len(gia) < window:
        return np.array([]), np.array([]), np.array([])
    series = pd.Series(gia)
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + n_std * std
    lower = ma - n_std * std
    return ma.values, upper.values, lower.values

def lay_lich_su_gia(ma_yahoo, ky_han="1y"):
    try:
        import yfinance as yf
        import contextlib, io
        ticker = yf.Ticker(ma_yahoo)
        with contextlib.redirect_stderr(io.StringIO()):
            hist = ticker.history(period=ky_han)
        if hist.empty or len(hist) < 5:
            return None
        return hist
    except:
        return None

def phan_tich_lich_su(ma_yahoo, ky_han="1y", benchmark="FUEVN100.VN"):
    try:
        hist = lay_lich_su_gia(ma_yahoo, ky_han)
        if hist is None or len(hist) < 5:
            return None

        gia_dong = hist['Close'].dropna().values
        if len(gia_dong) < 5:
            return None
        loi_nhuan_ngay = np.diff(gia_dong) / gia_dong[:-1]
        loi_nhuan_ngay = loi_nhuan_ngay[~np.isnan(loi_nhuan_ngay)]
        loi_nhuan_ngay = loi_nhuan_ngay[~np.isinf(loi_nhuan_ngay)]
        if len(loi_nhuan_ngay) < 4:
            return None

        so_nam = len(gia_dong) / 252
        cagr = tinh_cagr(gia_dong[0], gia_dong[-1], so_nam) if so_nam > 0 else 0
        max_dd, dd_point = tinh_max_drawdown(gia_dong)
        dd_series = tinh_drawdown_series(gia_dong)
        var_95 = tinh_var(loi_nhuan_ngay, 0.95)
        var_99 = tinh_var(loi_nhuan_ngay, 0.99)
        cvar_95 = tinh_cvar(loi_nhuan_ngay, 0.95)
        cvar_99 = tinh_cvar(loi_nhuan_ngay, 0.99)
        sortino = tinh_sortino(loi_nhuan_ngay, 0.05/252)
        rui_ro_ngay = np.std(loi_nhuan_ngay)
        rui_ro_nam = rui_ro_ngay * np.sqrt(252)
        loi_nhuan_tb_nam = np.mean(loi_nhuan_ngay) * 252
        sharp = tinh_sharpe_ratio(loi_nhuan_tb_nam, rui_ro_nam)

        skew = float(pd.Series(loi_nhuan_ngay).skew())
        kurt = float(pd.Series(loi_nhuan_ngay).kurtosis())

        rolling_sharpe = tinh_rolling_sharpe(loi_nhuan_ngay, 63)
        rsi = tinh_rsi(gia_dong, 14)
        macd_line, signal_line, macd_hist = tinh_macd(gia_dong, 12, 26, 9)
        bb_ma, bb_upper, bb_lower = tinh_bollinger(gia_dong, 20, 2)

        loi_nhuan_tb_ngay = loi_nhuan_tb_nam / 252
        rui_ro_ngay_du_bao = rui_ro_nam / np.sqrt(252)
        so_ngay_du_bao = 126
        nhiem_ngau_nhien = np.random.normal(loi_nhuan_tb_ngay, rui_ro_ngay_du_bao, so_ngay_du_bao)
        gia_cuoi = gia_dong[-1] * np.cumprod(1 + nhiem_ngau_nhien)
        du_bao_6m = float(np.median(gia_cuoi))

        loi_nhuan_tich_luy = np.cumprod(1 + loi_nhuan_ngay) - 1

        beta, alpha = tinh_beta(ma_yahoo, benchmark, ky_han)
        treynor = tinh_treynor_ratio(loi_nhuan_tb_nam, beta) if beta else None
        calmar = tinh_calmar_ratio(cagr, max_dd)
        ulcer = tinh_ulcer_index(gia_dong)
        win_rate = tinh_win_rate(loi_nhuan_ngay)
        profit_factor = tinh_profit_factor(loi_nhuan_ngay)
        omega = tinh_omega_ratio(loi_nhuan_ngay)
        downside_dev = tinh_downside_deviation(loi_nhuan_ngay)
        autocorr_1 = tinh_autocorrelation(loi_nhuan_ngay, 1)
        autocorr_5 = tinh_autocorrelation(loi_nhuan_ngay, 5)
        jb_stat, jb_pval = tinh_jarque_bera(loi_nhuan_ngay)

        tracking_error = None
        try:
            hist_bm = lay_lich_su_gia(benchmark, ky_han)
            if hist_bm is not None and len(hist_bm) >= 2:
                bm_gia = hist_bm['Close'].values
                bm_ln = np.diff(bm_gia) / bm_gia[:-1]
                tracking_error = tinh_tracking_error(loi_nhuan_ngay, bm_ln)
        except:
            pass

        return {
            "cagr": cagr,
            "max_drawdown": max_dd,
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "sortino": sortino,
            "sharpe": sharp,
            "rui_ro_nam": rui_ro_nam,
            "loi_nhuan_tb_nam": loi_nhuan_tb_nam,
            "du_bao_6m": du_bao_6m,
            "gia_hien_tai": gia_dong[-1],
            "so_ngay": len(gia_dong),
            "loi_nhuan_ngay": loi_nhuan_ngay,
            "loi_nhuan_tich_luy": loi_nhuan_tich_luy,
            "gia_dong": gia_dong,
            "ngay": hist.index,
            "skewness": skew,
            "kurtosis": kurt,
            "rolling_sharpe": rolling_sharpe,
            "drawdown_series": dd_series,
            "rsi": rsi,
            "macd_line": macd_line,
            "signal_line": signal_line,
            "macd_histogram": macd_hist,
            "bb_ma": bb_ma,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "beta": beta,
            "alpha": alpha,
            "treynor": treynor,
            "calmar": calmar,
            "ulcer_index": ulcer,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "omega_ratio": omega,
            "downside_dev": downside_dev,
            "autocorr_1": autocorr_1,
            "autocorr_5": autocorr_5,
            "jb_stat": jb_stat,
            "jb_pval": jb_pval,
            "tracking_error": tracking_error,
        }
    except Exception as e:
        logger.warning("phan_tich_lich_su(%s): %s", ma_yahoo, e)
        return None

def tinh_tuong_quan(cac_ma_yahoo, ky_han="1y"):
    import yfinance as yf
    import contextlib, io
    du_lieu = {}
    for ma in cac_ma_yahoo:
        try:
            ticker = yf.Ticker(ma)
            with contextlib.redirect_stderr(io.StringIO()):
                hist = ticker.history(period=ky_han)
            if not hist.empty:
                du_lieu[ma] = hist['Close'].pct_change().dropna()
        except:
            pass

    if len(du_lieu) < 2:
        return None

    df = pd.DataFrame(du_lieu)
    return df.corr()

def phan_tich_danh_muc_nang_cao(ty_trong, cac_ma=None):
    if cac_ma is None:
        return None

    phan_tich = {}
    tong_loi_nhuan = 0
    tong_rui_ro = 0

    for ma, ty_trong_ma in zip(cac_ma, ty_trong):
        if ty_trong_ma <= 0:
            continue
        pt = phan_tich_lich_su(ma, "2y")
        if pt:
            phan_tich[ma] = {
                "ty_trong": ty_trong_ma,
                "cagr": pt["cagr"],
                "max_dd": pt["max_drawdown"],
                "sharpe": pt["sharpe"],
                "var_95": pt["var_95"],
            }
            tong_loi_nhuan += pt["cagr"] * ty_trong_ma
            tong_rui_ro += pt["rui_ro_nam"] * ty_trong_ma

    return {
        "chi_tiet": phan_tich,
        "tong_loi_nhuan": tong_loi_nhuan,
        "tong_rui_ro": tong_rui_ro,
        "sharpe_danh_muc": tong_loi_nhuan / tong_rui_ro if tong_rui_ro > 0 else 0,
    }
