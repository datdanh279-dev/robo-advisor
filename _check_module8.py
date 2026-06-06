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

# Manually execute each intent check
dm = ctx["dm"]
kpi = ctx["kpi"]
market_data = ctx["market_data"]
real_prices = ctx.get("real_prices", {})
risk = ctx.get("risk_profile", "Trung bình")

def check(name, kw_list):
    matched = [kw for kw in kw_list if kw in cau_thuong or kw in cau_khong_dau]
    print(f"  {name}: {matched if matched else 'no match'}")
    return bool(matched)

print("Intent checks for 'Phân tích VCB':")
check("intent_dm", ["danh mục của tôi", "danh muc cua toi", "dm của tôi", "dm cua toi", "phân tích danh mục", "phan tich danh muc", "review danh mục", "review dm", "nên tăng mã nào", "nen tang ma nao", "nên giảm mã nào", "nen giam ma nao", "danh mục hiện tại", "danh muc hien tai", "portfolio của tôi"])
check("intent_top", ["mã nào đang tăng", "ma nao dang tang", "mã tăng mạnh", "ma tang manh", "top tăng", "top tang", "cổ phiếu tăng", "co phieu tang", "mã nào đang giảm", "ma nao dang giam", "mã giảm mạnh", "ma giam manh", "top giảm", "top giam", "cổ phiếu giảm", "co phieu giam", "mã nào hot", "ma nao hot", "mã nào đáng chú ý", "ma nao dang chu y"])
check("intent_volume", ["mã nào vol cao", "volume đột biến", "volume dot bien", "vol đột biến", "mã nào thanh khoản", "thanh khoản cao", "mã nào giao dịch nhiều"])
check("intent_phan_bo", ["phân bổ vốn", "phan bo von", "phân bổ", "phan bo", "100 triệu", "100 trieu", "200 triệu", "200 trieu", "500 triệu", "500 trieu", "1 tỷ", "1 ty", "1 tỷ", "5 tỷ", "5 ty"])
check("intent_co_tuc", ["cổ tức tốt", "co tuc tot", "cổ tức cao", "co tuc cao", "cổ tức", "co tuc"])
check("intent_nen_mua", ["có nên mua", "co nen mua", "nên mua không", "nen mua khong", "mua mã nào", "mua ma nao", "nên mua mã nào", "nen mua ma nao", "tôi nên mua", "toi nen mua"])
check("intent_an_toan", ["mã nào an toàn", "ma nao an toan", "rủi ro thấp", "rui ro thap", "ít rủi ro", "it rui ro", "blue chip", "ổn định", "on dinh"])
check("intent_von_hoa", ["vốn hóa lớn nhất", "von hoa lon nhat", "blue chip", "cổ phiếu lớn", "co phieu lon", "mã vốn hóa lớn"])
check("intent_phan_tich_ma", ["phân tích mã", "phan tich ma", "đánh giá mã", "danh gia ma", "mã này có tốt", "ma nay co tot", "review mã", "review ma", "thông tin về mã", "thong tin ve ma", "nên giữ", "nen giu", "phân tích", "phan tich", "đánh giá", "danh gia", "review", "thông tin", "thong tin", "có tốt", "co tot"])

# If intent_phan_tich_ma matches, then:
print("\nNow invoking _xu_ly_smart directly:")
r = chat_advisor._xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx)
print(f"  Result type: {type(r)}")
print(f"  Result[:300]: {r[:300] if r else None}")
