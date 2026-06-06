import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor

cau_hoi = "Phân tích VCB"
cau_thuong = cau_hoi.lower().strip()
from backend.chat_advisor import xu_ly_bo_dau
cau_khong_dau = xu_ly_bo_dau(cau_thuong)
ctx = {
    "dm": {"VCB": {"ten": "Vietcombank", "ty_trong": 25.0, "gia": 95000, "return_pct": 5.0}},
    "kpi": {"VCB": {"pe": 15.7, "pb": 2.3, "roe": 16.4, "dividend_yield": 0.7, "ten": "Vietcombank"}},
    "market_data": [{"ma": "VCB", "ten": "Vietcombank", "gia": 95000, "ret_3m": 5.0, "vol_ratio": 1.2, "nganh": "Ngân hàng", "von_hoa": 5.19e14}],
    "risk_profile": "Trung bình"
}

# Monkey-patch to add tracing
original_smart = chat_advisor._xu_ly_smart

import functools
@functools.wraps(original_smart)
def traced_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx):
    import traceback
    result = original_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx)
    print(f"\n=== TRACED _xu_ly_smart result ===")
    print(f"cau_hoi: {cau_hoi!r}")
    print(f"result type: {type(result)}")
    if result:
        print(f"result[:200]: {result[:200]}")
    return result

chat_advisor._xu_ly_smart = traced_smart

# Now call tim_cau_tra_loi
r = chat_advisor.tim_cau_tra_loi(cau_hoi, [], context=ctx)
print(f"\n\n=== FINAL RESULT ===")
if r:
    print(f"type: {type(r)}")
    print(f"[:300]: {r[:300]}")
else:
    print("None")
