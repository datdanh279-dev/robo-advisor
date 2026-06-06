import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend import chat_advisor
import re

cau_hoi = "Phân tích VCB"
cau_thuong = cau_hoi.lower().strip()
from backend.chat_advisor import xu_ly_bo_dau
cau_khong_dau = xu_ly_bo_dau(cau_thuong)
print(f"cau_thuong: {cau_thuong!r}")
print(f"cau_khong_dau: {cau_khong_dau!r}")
ctx = {
    "dm": {"VCB": {"ten": "Vietcombank", "ty_trong": 25.0, "gia": 95000, "return_pct": 5.0}},
    "kpi": {"VCB": {"pe": 15.7, "pb": 2.3, "roe": 16.4, "dividend_yield": 0.7, "ten": "Vietcombank"}},
    "market_data": [{"ma": "VCB", "ten": "Vietcombank", "gia": 95000, "ret_3m": 5.0, "vol_ratio": 1.2, "nganh": "Ngân hàng", "von_hoa": 5.19e14}],
    "risk_profile": "Trung bình"
}
smart = chat_advisor._xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx)
print(f"smart: {smart[:200] if smart else None}")
print()

# Re-test intent matching
intent_phan_tich_ma = ["phân tích mã", "phan tich ma", "đánh giá mã", "danh gia ma",
                       "mã này có tốt", "ma nay co tot", "review mã", "review ma",
                       "thông tin về mã", "thong tin ve ma", "nên giữ", "nen giu",
                       "phân tích", "phan tich", "đánh giá", "danh gia", "review",
                       "thông tin", "thong tin", "có tốt", "co tot"]
print("Intent match test:")
for kw in intent_phan_tich_ma:
    if kw in cau_thuong or kw in cau_khong_dau:
        print(f"  ✓ Match: {kw!r}")

words = re.findall(r"\b[A-Z]{3,4}\b", cau_hoi.upper())
print(f"  words: {words}")

kpi = ctx["kpi"]
market_data = ctx["market_data"]
for w in words:
    if w in (kpi or {}) or any(d.get("ma") == w for d in market_data or []):
        print(f"  ✓ ma_match: {w}")
        break
