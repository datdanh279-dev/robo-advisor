import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestDataLoaderConfig(unittest.TestCase):
    def test_excel_path_configured(self):
        from backend.data_loader import EXCEL_PATH
        self.assertIsNotNone(EXCEL_PATH)
        self.assertIsInstance(EXCEL_PATH, str)
        self.assertTrue(len(EXCEL_PATH) > 0)

    def test_docs_structure(self):
        from backend.data_loader import DOCS
        required_keys = {"live", "co_phieu_vn", "co_phieu_tg", "danh_muc",
                         "kpi", "liquid", "esg", "performance", "stress_vars",
                         "stress", "ngay_cap_nhat", "danh_sach_portfolio"}
        for key in required_keys:
            self.assertIn(key, DOCS, f"Missing key: {key}")

    def test_ngay_cap_nhat_format(self):
        from backend.data_loader import DOCS
        self.assertRegex(DOCS["ngay_cap_nhat"], r"\d{2}/\d{2}/\d{4}")

    def test_danh_sach_portfolio(self):
        from backend.data_loader import DOCS
        self.assertIsInstance(DOCS["danh_sach_portfolio"], list)
        if DOCS["danh_sach_portfolio"]:
            self.assertIsInstance(DOCS["danh_sach_portfolio"][0], str)

    def test_performance_has_rf(self):
        from backend.data_loader import DOCS
        perf = DOCS.get("performance", {})
        self.assertIn("Rf", perf)


if __name__ == "__main__":
    unittest.main()
