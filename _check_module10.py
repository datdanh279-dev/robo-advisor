import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
from backend import chat_advisor
import dis

# Print the actual function bytecode
print("=== Disassembly of _xu_ly_smart ===")
dis.dis(chat_advisor._xu_ly_smart)
