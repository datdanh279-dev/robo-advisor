import sys
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor
print("Module:", chat_advisor.__file__)
print("smart func id:", id(chat_advisor._xu_ly_smart))
print("tim func id:", id(chat_advisor.tim_cau_tra_loi))
import inspect
src = inspect.getsource(chat_advisor._xu_ly_smart)
print("First 300 chars of smart:")
print(src[:300])
print()
print("Last 500 chars of smart:")
print(src[-500:])
