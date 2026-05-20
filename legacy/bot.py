import pyautogui
import time

print("Start za 5 sekund...")
time.sleep(5)

# kliknięcie myszką
pyautogui.click(500, 500)

# wpisanie szerokości
pyautogui.write("1111")

# przejście TAB dalej
pyautogui.press("tab")

# wpisanie wysokości
pyautogui.write("2222")

print("Gotowe")