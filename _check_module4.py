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

# Manually replicate the intent_dm check
intent_dm = ["danh mục của tôi", "danh muc cua toi", "dm của tôi", "dm cua toi",
             "phân tích danh mục", "phan tich danh muc", "review danh mục", "review dm",
             "nên tăng mã nào", "nen tang ma nao", "nên giảm mã nào", "nen giam ma nao",
             "danh mục hiện tại", "danh muc hien tai", "portfolio của tôi"]
dm_match = any(kw in cau_thuong or kw in cau_khong_dau for kw in intent_dm)
print(f"intent_dm match: {dm_match}")

# intent_top
intent_top = ["mã nào đang tăng", "ma nao dang tang", "mã tăng mạnh", "ma tang manh",
              "top tăng", "top tang", "cổ phiếu tăng", "co phieu tang",
              "mã nào đang giảm", "ma nao dang giam", "mã giảm mạnh", "ma giam manh",
              "top giảm", "top giam", "cổ phiếu giảm", "co phieu giam",
              "mã nào hot", "ma nao hot", "mã nào đáng chú ý", "ma nao dang chu y"]
top_match = any(kw in cau_thuong or kw in cau_khong_dau for kw in intent_top)
print(f"intent_top match: {top_match}")

# What about tim_quy?
from backend.chat_advisor import QUY_KW, tim_quy
qy = tim_quy(cau_thuong, cau_khong_dau)
if qy:
    print(f"tim_quy matched: {qy[:200]}")
else:
    print("tim_quy: None")

# Now call _xu_ly_smart
smart = chat_advisor._xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx)
print(f"\nsmart result: {smart[:400] if smart else 'None'}")
