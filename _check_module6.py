import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor
import re

# Patch the file content
src = open(chat_advisor.__file__, 'r', encoding='utf-8').read()
# Insert traces
patched = src.replace(
    "def _xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx):",
    "def _xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx):\n    import sys\n    print('[TRACE_SMART] entered', file=sys.stderr)"
).replace(
    "if any(kw in cau_thuong or kw in cau_khong_dau for kw in intent_nen_mua):\n        return _goi_y_mua_theo_risk(risk, market_data, dm, kpi)",
    "if any(kw in cau_thuong or kw in cau_khong_dau for kw in intent_nen_mua):\n        print('[TRACE_SMART] match nen_mua', file=sys.stderr)\n        return _goi_y_mua_theo_risk(risk, market_data, dm, kpi)"
).replace(
    "if ma_match and (kpi or market_data):",
    "print(f'[TRACE_SMART] ma_match={ma_match}, kpi_keys={list((kpi or {}).keys())[:5]}', file=sys.stderr)\n    if ma_match and (kpi or market_data):"
).replace(
    "    return None\n\n\ndef _phan_tich_danh_muc_user(",
    "    print('[TRACE_SMART] returning None', file=sys.stderr)\n    return None\n\n\ndef _phan_tich_danh_muc_user("
)

# Write to a temp module
import importlib.util
spec = importlib.util.spec_from_loader("traced", loader=None)
mod = importlib.util.module_from_spec(spec)
exec(compile(patched, chat_advisor.__file__, 'exec'), mod.__dict__)

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

result = mod._xu_ly_smart(cau_hoi, cau_thuong, cau_khong_dau, ctx)
print(f"\n=== RESULT ===\n{result[:300] if result else 'None'}")
