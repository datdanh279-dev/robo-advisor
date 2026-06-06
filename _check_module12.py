import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
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

for q in ["Phân tích VCB", "Đánh giá HPG", "review FPT", "Danh mục của tôi"]:
    r = chat_advisor.tim_cau_tra_loi(q, [], context=ctx)
    if r:
        # Find the analysis section
        idx = r.find("📊 **Dữ liệu real-time:**")
        if idx > 0:
            end = r.find("\n\n💡", idx)
            print(f"=== {q} ===")
            print(r[idx:end if end > 0 else idx+500])
            print()
        else:
            idx2 = r.find("📊 **PHÂN TÍCH")
            if idx2 > 0:
                print(f"=== {q} (DM analysis) ===")
                print(r[idx2:idx2+500])
                print()
            else:
                print(f"=== {q} (first 200 after MO_DAU) ===")
                # MO_DAU ends at "GÓC NHÌN CHUYÊN GIA" line
                mo_dau_end = r.find("GÓC NHÌN CHUYÊN GIA")
                if mo_dau_end > 0:
                    print(r[mo_dau_end:mo_dau_end+500])
                else:
                    print(r[:300])
                print()
    else:
        print(f"=== {q} → None ===\n")
