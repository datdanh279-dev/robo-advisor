import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor
src = open(chat_advisor.__file__, 'r', encoding='utf-8').read()
# Find _xu_ly_smart
start = src.find("def _xu_ly_smart")
end = src.find("\ndef ", start+1)
smart_src = src[start:end]
print("FIRST 500 chars of _xu_ly_smart:")
print(smart_src[:500])
print("---")
print("LAST 500 chars:")
print(smart_src[-500:])
