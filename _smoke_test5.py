import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend import chat_advisor
ctx = {
    "dm": [{"ma": "VCB", "ten": "Vietcombank", "ty_trong": 25.0, "gia": 95000, "return_pct": 5.0}],
    "kpi": {"VCB": {"pe": 15.7, "pb": 2.3, "roe": 16.4, "dividend_yield": 0.7, "ten": "Vietcombank"}},
    "market_data": [
        {"ma": "VCB", "ten": "Vietcombank", "gia": 95000, "ret_3m": 5.0, "vol_ratio": 1.2, "nganh": "Ngân hàng", "von_hoa": 5.19e14},
        {"ma": "HPG", "ten": "Hòa Phát", "gia": 27500, "ret_3m": 8.0, "vol_ratio": 1.3, "nganh": "Thép", "von_hoa": 1.5e14},
        {"ma": "FPT", "ten": "FPT Corp", "gia": 145000, "ret_3m": 12.0, "vol_ratio": 0.9, "nganh": "Công nghệ", "von_hoa": 1.6e14},
    ],
    "risk_profile": "Trung bình"
}
queries = [
    "Phân tích VCB",
    "phan tich vcb",
    "VCB có tốt không",
    "Đánh giá HPG",
    "review FPT",
    "Mã nào an toàn?",
    "Danh mục của tôi",
    "Mã nào đang tăng?",
    "Phân bổ 100 triệu",
    "Top vốn hóa lớn nhất",
]
for q in queries:
    r = chat_advisor.tim_cau_tra_loi(q, [], context=ctx)
    if r:
        print(f"Q: {q}")
        print(f"   → {r[:200]}...")
    else:
        print(f"Q: {q} → None")
