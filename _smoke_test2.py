try:
    from backend import expert_panel, chat_advisor
    print("EXPERTS:", len(expert_panel.EXPERTS))
    for e in expert_panel.EXPERTS:
        print(f"  - {e['id']}: {e['name']} ({e['title']}) [{e['backend']}/{e['model']}]")
    print("CHAT_ADVISOR functions:", [f for f in dir(chat_advisor) if not f.startswith('_')][:10])
except Exception as e:
    import traceback
    traceback.print_exc()
