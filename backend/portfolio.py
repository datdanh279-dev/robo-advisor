import numpy as np
import pandas as pd
from .data_loader import DOCS

# Floating-Point Safety: tất cả mảng tỷ trọng đều được làm tròn và chuẩn hóa
# trước khi nạp vào thuật toán tối ưu, tránh lỗi sum=0.9999999 gây treo scipy
def _chuan_hoa_ty_trong(w, decimals=8):
    w = np.round(np.array(w, dtype=np.float64), decimals)
    w = np.clip(w, 0, 1)
    w = w / w.sum() if w.sum() > 0 else w
    return w

# Lưu ý (GIGO fix): Các giá trị loi_nhuan_trung_binh dưới đây là
# LỢI NHUẬN TRUNG BÌNH LỊCH SỬ của từng kênh (Historical Mean Returns),
# KHÔNG phải dự báo hồi quy tuyến tính. Dùng historical mean returns
# cho MPT (Modern Portfolio Theory) ổn định hơn forecast từ linear regression.
#
# Nguồn tham khảo: VN-Index CAGR 5 năm ~8-10%, lãi suất TK ~5%,
# vàng ~8-10%/năm (dài hạn), crypto ~30-50%/năm (rủi ro cao).


THONG_TIN_KENH = {
    "Tiền gửi/Ngân hàng": {
        "loi_nhuan_trung_binh": 0.05,
        "rui_ro": 0.01,
        "thanh_khoan": 1.0,
        "mo_ta": "Gửi tiết kiệm ngân hàng với lãi suất cố định",
    },
    "Trái phiếu chính phủ": {
        "loi_nhuan_trung_binh": 0.07,
        "rui_ro": 0.03,
        "thanh_khoan": 0.7,
        "mo_ta": "Trái phiếu do Kho bạc Nhà nước phát hành",
    },
    "Vàng": {
        "loi_nhuan_trung_binh": 0.08,
        "rui_ro": 0.12,
        "thanh_khoan": 0.9,
        "mo_ta": "Vàng miếng, vàng nhẫn, vàng SJC",
    },
    "Cổ phiếu blue-chip": {
        "loi_nhuan_trung_binh": 0.14,
        "rui_ro": 0.18,
        "thanh_khoan": 0.9,
        "mo_ta": "Cổ phiếu vốn hóa lớn trên HOSE (VN30)",
    },
    "Bất động sản": {
        "loi_nhuan_trung_binh": 0.12,
        "rui_ro": 0.20,
        "thanh_khoan": 0.3,
        "mo_ta": "Đất nền, căn hộ, nhà phố",
    },
    "Cổ phiếu tăng trưởng": {
        "loi_nhuan_trung_binh": 0.20,
        "rui_ro": 0.30,
        "thanh_khoan": 0.8,
        "mo_ta": "Cổ phiếu vốn hóa vừa và nhỏ có tiềm năng tăng trưởng",
    },
    "Chứng chỉ quỹ/ETF": {
        "loi_nhuan_trung_binh": 0.12,
        "rui_ro": 0.14,
        "thanh_khoan": 0.95,
        "mo_ta": "Quỹ ETF VN30, quỹ mở trái phiếu, quỹ cân bằng",
    },
    "Tiền điện tử": {
        "loi_nhuan_trung_binh": 0.35,
        "rui_ro": 0.55,
        "thanh_khoan": 0.8,
        "mo_ta": "Bitcoin, Ethereum và các altcoin tiềm năng",
    },
}

MA_TRAN_TUONG_QUAN = pd.DataFrame(
    {
        "Tiền gửi/Ngân hàng": [1.0, 0.2, 0.1, 0.1, 0.0, 0.0, 0.1, 0.0],
        "Trái phiếu chính phủ": [0.2, 1.0, 0.3, 0.2, 0.1, 0.1, 0.3, 0.0],
        "Vàng": [0.1, 0.3, 1.0, 0.2, 0.3, 0.1, 0.15, 0.2],
        "Cổ phiếu blue-chip": [0.1, 0.2, 0.2, 1.0, 0.4, 0.6, 0.6, 0.2],
        "Bất động sản": [0.0, 0.1, 0.3, 0.4, 1.0, 0.3, 0.2, 0.1],
        "Cổ phiếu tăng trưởng": [0.0, 0.1, 0.1, 0.6, 0.3, 1.0, 0.4, 0.3],
        "Chứng chỉ quỹ/ETF": [0.1, 0.3, 0.15, 0.6, 0.2, 0.4, 1.0, 0.15],
        "Tiền điện tử": [0.0, 0.0, 0.2, 0.2, 0.1, 0.3, 0.15, 1.0],
    },
    index=[
        "Tiền gửi/Ngân hàng",
        "Trái phiếu chính phủ",
        "Vàng",
        "Cổ phiếu blue-chip",
        "Bất động sản",
        "Cổ phiếu tăng trưởng",
        "Chứng chỉ quỹ/ETF",
        "Tiền điện tử",
    ],
)


