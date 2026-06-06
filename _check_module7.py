import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor

# Replace _xu_ly_smart with traced version using line-by-line execution
import inspect

src = inspect.getsource(chat_advisor._xu_ly_smart)
# Inject traces after each `return ` line
traced = []
for line in src.split("\n"):
    traced.append(line)
    if line.strip().startswith("return "):
        indent = len(line) - len(line.lstrip())
        var = line.strip()[7:]  # strip "return "
        traced.append(" " * indent + f"print(f'[T] return {{{var}!r}}', flush=True)")

new_src = "\n".join(traced)
print("PATCHED SMART SRC (first 1000):")
print(new_src[:1000])
print("---")
print("LAST 500:")
print(new_src[-500:])

# Execute
exec_globals = dict(chat_advisor.__dict__)
exec_globals.update({
    "__builtins__": __builtins__,
    "MO_DAU": chat_advisor.MO_DAU,
    "_phan_tich_danh_muc_user": chat_advisor._phan_tich_danh_muc_user,
    "_goi_y_phan_bo": chat_advisor._goi_y_phan_bo,
    "_goi_y_mua_theo_risk": chat_advisor._goi_y_mua_theo_risk,
})

# Just print
print("\n=== EXECUTING ===\n")
try:
    exec(compile(new_src, "<smart>", "exec"), exec_globals)
except Exception as e:
    print(f"Error: {e}")
