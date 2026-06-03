import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPortfolio(unittest.TestCase):
    def test_tinh_toan_danh_muc(self):
        from backend.portfolio import tinh_toan_danh_muc
        result = tinh_toan_danh_muc([0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1])
        self.assertIn("loi_nhuan_ky_vong", result)
        self.assertIn("rui_ro_danh_muc", result)
        self.assertIn("sharp_ratio", result)
        self.assertGreaterEqual(result["loi_nhuan_ky_vong"], 0)
        self.assertGreaterEqual(result["rui_ro_danh_muc"], 0)

    def test_phan_bo_danh_muc(self):
        from backend.risk_profile import phan_bo_danh_muc
        result = phan_bo_danh_muc("Trung dung", 10_000_000)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)

    def test_danh_gia_rui_ro(self):
        from backend.risk_profile import danh_gia_rui_ro
        loai, diem, mo_ta, danh_muc = danh_gia_rui_ro({})
        self.assertIn(loai, ["Bảo thủ", "Thận trọng", "Trung dung", "Tăng trưởng", "Táo bạo"])
        self.assertIsInstance(diem, int)
        self.assertIsInstance(mo_ta, str)
        self.assertIsInstance(danh_muc, dict)


if __name__ == "__main__":
    unittest.main()
