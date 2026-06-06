try:
    import app
    print("IMPORT OK")
    print(f"app module: {app.__name__}")
    print(f"has hoi_dong_chuyen_gia: {hasattr(app, 'hoi_dong_chuyen_gia')}")
    print(f"has _build_chat_context: {hasattr(app, '_build_chat_context')}")
except Exception as e:
    import traceback
    traceback.print_exc()
