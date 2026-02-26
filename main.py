import os
import sys
import threading
import traceback
from datetime import datetime

from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog

class BluetoothDebugger(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.95, 0.95, 0.95, 1]
        self.selected_mac = None
        self.selected_name = "None"
        
        layout = MDBoxLayout(orientation='vertical', spacing=dp(5))
        
        # Header
        layout.add_widget(MDTopAppBar(title="Bluetooth Debugger"))
        
        # Controls
        controls = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(10), spacing=dp(10))
        self.btn_device = MDFillRoundFlatButton(text="Select Printer", on_release=self.scan_devices)
        controls.add_widget(self.btn_device)
        self.lbl_device = MDLabel(text="No device selected", theme_text_color="Secondary")
        controls.add_widget(self.lbl_device)
        layout.add_widget(controls)
        
        # Test Buttons
        btns1 = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(10), spacing=dp(10))
        btns1.add_widget(MDRaisedButton(text="Test JNI (UUID)", on_release=self.test_jni_uuid, md_bg_color=[0.8, 0.3, 0.2, 1]))
        btns1.add_widget(MDRaisedButton(text="Test JNI (Reflect)", on_release=self.test_jni_reflect, md_bg_color=[0.2, 0.6, 0.8, 1]))
        layout.add_widget(btns1)
        
        btns2 = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(10), spacing=dp(10))
        btns2.add_widget(MDRaisedButton(text="Test Python Socket", on_release=self.test_python_socket, md_bg_color=[0.2, 0.8, 0.2, 1]))
        btns2.add_widget(MDRaisedButton(text="Clear Log", on_release=self.clear_log, md_bg_color=[0.5, 0.5, 0.5, 1]))
        layout.add_widget(btns2)
        
        # Logger Console
        scroll = MDScrollView()
        self.log_console = MDLabel(text="=== Debug Log ===\n", size_hint_y=None, font_style="Caption", markup=True)
        self.log_console.bind(texture_size=self.log_console.setter('size'))
        scroll.add_widget(self.log_console)
        
        box = MDBoxLayout(padding=dp(10))
        box.add_widget(scroll)
        layout.add_widget(box)
        
        self.add_widget(layout)
        self.log("App Started.")
        self.request_perms()

    def log(self, text, color="000000"):
        def _add(*a):
            now = datetime.now().strftime("%H:%M:%S")
            self.log_console.text += f"\n[color=#{color}][{now}] {text}[/color]"
        Clock.schedule_once(_add, 0)
        print(f"[DEBUG] {text}")

    def clear_log(self, *args):
        self.log_console.text = "=== Debug Log ===\n"

    def request_perms(self):
        try:
            from android.permissions import request_permissions, check_permission, Permission
            perms = [Permission.BLUETOOTH_CONNECT, Permission.BLUETOOTH_SCAN, Permission.ACCESS_FINE_LOCATION]
            request_permissions(perms, lambda p, g: self.log(f"Perms: {g}", "0000FF"))
        except ImportError:
            self.log("Not on Android, skipping perms")

    def scan_devices(self, *args):
        self.log("Scanning paired devices...")
        devices = []
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter:
                self.log("No BT adapter found!", "FF0000")
                return
            if not adapter.isEnabled():
                self.log("BT is OFF!", "FF0000")
                return
            for d in adapter.getBondedDevices().toArray():
                devices.append({'name': d.getName(), 'mac': d.getAddress()})
                self.log(f"Found: {d.getName()} ({d.getAddress()})", "008800")
        except Exception as e:
            self.log(f"Scan error: {traceback.format_exc()}", "FF0000")
            return

        if not devices:
            self.log("No paired devices.", "FF0000")
            return

        content = MDList()
        dlg_ref = []
        def pick(mac, name):
            self.selected_mac = mac
            self.selected_name = name
            self.lbl_device.text = f"{name} ({mac})"
            self.log(f"Selected: {name}")
            dlg_ref[0].dismiss()

        for dev in devices:
            item = OneLineListItem(text=f"{dev['name']} ({dev['mac']})")
            item.bind(on_release=lambda x, m=dev['mac'], n=dev['name']: pick(m, n))
            content.add_widget(item)

        dlg = MDDialog(title="Select Paired Printer", type="custom", content_cls=content)
        dlg_ref.append(dlg)
        dlg.open()

    def run_test_bg(self, test_func, test_name):
        if not self.selected_mac:
            self.log("❌ Please select a printer first!", "FF0000")
            return
        self.log(f"\n--- Starting {test_name} ---", "0000FF")
        
        def bg_thread():
            try:
                test_func()
                self.log(f"✅ {test_name} SUCCESS!", "00AA00")
            except Exception as e:
                self.log(f"❌ {test_name} FAILED:\n{traceback.format_exc()}", "FF0000")
                
        threading.Thread(target=bg_thread, daemon=True).start()

    # --- TEST 1: JNI UUID ---
    def test_jni_uuid(self, *args):
        self.run_test_bg(self._run_jni_uuid, "JNI_UUID")
        
    def _run_jni_uuid(self):
        from jnius import autoclass
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        UUID = autoclass('java.util.UUID')
        adapter = BluetoothAdapter.getDefaultAdapter()
        adapter.cancelDiscovery()
        self.log("Discovery canceled. Getting remote device...")
        device = adapter.getRemoteDevice(self.selected_mac)
        serial_uuid = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb")
        
        self.log(f"Creating Socket with UUID {serial_uuid.toString()}...")
        bt_socket = device.createInsecureRfcommSocketToServiceRecord(serial_uuid)
        self.log("Calling connect()... (May crash here)")
        bt_socket.connect()
        self.log("Connected! Writing test bytes...")
        out = bt_socket.getOutputStream()
        out.write(10) # newline
        out.write(bytearray("JNI UUID TEST OK\n\n\n".encode('utf-8')))
        out.flush()
        bt_socket.close()

    # --- TEST 2: JNI Reflection ---
    def test_jni_reflect(self, *args):
        self.run_test_bg(self._run_jni_reflect, "JNI_REFLECTION")

    def _run_jni_reflect(self):
        from jnius import autoclass
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        adapter = BluetoothAdapter.getDefaultAdapter()
        adapter.cancelDiscovery()
        self.log("Discovery canceled. Getting remote device...")
        device = adapter.getRemoteDevice(self.selected_mac)
        
        self.log("Using reflection createRfcommSocket(1)...")
        clazz = device.getClass()
        IntegerType = autoclass('java.lang.Integer')
        method = clazz.getMethod('createRfcommSocket', IntegerType.TYPE)
        bt_socket = method.invoke(device, 1)
        
        self.log("Calling connect()... (May crash here)")
        bt_socket.connect()
        self.log("Connected! Writing test bytes...")
        out = bt_socket.getOutputStream()
        out.write(10)
        out.write(bytearray("JNI REFLECT TEST OK\n\n\n".encode('utf-8')))
        out.flush()
        bt_socket.close()

    # --- TEST 3: Python Built-in Socket ---
    def test_python_socket(self, *args):
        self.run_test_bg(self._run_python_socket, "PYTHON_SOCKET")

    def _run_python_socket(self):
        import socket
        mac = self.selected_mac
        self.log("Creating AF_BLUETOOTH socket...")
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.log("Calling connect()...")
        s.settimeout(10)
        s.connect((mac, 1))
        self.log("Connected! Writing test bytes...")
        s.send(b"\nPYTHON SOCKET TEST OK\n\n\n")
        s.close()

class Bin888App(MDApp):
    def build(self):
        return BluetoothDebugger()

if __name__ == '__main__':
    Bin888App().run()
