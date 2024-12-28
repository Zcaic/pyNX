from pywinauto.application import Application

nx = Application(backend="uia").connect(title="NX - 建模")
mw = nx.top_window()
mw.type_keys("%{F8}")

script_window = mw.child_window(title="运行", class_name="Button").wait("visible",10)
# script_window.click_input()
script_window.type_keys("{ENTER}")