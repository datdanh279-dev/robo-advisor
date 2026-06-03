"""Chỉ số danh mục — không import data_loader/portfolio (tránh circular import trên Streamlit)."""


def tinh_return_danh_muc(danh_muc):
    """Trả về (tổng GT, tổng vốn, lãi/lỗ, % return trên giá trị thị trường)."""
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
