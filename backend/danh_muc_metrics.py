"""Chỉ số danh mục — không import data_loader/portfolio (tránh circular import trên Streamlit)."""


def tinh_return_danh_muc(danh_muc):
    """Trả về (tổng GT thị trường, tổng vốn, lãi/lỗ, % return trên giá trị thị trường).

    % return = lãi ròng / tổng GT thị trường. Đây là % "lợi nhuận trên tài sản
    hiện tại" (~10.7% với danh mục 8 mã hiện tại) — khớp với % Lãi/Lỗ tổng quan
    ở tab Tổng quan. Không dùng Rp từ performance.json (có thể lệch do cache Excel).
    """
    tong_gt = sum(
        info.get("gia_thi_truong", 0) * info.get("so_luong", 0)
        for info in danh_muc.values()
    )
    tong_von = sum(
        info.get("gia_von", 0) * info.get("so_luong", 0)
        for info in danh_muc.values()
    )
    tong_lai_lo = sum(
        (info.get("gia_thi_truong", 0) - info.get("gia_von", 0)) * info.get("so_luong", 0)
        for info in danh_muc.values()
    )
    return_pct = (tong_lai_lo / tong_gt * 100) if tong_gt else 0.0
    return tong_gt, tong_von, tong_lai_lo, return_pct
