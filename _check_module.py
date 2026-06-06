import sys
sys.path.insert(0, r"C:\Users\ACER\robo-advisor")
import backend.chat_advisor
print("FILE:", backend.chat_advisor.__file__)
import os
print("MTIME:", os.path.getmtime(backend.chat_advisor.__file__))

# Try to import chat_advisor the same way the test does
import os
os.chdir(r"C:\Users\ACER\robo-advisor")
sys.path.insert(0, ".")
import chat_advisor as ca2
print("FILE2:", ca2.__file__)
