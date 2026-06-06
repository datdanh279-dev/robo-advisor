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
    "dm": {"VCB": {"ten": "Vietcombank"}},
    "kpi": {"VCB": {"pe": 15.7, "roe": 16.4, "ten": "Vietcombank"}},
    "market_data": [{"ma": "VCB", "ten": "Vietcombank", "gia": 95000, "ret_3m": 5.0, "vol_ratio": 1.2, "nganh": "Ngân hàng", "von_hoa": 5.19e14}],
    "risk_profile": "Trung bình"
}

r = chat_advisor.tim_cau_tra_loi(cau_hoi, [], context=ctx)
if r:
    print(f"=== FULL RESULT ({len(r)} chars) ===")
    # Skip MO_DAU and print the rest
    skip_marker = "ĐÁNH GIÁ TỔNG HỢP" if "ĐÁNH GIÁ TỔNG HỢP" in r.upper() else "Đánh giá tổng hợp"
    if skip_marker.lower() in r.lower():
        idx = r.lower().find(skip_marker.lower())
        # Go back to find the start
        start = r.rfind("\n", 0, idx - 200) if idx > 200 else 0
        print(r[start:idx + 500])
    else:
        print(r[1000:2000])
else:
    print("None")
