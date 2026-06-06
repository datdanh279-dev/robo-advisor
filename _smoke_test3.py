import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=== Testing chat_advisor ===")
try:
    from backend import chat_advisor
    print("OK chat_advisor imported")
    if hasattr(chat_advisor, 'tim_cau_tra_loi'):
        print("  has tim_cau_tra_loi()")
    if hasattr(chat_advisor, '_xu_ly_smart'):
        print("  has _xu_ly_smart()")
    if hasattr(chat_advisor, 'INTENT_HANDLERS'):
        print("  INTENT_HANDLERS:", list(chat_advisor.INTENT_HANDLERS.keys()))
except Exception as e:
    import traceback
    traceback.print_exc()

print("=== Testing expert_panel ===")
try:
    from backend import expert_panel
    print("OK expert_panel imported")
    print(f"  6 experts:", [e['id'] for e in expert_panel.EXPERTS])
    print(f"  has hoi_dong_chuyen_gia: {hasattr(expert_panel, 'hoi_dong_chuyen_gia')}")
    print(f"  has _build_error_result: {hasattr(expert_panel, '_build_error_result')}")
    print(f"  has _run_expert_panel_async: {hasattr(expert_panel, '_run_expert_panel_async')}")
except Exception as e:
    import traceback
    traceback.print_exc()

print("=== Testing data_loader ===")
try:
    from backend import data_loader
    print("OK data_loader imported")
    co_vn = data_loader.doc_co_phieu_vn()
    co_tg = data_loader.doc_co_phieu_tg()
    print(f"  VN stocks: {len(co_vn)}, TG stocks: {len(co_tg)}")
except Exception as e:
    import traceback
    traceback.print_exc()