def tinh_toan_danh_muc(ty_trong):
    ty_trong = _chuan_hoa_ty_trong(ty_trong)
    loi_nhuan = np.array([THONG_TIN_KENH[k]["loi_nhuan_trung_binh"] for k in THONG_TIN_KENH])
    rui_ro = np.array([THONG_TIN_KENH[k]["rui_ro"] for k in THONG_TIN_KENH])

    ma_tran_hiep_bien = MA_TRAN_TUONG_QUAN.values * np.outer(rui_ro, rui_ro)
    np.fill_diagonal(ma_tran_hiep_bien, rui_ro**2)

    loi_nhuan_ky_vong = np.dot(ty_trong, loi_nhuan)
    phuong_sai = np.dot(ty_trong.T, np.dot(ma_tran_hiep_bien, ty_trong))
    rui_ro_danh_muc = np.sqrt(phuong_sai)

    sharp_ratio = (loi_nhuan_ky_vong - DOCS.get("performance", {}).get("Rf", 0.05)) / rui_ro_danh_muc if rui_ro_danh_muc > 0 else 0

    return {
        "loi_nhuan_ky_vong": loi_nhuan_ky_vong,
        "rui_ro_danh_muc": rui_ro_danh_muc,
        "sharp_ratio": sharp_ratio,
    }


def mo_phong_monte_carlo(so_lan=1000):
    np.random.seed(None)
    n = len(THONG_TIN_KENH)
    loi_nhuan = np.array([THONG_TIN_KENH[k]["loi_nhuan_trung_binh"] for k in THONG_TIN_KENH])
    rui_ro = np.array([THONG_TIN_KENH[k]["rui_ro"] for k in THONG_TIN_KENH])
    ma_tran_hiep_bien = MA_TRAN_TUONG_QUAN.values * np.outer(rui_ro, rui_ro)
    np.fill_diagonal(ma_tran_hiep_bien, rui_ro**2)

    ket_qua = []
    for _ in range(so_lan):
        w = _chuan_hoa_ty_trong(np.random.dirichlet(np.ones(n), 1)[0])
        loi_nhuan_kv = np.dot(w, loi_nhuan)
        phuong_sai = np.dot(w.T, np.dot(ma_tran_hiep_bien, w))
        rui_ro_dm = np.sqrt(phuong_sai)
        rf = DOCS.get("performance", {}).get("Rf", 0.05)
        sharp = (loi_nhuan_kv - rf) / rui_ro_dm if rui_ro_dm > 0 else 0
        ket_qua.append((w, loi_nhuan_kv, rui_ro_dm, sharp))

    return ket_qua


def toi_uu_danh_muc():
    from scipy.optimize import minimize

    n = len(THONG_TIN_KENH)
    loi_nhuan = np.array([THONG_TIN_KENH[k]["loi_nhuan_trung_binh"] for k in THONG_TIN_KENH])
    rui_ro = np.array([THONG_TIN_KENH[k]["rui_ro"] for k in THONG_TIN_KENH])
    ma_tran_hiep_bien = MA_TRAN_TUONG_QUAN.values * np.outer(rui_ro, rui_ro)
    np.fill_diagonal(ma_tran_hiep_bien, rui_ro**2)

    def ham_muc_tieu(w):
        w = np.array(w)
        p = np.dot(w.T, np.dot(ma_tran_hiep_bien, w))
        return p

    constraints = ({"type": "eq", "fun": lambda x: np.sum(x) - 1},)
    bounds = tuple((0, 1) for _ in range(n))

    w0 = np.array([1.0 / n] * n)
    ket_qua = minimize(ham_muc_tieu, w0, method="SLSQP", bounds=bounds, constraints=constraints, options={"ftol": 1e-10, "maxiter": 1000})

    w = _chuan_hoa_ty_trong(ket_qua.x)
    return w


def tinh_toan_phan_bo_lai_lo(ty_trong, so_tien_dau_tu, ty_le_loi_nhuan_thi_truong=None):
    if ty_le_loi_nhuan_thi_truong is None:
        ty_le_loi_nhuan_thi_truong = {
            "Tiền gửi/Ngân hàng": 0.05,
            "Trái phiếu chính phủ": 0.07,
            "Chứng chỉ quỹ/ETF": 0.14,
            "Vàng": 0.10,
            "Cổ phiếu blue-chip": 0.18,
            "Bất động sản": 0.15,
            "Cổ phiếu tăng trưởng": 0.25,
            "Tiền điện tử": 0.40,
        }

    ket_qua = {}
    tong_gia_tri = 0
    tong_lai_lo = 0

    for kenh in ty_trong:
        ty_trong_kenh = ty_trong[kenh]
        so_tien = so_tien_dau_tu * ty_trong_kenh
        lai_lo_ty_le = ty_le_loi_nhuan_thi_truong.get(kenh, 0)
        lai_lo = so_tien * lai_lo_ty_le
        gia_tri_cuoi = so_tien + lai_lo
        tong_gia_tri += gia_tri_cuoi
        tong_lai_lo += lai_lo
        ket_qua[kenh] = {
            "so_tien_dau_tu": round(so_tien, -3),
            "lai_lo": round(lai_lo, -3),
            "gia_tri_cuoi": round(gia_tri_cuoi, -3),
            "ty_suat_loi_nhuan": lai_lo_ty_le,
        }

    return ket_qua, round(tong_gia_tri, -3), round(tong_lai_lo, -3)
