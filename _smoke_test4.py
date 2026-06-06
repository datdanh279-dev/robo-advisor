import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend import chat_advisor
print("=== chat_advisor attributes ===")
attrs = [a for a in dir(chat_advisor) if not a.startswith('__')]
for a in attrs:
    obj = getattr(chat_advisor, a)
    if callable(obj):
        print(f"  func: {a}")
    else:
        print(f"  var: {a} = {repr(obj)[:80]}")

print()
print("=== test tim_cau_tra_loi with sample input ===")
try:
    ctx = {
        "dm": [{"ma": "VCB", "ten": "Vietcombank", "ty_trong": 25.0, "gia": 95000, "return_pct": 5.0}],
        "kpi": {"VCB": {"pe": 15.7, "pb": 2.3, "roe": 16.4, "dividend_yield": 0.7}},
        "market_data": [],
        "risk_profile": "Trung bình"
    }
    res = chat_advisor.tim_cau_tra_loi("Phân tích VCB", [], context=ctx)
    print(f"  result type: {type(res)}")
    print(f"  result: {str(res)[:300]}")
except Exception as e:
    import traceback
    traceback.print_exc()
