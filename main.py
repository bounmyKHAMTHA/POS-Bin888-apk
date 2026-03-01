import os
import json
import requests
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import OneLineListItem, MDList, IRightBodyTouch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.core.text import LabelBase
from datetime import datetime
from kivy.uix.spinner import Spinner

# Multi-language Font Support (Lao, Thai, English)
import os
from kivy.core.text import LabelBase

# Multi-language Font Support (Lao, Thai, English)
import os
from kivy.core.text import LabelBase

# ลำดับความสำคัญของฟอนต์ (เน้นตัวที่อ่านภาษาลาวออกชัวร์ๆ ก่อน)
font_options = [
    "Lao.ttf",
    "NotoSans-Regular.ttf"
]

font_path = None
for f in font_options:
    p = os.path.join(os.path.dirname(__file__), f)
    # เช็คว่าไฟล์มีอยู่จริงและมีขนาดมากกว่า 1KB (ป้องกันไฟล์เสีย)
    if os.path.exists(p) and os.path.getsize(p) > 1024:
        font_path = p
        break

if font_path:
    # ลงทะเบียนชื่อ "LaoFont" ให้แอปใช้งาน
    LabelBase.register(name="LaoFont", fn_regular=font_path)
    
    # ตั้งค่าให้ Kivy ใช้ตัวนี้เป็นค่าเริ่มต้น
    from kivy.config import Config
    Config.set('kivy', 'default_font', ['LaoFont', font_path])
    print(f"✓ Using font: {os.path.basename(font_path)}")
else:
    print("Warning: No valid fonts found. Please ensure Lao.ttf exists.")

# Set window size for desktop testing (handy for mobile layout)
# Window.size = (360, 640)

class PrinterManager:
    """Helper class to handle Bluetooth printing logic for Android"""
    def __init__(self):
        self.is_connected = False
        self._device = None
        self._socket = None

    def print_receipt(self, shop_name, items, total_lak, total_thb=0, total_bonus=0, rate=0):
        print(f"Printing to Bluetooth: {shop_name}")
        
        from kivy.utils import platform
        if platform != 'android':
            print("Fallback for desktop: print to terminal")
            print(f"--- {shop_name} ---")
            if rate: print(f"Rate: {rate:,.0f}")
            for item in items:
                name = item.get('name') or item.get('bin_name') or "Item"
                p_lak = item.get('price_lak') or item.get('sale_price_lak') or 0
                p_thb = item.get('price_thb') or item.get('sale_price_thb') or 0
                print(f"{name} - {p_lak:,} LAK ({p_thb:,.2f} THB)")
            print(f"TOTAL THB: {total_thb:,.2f}")
            print(f"TOTAL BONUS: {total_bonus:,.2f}")
            print(f"TOTAL LAK: {total_lak:,.0f}")
            print("-------------------")
            return

        try:
            from jnius import autoclass
            # Android Bluetooth API
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            UUID = autoclass('java.util.UUID')
            
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter: return
            if not adapter.isEnabled(): return

            SERIAL_UUID = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb")
            paired_devices = adapter.getBondedDevices().toArray()
            target_device = None
            for device in paired_devices:
                if "Printer" in device.getName() or "MPT" in device.getName():
                    target_device = device
                    break
            
            if not target_device and paired_devices: target_device = paired_devices[0]
            if not target_device: return

            socket = target_device.createRfcommSocketToServiceRecord(SERIAL_UUID)
            socket.connect()
            ostream = socket.getOutputStream()

            # Initialize
            ostream.write(bytes([0x1B, 0x40]))
            # Center Align
            ostream.write(bytes([0x1B, 0x61, 0x01]))
            # Bold On
            ostream.write(bytes([0x1B, 0x45, 0x01]))
            ostream.write(f"{shop_name}\n\n".encode('utf-8'))
            # Bold Off
            ostream.write(bytes([0x1B, 0x45, 0x00]))
            
            if rate:
                ostream.write(f"Rate: {rate:,.0f}\n".encode('utf-8'))
            
            # Left Align
            ostream.write(bytes([0x1B, 0x61, 0x00]))
            
            for item in items:
                p_lak = item.get('price_lak') or item.get('sale_price_lak') or 0
                p_thb = item.get('price_thb') or item.get('sale_price_thb') or 0
                name = item.get('name') or item.get('bin_name') or "Item"
                line = f"{name}\n{p_lak:,.0f} LAK ({p_thb:,.2f} THB)\n"
                ostream.write(line.encode('utf-8'))
            
            ostream.write(f"\nTOTAL THB: {total_thb:,.2f}\n".encode('utf-8'))
            ostream.write(f"TOTAL BONUS: {total_bonus:,.2f}\n".encode('utf-8'))
            ostream.write(f"TOTAL LAK: {total_lak:,.0f}\n".encode('utf-8'))
            ostream.write(b"\n\n\n\n")
            
            ostream.flush()
            socket.close()
        except Exception as e:
            print(f"Printer Error: {str(e)}")

from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.properties import NumericProperty
import threading
from kivy.clock import Clock

class SpinningLogo(Image):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = Animation(angle=360, duration=1.0)
        self.anim += Animation(angle=360, duration=1.0) # Allows infinite looping
        self.anim.repeat = True

    def start(self):
        self.angle = 0
        self.anim.start(self)
        
    def stop(self):
        self.anim.stop(self)

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1] # Ensure Solid White Background
        layout = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Header Area
        header = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(10))
        header.add_widget(MDLabel(
            text="Login ເຂົ້າສຸລະບົບ ຂາຍເຄື່ອງອອນລາຍ",
            halign="center",
            font_style="H5",
            theme_text_color="Primary",
            font_name="LaoFont" if os.path.exists(font_path) else None
        ))
        layout.add_widget(header)
        
        # Spinner
        from kivy.lang import Builder
        Builder.load_string('''
<SpinningLogo>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.angle
            origin: self.center
    canvas.after:
        PopMatrix
''')
        self.spinner = SpinningLogo(source='app_icon.png', size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={'center_x': .5})
        self.spinner.opacity = 0
        layout.add_widget(self.spinner)

        # Form Area
        content = MDBoxLayout(orientation='vertical', spacing=dp(15))
        
        self.user_field = MDTextField(
            hint_text="Username",
            icon_right="account",
            mode="fill"
        )
        self.pass_field = MDTextField(
            hint_text="Password",
            icon_right="key",
            password=True,
            mode="fill"
        )
        
        content.add_widget(self.user_field)
        content.add_widget(self.pass_field)
        
        self.login_btn = MDFillRoundFlatButton(
            text="Login ເຂົ້າສຸລະບົບ",
            font_style="Subtitle1",
            font_name="LaoFont" if os.path.exists(font_path) else None,
            font_size="18sp",
            pos_hint={"center_x": .5},
            size_hint_x=0.8,
            on_release=self.perform_login
        )
        content.add_widget(self.login_btn)
        
        layout.add_widget(content)
        layout.add_widget(MDBoxLayout()) # Spacer
        
        self.add_widget(layout)

    def perform_login(self, *args):
        app = MDApp.get_running_app()
        base_url = app.base_url
        username = self.user_field.text
        password = self.pass_field.text
        
        if not username or not password:
            self.user_field.error = True
            return

        self.login_btn.disabled = True
        self.login_btn.opacity = 0
        self.spinner.opacity = 1
        self.spinner.start()
        
        threading.Thread(target=self._do_login_thread, args=(base_url, username, password), daemon=True).start()

    def _do_login_thread(self, base_url, username, password):
        try:
            app = MDApp.get_running_app()
            headers = {
                'X-App-Access-Key': app.APP_KEY,
                'X-App-Version': app.APP_VERSION
            }
            response = requests.post(
                f"{base_url}/api/v1/login/",
                data={"username": username, "password": password},
                headers=headers,
                timeout=10
            )
            Clock.schedule_once(lambda dt: self._handle_login_result(response, base_url))
        except Exception as e:
            print("Error connecting to server:", str(e))
            Clock.schedule_once(lambda dt: self._reset_login_ui("SERVER ERROR"))

    def _handle_login_result(self, response, base_url):
        self.spinner.stop()
        self.spinner.opacity = 0
        self.login_btn.disabled = False
        self.login_btn.opacity = 1
        
        if response.status_code == 200:
            data = response.json()
            MDApp.get_running_app().config_data = data
            MDApp.get_running_app().base_url = base_url
            MDApp.get_running_app().save_config() # Save for hot reload
            threading.Thread(target=MDApp.get_running_app().fetch_brands, daemon=True).start()
            self.manager.current = 'dashboard'
        elif response.status_code == 403 and "APP_UPDATE_REQUIRED" in response.text:
            self.login_btn.text = "UPDATE REQUIRED"
            MDApp.get_running_app().show_update_dialog()
        else:
            print("Login Failed:", response.text)
            self.login_btn.text = "LOGIN FAILED - RETRY"
            
    def _reset_login_ui(self, msg):
        self.spinner.stop()
        self.spinner.opacity = 0
        self.login_btn.disabled = False
        self.login_btn.opacity = 1
        self.login_btn.text = msg

# VoucherItemCard has been removed in favor of direct Image Rendering

class VoucherScreen(MDScreen):
    def setup_voucher(self, shop_name, items, sale_id, totals, received=0, exchange_rate=650.0, **kwargs):
        app = MDApp.get_running_app()
        from datetime import datetime
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        lak_total = float(totals.get('lak', 0))
        received = float(received)
        change = received - lak_total if received > lak_total else 0

        # Save receipt data for printing
        self._print_shop_name = shop_name
        self._print_items = items
        self._print_total_lak = lak_total
        self._print_total_thb = totals['thb']
        self._print_total_bonus = totals.get('bonus', 0)
        self._print_received = received
        self._print_change = change
        self._print_sale_id = sale_id
        self._print_date = now_str
        
        # Phone logic
        config = app.config_data
        phone = config.get('phone_number', '977 18 595')
        self._print_phone = phone
        
        # Rate logic
        actual_rate = exchange_rate
        if items and 'lad' in items[0]:
            actual_rate = items[0]['lad']
        self._print_exchange_rate = float(actual_rate)
        
        import os, tempfile
        from kivy.clock import Clock
        from kivy.uix.image import Image as KivyImage

        # Show loading label immediately so screen appears before the slow render
        self.preview_container.clear_widgets()
        self.preview_container.add_widget(MDLabel(
            text="ກຳລັງສ້າງໃບບິນ...",
            halign="center",
            size_hint_y=None,
            height=dp(60)
        ))
        self._cached_receipt_img = None  # reset cache

        # Schedule image generation on next frame (after UI shows loading)
        # KivyLabel MUST run on main thread — Clock keeps it there
        def _generate(dt):
            try:
                img = self.generate_receipt_image(
                    shop_name=self._print_shop_name,
                    items=self._print_items,
                    total_lak=self._print_total_lak,
                    pt_thb=self._print_total_thb,
                    pt_bonus=self._print_total_bonus,
                    pt_rec=self._print_received,
                    pt_chg=self._print_change,
                    pt_sid=self._print_sale_id,
                    pt_date=self._print_date,
                    pt_phone=self._print_phone,
                    pt_rate=self._print_exchange_rate
                )
                self._cached_receipt_img = img
                preview_path = os.path.join(tempfile.gettempdir(), "receipt_preview.png")
                img.save(preview_path)
                self.preview_container.clear_widgets()
                self.preview_container.add_widget(KivyImage(
                    source=preview_path,
                    allow_stretch=True,
                    keep_ratio=True,
                    size_hint_y=None,
                    height=dp(min(img.height // 1.5, 1200))
                ))
            except Exception as e:
                print(f"Receipt render error: {e}")

        Clock.schedule_once(_generate, 0.1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1] # Ensure Solid White Background
        layout = MDBoxLayout(orientation="vertical")
        
        # Toolbar
        layout.add_widget(MDTopAppBar(
            title="Receipt Preview",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["printer", lambda x: self.print_action()]]
        ))
        
        scroll = MDScrollView(do_scroll_x=False)
        content = MDBoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        # Preview Container
        self.preview_container = MDBoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        self.preview_container.bind(minimum_height=self.preview_container.setter('height'))
        content.add_widget(self.preview_container)
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        
        # Bottom Buttons (Cleaned up from testing)
        btns = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(10), spacing=dp(10))
        done_btn = MDFillRoundFlatButton(text="ສຳເລັດ", size_hint_x=0.4, on_release=self.go_back)
        if os.path.exists(font_path): done_btn.font_name = "LaoFont"
        btns.add_widget(done_btn)
        
        print_btn = MDFillRoundFlatButton(text="ພິມໃບບິນ", size_hint_x=0.6, md_bg_color=[0, 0.5, 1, 1], on_release=self.print_action)
        if os.path.exists(font_path): print_btn.font_name = "LaoFont"
        btns.add_widget(print_btn)
        
        layout.add_widget(btns)
        
        self.add_widget(layout)

    def go_back(self, *args):
        self.manager.current = 'dashboard'

    def scan_and_pick_printer(self, *args):
        """List paired BT devices, let user pick, then print via JNI UUID"""
        from kivy.utils import platform
        if platform != 'android':
            Snackbar(MDLabel(text="Bluetooth printing is only supported on Android devices.", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return
            
        devices = []
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter and adapter.isEnabled():
                for d in adapter.getBondedDevices().toArray():
                    devices.append({'name': d.getName(), 'mac': d.getAddress()})
        except Exception as e:
            Snackbar(MDLabel(text=f"BT scan error: {str(e)[:50]}", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return

        if not devices:
            Snackbar(MDLabel(text="No paired BT devices. Please pair your POS printer in Android Settings.", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return

        # Show picker dialog
        from kivymd.uix.list import MDList
        content = MDList()
        dialog_ref = []
        def pick(mac, name):
            if dialog_ref:
                dialog_ref[0].dismiss()
            app = MDApp.get_running_app()
            app.config_data['selected_printer_mac'] = mac
            app.config_data['selected_printer_name'] = name
            app.save_config()
            # Generate receipt image on main thread before BT background thread
            try:
                receipt_img = self.generate_receipt_image(
                    getattr(self, '_print_shop_name', 'Shop'),
                    getattr(self, '_print_items', []),
                    getattr(self, '_print_total_lak', 0),
                    getattr(self, '_print_total_thb', 0),
                    getattr(self, '_print_total_bonus', 0),
                    getattr(self, '_print_received', 0),
                    getattr(self, '_print_change', 0),
                    getattr(self, '_print_sale_id', '0000'),
                    getattr(self, '_print_date', ''),
                    getattr(self, '_print_phone', ''),
                    getattr(self, '_print_exchange_rate', 650.0),
                )
            except Exception as e:
                Snackbar(MDLabel(text=f"Receipt gen error: {str(e)[:40]}", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
                return
            self._print_via_socket(mac, name, receipt_img=receipt_img)
        for dev in devices:
            item = OneLineListItem(text=f"{dev['name']} ({dev['mac']})")
            item.bind(on_release=lambda x, m=dev['mac'], n=dev['name']: pick(m, n))
            content.add_widget(item)

        dlg = MDDialog(
            title="Select Printer",
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="CANCEL", on_release=lambda x: dialog_ref[0].dismiss())]
        )
        dialog_ref.append(dlg)
        dlg.open()

    def generate_receipt_image(self, shop_name, items, total_lak, pt_thb, pt_bonus, pt_rec, pt_chg, pt_sid, pt_date, pt_phone, pt_rate):
        from PIL import Image, ImageDraw
        global font_path
        
        img_w = 384
        # FIX: Make initial canvas huge and use 255 (white) to prevent black boxes
        height = 4000 
        img = Image.new('1', (img_w, height), 255) 
        draw = ImageDraw.Draw(img)
        
        def render_lao_text_to_pil(text, font_size):
            try:
                from kivy.core.text import Label as KivyLabel
                from PIL import Image as PILImage
                import os
                
                font_name = "Roboto"
                global font_path 
                
                if font_path and os.path.exists(font_path):
                    font_name = "LaoFont"
                    
                lbl = KivyLabel(text=str(text), font_name=font_name, font_size=font_size, color=(0,0,0,1))
                lbl.refresh()
                if not lbl.texture: return None
                    
                tex = lbl.texture
                img_tex = PILImage.frombytes('RGBA', tex.size, tex.pixels)
                
                bg = PILImage.new('RGBA', img_tex.size, (255, 255, 255, 255))
                bg.paste(img_tex, (0, 0), img_tex) 
                return bg.convert('1')
            except Exception as e:
                print(f"Lao render error: {e}")
                return None

        def draw_center(text, y_pos, font_size):
            pil_txt = render_lao_text_to_pil(text, font_size)
            if pil_txt:
                tw, th = pil_txt.size
                img.paste(pil_txt, ((img_w - tw) // 2, y_pos))
                return y_pos + th + 1
            return y_pos + 15

        def draw_row(label, value, y_pos, font_size):
            pil_lbl = render_lao_text_to_pil(label, font_size)
            pil_val = render_lao_text_to_pil(value, font_size)
            th = 0
            if pil_lbl:
                img.paste(pil_lbl, (10, y_pos))
                th = max(th, pil_lbl.size[1])
            if pil_val:
                tw, vh = pil_val.size
                img.paste(pil_val, (img_w - 10 - tw, y_pos))
                th = max(th, vh)
            return y_pos + th + 1

        y = 2
        
        # 1. Header (Shop, Phone)
        y = draw_center(shop_name, y, 26)
        y = draw_center(f"Phone: {pt_phone}", y, 22)
        y += 2
        
        # 2. Items
        draw.line((10, y, img_w-10, y), fill=0, width=1)
        y += 4
        
        for item in items:
            item_lad = float(item.get('lad', pt_rate))
            y = draw_center(f"ID: #{pt_sid} | {pt_date} | ເລດ: {item_lad:,.0f}", y, 20)
            
            base_brand_label = "GIFT CARD"
            app = MDApp.get_running_app()
            matched_brand = None
            if hasattr(app, 'brands_cache') and app.brands_cache:
                import random
                matched_brand = random.choice(app.brands_cache)
            if matched_brand:
                base_brand_label = matched_brand['name'].upper()

            y = draw_center(base_brand_label, y, 24)
            y = draw_center(item['name'], y, 28)
            
            price_lak = float(item['price_lak'])
            price_thb = float(item['price_thb'])
            price_bonus = float(item.get('price_bonus', 0))
            
            bonus_text = f" + ໂບນັດ {price_bonus:,.2f} THB" if price_bonus > 0 else ""
            sub_text = f"{price_lak:,.0f} ກີບ / {price_thb:,.2f} THB{bonus_text}"
            y = draw_center(sub_text, y, 20) + 2
            
            # PIN Outline Box
            y = draw_center("PIN CODE / REDEEM CODE", y, 20) + 2
            pw_str = str(item.get('pw', 'N/A'))
            
            pil_pw = render_lao_text_to_pil(pw_str, 34)
            if pil_pw:
                tw, th = pil_pw.size
                bx = (img_w - tw) // 2 - 8
                by = y
                bw = tw + 16
                bh = th + 6
                draw.rectangle([bx, by, bx+bw, by+bh], outline=0, width=2)
                img.paste(pil_pw, ((img_w - tw) // 2, y + 3))
                y += bh + 4
            else:
                y += 20
            
            # Bottom Demarcation
            draw.line((10, y, img_w-10, y), fill=0, width=1)
            y += 4
        
        # 3. Summary
        y = draw_row("Total LAK:", f"{total_lak:,.0f} LAK", y, 20)
        y = draw_row("Total THB:", f"{pt_thb:,.2f} THB", y, 20)
        if pt_bonus > 0:
            y = draw_row("Total Bonus:", f"+ {pt_bonus:,.2f} THB", y, 20)
        
        y += 2
        draw.line((10, y, img_w-10, y), fill=0, width=1)
        y += 2
        
        y = draw_row("Received:", f"{pt_rec:,.0f} LAK", y, 20)
        y = draw_row("Change:", f"{pt_chg:,.0f} LAK", y, 20) + 4
        
        # 4. Footer
        footer1 = "*** ທຸກບິນທີ່ຂາຍໄປຢູ່ໄດ້ບໍ່ເກີນ 3 ວັນຈະໝົດອາຍຸ"
        footer2 = "ຫາກໝົດອາຍຸແລ້ວຕິດຕໍ່ຮ້ານຄ້າເພື່ອແກ້ໄຂ ***"
        footer3 = "ຂອບໃຈທີ່ໃຊ້ບໍລິການ / Thank You!"
        
        y = draw_center(footer1, y, 18)
        y = draw_center(footer2, y, 18) + 2
        y = draw_center(footer3, y, 18)
        
        # Minimal tear padding (1 line worth)
        y += 10 
        
        img = img.crop((0, 0, img_w, y))
        return img

    def _print_via_socket(self, mac, name, receipt_img=None):
        """Connect and print via BT. receipt_img must be pre-generated on main thread."""
        import threading
        from kivy.clock import Clock
        
        if receipt_img is None:
            Snackbar(MDLabel(text="Error: receipt image not ready", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return
        
        Snackbar(MDLabel(text=f"Connecting to {name}...", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
        
        def run():
            bt_socket = None
            try:
                from jnius import autoclass
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                UUID = autoclass('java.util.UUID')
                
                adapter = BluetoothAdapter.getDefaultAdapter()
                # FIX: Prevent crash if cancelDiscovery fails on Android 12+
                try:
                    adapter.cancelDiscovery()  
                except Exception as e:
                    print(f"cancelDiscovery error (ignoring): {e}")
                
                # FIX: Give printer more time to stabilize
                import time
                time.sleep(1.0)

                device = adapter.getRemoteDevice(mac)
                serial_uuid = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb")
                
                # ==========================================
                # 🚀 LOGIC การเชื่อมต่อ 3 ระดับ (ปราบเครื่องพิมพ์ดื้อ)
                # ==========================================
                connected = False
                
                # ลองแบบที่ 1: Insecure Connection
                try:
                    bt_socket = device.createInsecureRfcommSocketToServiceRecord(serial_uuid)
                    bt_socket.connect()
                    connected = True
                except Exception as e1:
                    print(f"Insecure connect failed: {e1}")
                    # ลองแบบที่ 2: Secure Connection
                    try:
                        bt_socket = device.createRfcommSocketToServiceRecord(serial_uuid)
                        bt_socket.connect()
                        connected = True
                    except Exception as e2:
                        print(f"Secure connect failed: {e2}")
                        # ลองแบบที่ 3: บังคับเชื่อมต่อ Port 1 (ทะลวงกำแพง JVM Exception)
                        try:
                            j_int = autoclass('java.lang.Integer').TYPE
                            method = device.getClass().getMethod("createRfcommSocket", j_int)
                            bt_socket = method.invoke(device, 1)
                            bt_socket.connect()
                            connected = True
                        except Exception as e3:
                            print(f"Reflection connect failed: {e3}")
                
                if not connected:
                    raise Exception("ไม่สามารถເຊື່ອມຕໍ່ໄດ້ (Printer might be off or busy)")

                ostream = bt_socket.getOutputStream()
                
                # ========================================
                # 1. USE PRE-GENERATED RECEIPT IMAGE
                # ========================================
                img = receipt_img

                # ========================================
                # 2. CONVERT PILLOW IMAGE TO ESC/POS RASTER IN SLICES
                # ========================================
                w, h = img.size
                pad_w = ((w + 7) // 8) * 8
                if pad_w != w:
                    new_img = Image.new('1', (pad_w, h), 255) # FIXED: 255 is white
                    new_img.paste(img, (0,0))
                    img = new_img
                    w = pad_w
                    
                init_cmd = bytearray([0x1B, 0x40]) # Init
                try:
                    ostream.write(bytes(init_cmd))
                except Exception:
                    for b in init_cmd: ostream.write(b)
                ostream.flush()
                time.sleep(0.1)

                slice_height = 200
                pixels = img.load()
                
                for start_y in range(0, h, slice_height):
                    cur_h = min(slice_height, h - start_y)
                    
                    xL = (w // 8) % 256
                    xH = (w // 8) // 256
                    yL = cur_h % 256
                    yH = cur_h // 256
                    
                    receipt = bytearray()
                    receipt.extend([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
                    
                    for py in range(start_y, start_y + cur_h):
                        for px_byte in range(w // 8):
                            byte_val = 0
                            for bit in range(8):
                                idx = px_byte * 8 + bit
                                # White background (1) -> bit 0, Black pixel (0) -> bit 1
                                if pixels[idx, py] == 0:
                                    byte_val |= (1 << (7 - bit))
                            receipt.append(byte_val)
                    
                    # Write slice to stream
                    try:
                        ostream.write(bytes(receipt))
                    except Exception:
                        for b in receipt: ostream.write(b)
                    ostream.flush()
                    time.sleep(0.05) # Reduced delay for faster printing

                # Feed 4 lines at the end for easy tearing
                feed_cmd = bytearray([0x0A, 0x0A, 0x0A, 0x0A])
                try:
                    ostream.write(bytes(feed_cmd))
                except Exception:
                    for b in feed_cmd: ostream.write(b)
                ostream.flush()
                bt_socket.close()
                
                Clock.schedule_once(lambda dt: Snackbar(MDLabel(text="\u2713 ພິມສຳເລັດ! (Print OK)", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open(), 0)
            except Exception as e:
                err = str(e)
                if bt_socket:
                    try: bt_socket.close()
                    except: pass
                Clock.schedule_once(lambda dt, m=f"BT Printer Error: {err[:60]}": Snackbar(MDLabel(text=m, theme_text_color="Custom", text_color=[1, 1, 1, 1])).open(), 0)
                
        threading.Thread(target=run, daemon=True).start()

    def print_action(self, *args):
        """Handle print button - ALWAYS check permissions first, then connect or scan."""
        from kivy.utils import platform
        if platform != 'android':
            Snackbar(MDLabel(text="Bluetooth printing is only supported on Android", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return
        
        # Always go through permission check - whether connecting saved or scanning
        self._check_bt_permissions_then(self._connect_saved_or_scan)

    def _connect_saved_or_scan(self):
        """Called after permissions confirmed. Generates receipt image on main thread, then sends to BT."""
        app = MDApp.get_running_app()
        saved_mac = app.config_data.get('selected_printer_mac')
        saved_name = app.config_data.get('selected_printer_name', 'Printer')
        
        if saved_mac:
            # CRITICAL: Generate the receipt image HERE on the main thread
            # (KivyLabel rendering requires OpenGL context = main thread only)
            try:
                shop_name = getattr(self, '_print_shop_name', 'Shop')
                items = getattr(self, '_print_items', [])
                total_lak = getattr(self, '_print_total_lak', 0)
                pt_thb = getattr(self, '_print_total_thb', 0)
                pt_bonus = getattr(self, '_print_total_bonus', 0)
                pt_rec = getattr(self, '_print_received', 0)
                pt_chg = getattr(self, '_print_change', 0)
                pt_sid = getattr(self, '_print_sale_id', '0000')
                pt_date = getattr(self, '_print_date', '')
                pt_phone = getattr(self, '_print_phone', '')
                pt_rate = getattr(self, '_print_exchange_rate', 650.0)
                receipt_img = self.generate_receipt_image(
                    shop_name, items, total_lak, pt_thb, pt_bonus, pt_rec, pt_chg, pt_sid, pt_date, pt_phone, pt_rate
                )
            except Exception as e:
                Snackbar(MDLabel(text=f"Receipt gen error: {str(e)[:40]}", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
                return
            # Now pass the pre-generated image to the background print thread
            self._print_via_socket(saved_mac, saved_name, receipt_img=receipt_img)
        else:
            self.scan_and_pick_printer()

    def _check_bt_permissions_then(self, callback):
        """Check/request Bluetooth permissions, then call callback when granted."""
        try:
            from android.permissions import request_permissions, check_permission
            from jnius import autoclass
            Build = autoclass('android.os.Build$VERSION')
            
            if Build.SDK_INT >= 31:
                perms = ['android.permission.BLUETOOTH_CONNECT', 'android.permission.BLUETOOTH_SCAN']
            else:
                perms = ['android.permission.BLUETOOTH', 'android.permission.ACCESS_FINE_LOCATION', 'android.permission.ACCESS_COARSE_LOCATION']
            
            needs_request = any(not check_permission(p) for p in perms)
            
            if needs_request:
                def on_result(permissions, grants):
                    from kivy.clock import Clock
                    if all(grants):
                        Clock.schedule_once(lambda dt: callback(), 1.0)
                    else:
                        from kivymd.app import MDApp as App
                        Clock.schedule_once(lambda dt: App.get_running_app().show_error_dialog("Bluetooth permission denied."), 0.5)
                request_permissions(perms, on_result)
                return
        except Exception as e:
            print(f"Permission check error: {e}")
        
        # Permissions already granted (or non-android fallback)
        callback()

    def request_bt_permissions_and_scan(self):
        from kivy.utils import platform
        if platform != 'android':
            self.scan_and_pick_printer()
            return

        try:
            from android.permissions import request_permissions, check_permission
            from jnius import autoclass
            Build = autoclass('android.os.Build$VERSION')
            
            if Build.SDK_INT >= 31:
                perms = ['android.permission.BLUETOOTH_CONNECT', 'android.permission.BLUETOOTH_SCAN']
            else:
                perms = ['android.permission.BLUETOOTH', 'android.permission.ACCESS_FINE_LOCATION', 'android.permission.ACCESS_COARSE_LOCATION']
                
            needs_request = False
            for p in perms:
                if not check_permission(p):
                    needs_request = True
                    break
                    
            if needs_request:
                def on_permission_result(permissions, grants):
                    from kivy.clock import Clock
                    if all(grants):
                        # หน่วงเวลา 1 วินาที เพื่อให้กราฟิกแอปฟื้นตัว ป้องกันแอปเด้ง!
                        Clock.schedule_once(lambda dt: self.scan_and_pick_printer(), 1.0)
                    else:
                        from kivymd.app import MDApp
                        Clock.schedule_once(lambda dt: MDApp.get_running_app().show_error_dialog("Bluetooth permission denied."), 0.5)
                
                request_permissions(perms, on_permission_result)
                return
                
        except Exception as e:
            print(f"Permission Error: {e}")

        self.scan_and_pick_printer()

class BinGroupWidget(MDCard): # Change to MDCard for better grid look
    def __init__(self, price_lak, stock_count, on_qty_change, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(50) # Absolute minimum height
        self.padding = dp(2)
        self.spacing = dp(0)
        self.elevation = 1
        self.price_lak = price_lak
        self.stock_count = stock_count
        self.quantity = 0
        self.on_qty_change = on_qty_change

        # Format price as "XK ກີບ"
        display_price = f"{int(price_lak / 1000)}K ກີບ"

        # Top Row: Price and Stock
        top_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        self.price_label = MDLabel(
            text=display_price,
            font_style="Subtitle2", bold=True,
            halign="center", theme_text_color="Primary",
            valign="center",
            font_name="LaoFont" if font_path else None
        )
        self.stock_label = MDLabel(
            text=f"Stock: {stock_count}",
            font_style="Caption", halign="center",
            theme_text_color="Secondary",
            valign="center"
        )
        top_row.add_widget(self.price_label)
        top_row.add_widget(self.stock_label)
        self.add_widget(top_row)
        
        # Bottom Row: Quantity Controls
        controls = MDBoxLayout(spacing=dp(5), pos_hint={"center_x": .5}, adaptive_width=True, size_hint_y=None, height=dp(25))
        
        btn_minus = MDIconButton(
            icon="minus-circle", icon_size=dp(20),
            theme_text_color="Custom", text_color=(1, 0, 0, 1),
            on_release=self.decrease,
            pos_hint={'center_y': .5}
        )
        
        self.qty_label = MDLabel(
            text="0", halign="center", font_style="Body1", bold=True,
            width=dp(25), size_hint_x=None,
            valign="center"
        )
        
        btn_plus = MDIconButton(
            icon="plus-circle", icon_size=dp(20),
            theme_text_color="Custom", text_color=(0, 0.6, 0, 1),
            on_release=self.increase,
            pos_hint={'center_y': .5}
        )
        
        controls.add_widget(btn_minus)
        controls.add_widget(self.qty_label)
        controls.add_widget(btn_plus)
        
        self.add_widget(controls)

    def increase(self, *args):
        if self.quantity < self.stock_count:
            self.quantity += 1
            self.update_ui()

    def decrease(self, *args):
        if self.quantity > 0:
            self.quantity -= 1
            self.update_ui()

    def update_ui(self):
        self.qty_label.text = str(self.quantity)
        self.on_qty_change(self.price_lak, self.quantity)

    def reset(self):
        self.quantity = 0
        self.qty_label.text = "0"

class RecycleScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1]
        
        layout = MDBoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Recycle Hub",
            elevation=4,
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["refresh", lambda x: self.refresh_data()]]
        )
        layout.add_widget(self.toolbar)
        
        # Main Content
        content = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Stats Cards
        stats_layout = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(100))
        
        self.waiting_card = self.create_stat_card("Waiting", "0", "#FB8C00") # Orange
        self.success_card_label = MDLabel(text="0", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="H5")
        self.success_card = MDCard(
            orientation='vertical', padding=dp(5), spacing=dp(2), radius=dp(10), elevation=2, md_bg_color=get_color_from_hex("#43A047")
        )
        self.success_card.add_widget(MDLabel(text="Success", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="Caption"))
        self.success_card.add_widget(self.success_card_label)
        
        self.failed_card_label = MDLabel(text="0", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="H5")
        self.failed_card = MDCard(
            orientation='vertical', padding=dp(5), spacing=dp(2), radius=dp(10), elevation=2, md_bg_color=get_color_from_hex("#E53935")
        )
        self.failed_card.add_widget(MDLabel(text="Failed", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="Caption"))
        self.failed_card.add_widget(self.failed_card_label)
        
        self.waiting_card_label = MDLabel(text="0", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="H5")
        self.waiting_card = MDCard(
            orientation='vertical', padding=dp(5), spacing=dp(2), radius=dp(10), elevation=2, md_bg_color=get_color_from_hex("#FB8C00")
        )
        self.waiting_card.add_widget(MDLabel(text="Pending", halign="center", theme_text_color="Custom", text_color=(1, 1, 1, 1), font_style="Caption"))
        self.waiting_card.add_widget(self.waiting_card_label)

        stats_layout.add_widget(self.waiting_card)
        stats_layout.add_widget(self.success_card)
        stats_layout.add_widget(self.failed_card)
        content.add_widget(stats_layout)
        
        # Bot Status Banner
        self.status_banner = MDCard(
            size_hint_y=None, height=dp(50), padding=dp(10), radius=dp(8), elevation=1, md_bg_color=get_color_from_hex("#EEEEEE")
        )
        self.status_label = MDLabel(text="Bot Status: Idle", halign="center", font_style="Subtitle2")
        self.status_banner.add_widget(self.status_label)
        content.add_widget(self.status_banner)
        
        # --- Config Section ---
        config_card = MDCard(
            orientation='vertical', padding=dp(10), spacing=dp(5), 
            size_hint_y=None, height=dp(130), radius=dp(10), elevation=1,
            md_bg_color=get_color_from_hex("#F5F5F5")
        )
        
        # Price Filter
        config_card.add_widget(MDLabel(text="ເລືອກປະເພດບິນ (Amount LAK)", font_style="Caption", font_name="LaoFont" if os.path.exists(font_path) else None))
        
        from kivy.lang import Builder
        if not hasattr(self.__class__, '_lao_spinner_registered'):
            Builder.load_string('''
<LaoSpinnerOption@SpinnerOption>:
    font_name: "LaoFont"
    color: 0, 0, 0, 1
    background_normal: ''
    background_color: 0.95, 0.95, 0.95, 1
''')
            self.__class__._lao_spinner_registered = True
            
        self.price_spinner = Spinner(
            text='ທັງໝົດ / All',
            values=('ທັງໝົດ / All',),
            size_hint=(1, None),
            height=dp(40),
            background_normal='',
            background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1),
            font_name="LaoFont" if os.path.exists(font_path) else None,
            option_cls='LaoSpinnerOption' if os.path.exists(font_path) else 'SpinnerOption'
        )
        config_card.add_widget(self.price_spinner)
        
        config_card.add_widget(MDLabel(text="ຈຳນວນທີ່ຕ້ອງການເຮັດ (Max 100 ID)", font_style="Caption", font_name="LaoFont" if os.path.exists(font_path) else None))
        self.limit_field = MDTextField(
            text="100",
            mode="rectangle",
            size_hint_y=None, height=dp(35),
            input_filter="int"
        )
        config_card.add_widget(self.limit_field)
        
        content.add_widget(config_card)
        # ----------------------
        
        # Buttons
        btns = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        self.start_btn = MDFillRoundFlatButton(
            text="Start Auto-Recycle Bot", icon="play", md_bg_color=get_color_from_hex("#311B92"), on_release=self.start_bot
        )
        self.reset_btn = MDFlatButton(
            text="Reset & Clear Errors", theme_text_color="Error", on_release=self.reset_bot
        )
        btns.add_widget(self.start_btn)
        btns.add_widget(self.reset_btn)
        content.add_widget(btns)
        
        # Logs List Header
        content.add_widget(MDLabel(text="ລາຍການປະມວນຜົນລ້າສຸດ (Recent Logs)", font_style="Subtitle1", size_hint_y=None, height=dp(30), font_name="LaoFont" if os.path.exists(font_path) else None))
        
        # Logs List
        self.log_scroll = MDScrollView()
        self.log_list = MDList()
        self.log_scroll.add_widget(self.log_list)
        content.add_widget(self.log_scroll)
        
        layout.add_widget(content)
        self.add_widget(layout)
        self._init_loading_overlay()

    def _init_loading_overlay(self):
        from kivymd.uix.spinner import MDSpinner
        from kivy.uix.modalview import ModalView
        from kivy.uix.anchorlayout import AnchorLayout
        modal = ModalView(
            background_color=[1, 1, 1, 0.6],
            overlay_color=[0, 0, 0, 0],
            auto_dismiss=False,
            size_hint=(1, 1)
        )
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(MDSpinner(
            size_hint=(None, None), size=(dp(48), dp(48)),
            active=True
        ))
        modal.add_widget(anchor)
        self._loading_modal = modal

    def show_loading(self): self._loading_modal.open()
    def hide_loading(self):
        if self._loading_modal.parent:
            self._loading_modal.dismiss()

    def create_stat_card(self, title, value, color):
        # Helper to avoid repetitive code if needed, but I already wrote them above
        pass

    def on_enter(self):
        self.show_loading()
        self.refresh_data()

    def go_back(self):
        self.manager.current = 'dashboard_screen'

    def refresh_data(self):
        self.show_loading()
        threading.Thread(target=self._fetch_recycle_data, daemon=True).start()

    def _fetch_recycle_data(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {
            'Authorization': f'Token {token}',
            'X-App-Access-Key': app.APP_KEY,
            'X-App-Version': app.APP_VERSION
        }
        base_url = app.base_url
        
        try:
            # 1. Fetch Status
            status_resp = requests.get(f"{base_url}/api/v1/recycle-status/", headers=headers, timeout=10)
            if status_resp.status_code == 200:
                data = status_resp.json()
                Clock.schedule_once(lambda dt: self.update_status_ui(data))
            
            # 2. Fetch Logs
            logs_resp = requests.get(f"{base_url}/api/v1/recycle-logs/", headers=headers, timeout=10)
            if logs_resp.status_code == 200:
                logs_data = logs_resp.json().get('results', [])
                Clock.schedule_once(lambda dt: self.update_logs_ui(logs_data))
        except Exception as e:
            print(f"Recycle fetch error: {e}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def update_status_ui(self, data):
        self.waiting_card_label.text = str(data.get('waiting_count', 0))
        self.success_card_label.text = str(data.get('success_today', 0))
        self.failed_card_label.text = str(data.get('failed_today', 0))
        
        is_running = data.get('is_running', False)
        if is_running:
            self.status_label.text = "Bot Status: Running... (ກຳລັງເຮັດວຽກ)"
            self.status_banner.md_bg_color = get_color_from_hex("#E8F5E9")
            self.start_btn.disabled = True
        else:
            self.status_label.text = "Bot Status: Idle (ວ່າງ)"
            self.status_banner.md_bg_color = get_color_from_hex("#EEEEEE")
            self.start_btn.disabled = False
            
        # Update Price Spinner
        price_counts = data.get('price_counts', [])
        values = ['ທັງໝົດ / All']
        for item in price_counts:
            val = f"{item['price_lak']:,.0f} LAK ({item['count']} ບິນ)"
            values.append(val)
        
        if self.price_spinner.text not in values and self.price_spinner.text != 'ທັງໝົດ / All':
            self.price_spinner.text = 'ທັງໝົດ / All'
        self.price_spinner.values = values

    def update_logs_ui(self, logs):
        self.log_list.clear_widgets()
        from kivymd.uix.list import ThreeLineListItem
        for log in logs:
            status_icon = "✅" if log['status'] == 'success' else "❌"
            msg = log['error_message'] if log['error_message'] else (f"Refilled: {log['refilled_amount']}" if log['status'] == 'success' else "N/A")
            item = ThreeLineListItem(
                text=f"{status_icon} ID: {log['bin_name']}",
                secondary_text=f"Time: {log['processed_at'][:19].replace('T', ' ')}",
                tertiary_text=f"Price: {log['price_lak']} | {msg}",
            )
            self.log_list.add_widget(item)

    def start_bot(self, *args):
        # Read values from UI
        price_text = self.price_spinner.text
        price_id = "all"
        if "LAK" in price_text:
            # Extract number before LAK
            price_id = price_text.split(" ")[0].replace(",", "")
            
        limit = self.limit_field.text or "10"
        try:
            limit = int(limit)
            if limit > 100: limit = 100
            if limit < 1: limit = 1
        except:
            limit = 10
            
        threading.Thread(target=self._do_start_bot, args=(price_id, limit)).start()

    def _do_start_bot(self, price_filter, job_limit):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        base_url = app.base_url
        
        try:
            payload = {
                'job_limit': job_limit,
                'price_filter': price_filter
            }
            resp = requests.post(f"{base_url}/api/v1/recycle-start/", data=payload, headers=headers, timeout=120) # บอทอาจใช้นาน
            if resp.status_code == 200:
                Clock.schedule_once(lambda dt: self.refresh_data())
            else:
                err = resp.json().get('error', 'Unknown Error')
                Clock.schedule_once(lambda dt, msg=err: MDApp.get_running_app().show_error_dialog(f"Error: {msg}"))
        except Exception as e:
            err_msg = str(e)
            print(f"Start bot error: {err_msg}")
            Clock.schedule_once(lambda dt, msg=err_msg: MDApp.get_running_app().show_error_dialog(f"Connection Error: {msg}"))

    def reset_bot(self, *args):
        threading.Thread(target=self._do_reset_bot).start()

    def _do_reset_bot(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        base_url = app.base_url
        
        try:
            resp = requests.post(f"{base_url}/api/v1/recycle-reset/", headers=headers, timeout=15)
            if resp.status_code == 200:
                Clock.schedule_once(lambda dt: self.refresh_data())
        except Exception as e:
            print(f"Reset bot error: {e}")

class AddBinScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.toolbar = MDTopAppBar(title="ເພີ່ມບິນ / Add Bin", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.form_box = MDBoxLayout(orientation='vertical', size_hint_y=None, padding=dp(10), spacing=dp(15))
        self.form_box.bind(minimum_height=self.form_box.setter('height'))
        
        self.name_field = MDTextField(hint_text="Username / ID", mode="rectangle")
        self.pw_field = MDTextField(hint_text="Password", mode="rectangle")
        self.price_lak_field = MDTextField(hint_text="Price LAK", mode="rectangle", input_filter="int")
        self.price_thb_field = MDTextField(hint_text="Price THB", mode="rectangle", input_filter="float")
        self.url_field = MDTextField(hint_text="URL (e.g. royal558.com)", mode="rectangle", text="royal558.com")
        
        if os.path.exists(font_path):
            for f in [self.name_field, self.pw_field, self.price_lak_field, self.price_thb_field, self.url_field]:
                f.font_name = "LaoFont"
                f.font_name_hint_text = "LaoFont"
        
        self.form_box.add_widget(self.name_field)
        self.form_box.add_widget(self.pw_field)
        self.form_box.add_widget(self.price_lak_field)
        self.form_box.add_widget(self.price_thb_field)
        self.form_box.add_widget(self.url_field)
        
        self.submit_btn = MDRaisedButton(
            text="ບັນທຶກຂໍ້ມູນ / SAVE",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            on_release=self.on_submit
        )
        self.form_box.add_widget(self.submit_btn)
        
        self.scroll.add_widget(self.form_box)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def on_submit(self, *args):
        if not self.name_field.text or not self.pw_field.text:
            return
            
        threading.Thread(target=self._do_add_bin).start()

    def _do_add_bin(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        payload = {
            "name": self.name_field.text,
            "pw": self.pw_field.text,
            "price_lak": self.price_lak_field.text or 0,
            "price_thb": self.price_thb_field.text or 0,
            "url": self.url_field.text
        }
        try:
            resp = requests.post(f"{app.base_url}/api/v1/add-bin/", json=payload, headers=headers, timeout=10)
            if resp.status_code == 201:
                Clock.schedule_once(lambda dt: self._on_success())
        except Exception as e: print(f"Add bin error: {e}")

    def _on_success(self):
        self.name_field.text = ""
        self.pw_field.text = ""
        self.price_lak_field.text = ""
        self.price_thb_field.text = ""
        MDApp.get_running_app().show_error_dialog("ບັນທຶກສຳເລັດ! / Saved Successfully")
        self.back_to_home()

class CalculatorScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(15))
        self.toolbar = MDTopAppBar(title="ເຄື່ອງຄິດເລກ / Calculator", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.credit_field = MDTextField(hint_text="ຈຳນວນ Credit / THB", mode="rectangle", input_filter="float")
        self.kib_field = MDTextField(hint_text="ຈຳນວນ ເງິນກີບ / LAK", mode="rectangle", input_filter="float")
        if os.path.exists(font_path):
            self.credit_field.font_name_hint_text = "LaoFont"
            self.kib_field.font_name_hint_text = "LaoFont"
            self.credit_field.font_name = "LaoFont"
            self.kib_field.font_name = "LaoFont"
        
        self.layout.add_widget(self.credit_field)
        self.layout.add_widget(MDLabel(text="ຫຼື / OR", halign="center", font_style="Caption", font_name="LaoFont" if os.path.exists(font_path) else None))
        self.layout.add_widget(self.kib_field)
        
        self.calc_btn = MDRaisedButton(text="ຄຳນວນ / CALCULATE", pos_hint={'center_x': 0.5}, font_name="LaoFont" if os.path.exists(font_path) else None, on_release=self.on_calculate)
        self.layout.add_widget(self.calc_btn)
        
        self.result_card = MDCard(orientation='vertical', padding=dp(10), spacing=dp(5), size_hint_y=None, height=dp(150), radius=dp(10), elevation=2)
        self.result_label = MDLabel(text="ຜົນການຄຳນວນຈະສະແດງຢູ່ນີ້", halign="center", font_name="LaoFont" if os.path.exists(font_path) else None)
        self.result_card.add_widget(self.result_label)
        self.layout.add_widget(self.result_card)
        
        # Spacer
        self.layout.add_widget(MDBoxLayout())
        self.add_widget(self.layout)

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def on_calculate(self, *args):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        
        payload = {}
        if self.credit_field.text:
            payload['credit'] = self.credit_field.text
        elif self.kib_field.text:
            payload['kib'] = self.kib_field.text
        else: return

        try:
            resp = requests.post(f"{app.base_url}/api/v1/calculate/", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                res_text = f"Credit: {data['credit']:,.2f}\n" \
                           f"Price THB: {data['price_thb']:,.2f}\n" \
                           f"Bonus: {data['price_bonus']:,.2f}\n" \
                           f"Total LAK: {data['price_lak']:,.0f}"
                self.result_label.text = res_text
        except Exception as e: print(f"Calc error: {e}")

class DataScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="ຂໍ້ມູນບິນ / Data List",
            elevation=4,
            left_action_items=[["arrow-left", lambda x: self.back_to_home()]]
        )
        self.layout.add_widget(self.toolbar)
        
        # Search Box
        self.search_field = MDTextField(
            hint_text="ຄົ້ນຫາ (ID, Name...)",
            mode="round",
            size_hint_x=0.9,
            pos_hint={'center_x': 0.5},
            on_text_validate=self.on_search
        )
        if os.path.exists(font_path):
            self.search_field.font_name = "LaoFont"
            self.search_field.font_name_hint_text = "LaoFont"
        self.layout.add_widget(self.search_field)
        
        # List
        self.scroll = MDScrollView()
        self.list_container = MDList()
        self.scroll.add_widget(self.list_container)
        self.layout.add_widget(self.scroll)
        
        self.add_widget(self.layout)
        self.all_bins = []
        self.current_page = 1
        self.total_pages = 1
        self._init_loading_overlay()

    def _init_loading_overlay(self):
        from kivymd.uix.spinner import MDSpinner
        from kivy.uix.modalview import ModalView
        from kivy.uix.anchorlayout import AnchorLayout
        modal = ModalView(background_color=[1,1,1,0.6], overlay_color=[0,0,0,0], auto_dismiss=False, size_hint=(1,1))
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(MDSpinner(size_hint=(None,None), size=(dp(48),dp(48)), active=True))
        modal.add_widget(anchor)
        self._loading_modal = modal

    def show_loading(self): self._loading_modal.open()
    def hide_loading(self):
        if self._loading_modal.parent: self._loading_modal.dismiss()

    def on_enter(self):
        self.show_loading()
        self.refresh_data()

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def refresh_data(self):
        self.current_page = 1
        self.show_loading()
        threading.Thread(target=self._fetch_bins_list, args=(1, self.search_field.text), daemon=True).start()

    def load_more(self, *args):
        if self.current_page < self.total_pages:
            self.current_page += 1
            threading.Thread(target=self._fetch_bins_list, args=(self.current_page, self.search_field.text)).start()

    def _fetch_bins_list(self, page=1, query=""):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        try:
            url = f"{app.base_url}/api/v1/imported-data/?page={page}&q={query}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                Clock.schedule_once(lambda dt: self.update_ui(data, append=(page > 1)))
        except Exception as e:
            print(f"Fetch bins error: {e}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def on_search(self, instance):
        self.refresh_data()

    def update_ui(self, data, append=False):
        if not append:
            self.list_container.clear_widgets()
            
        bins = data.get('results', [])
        self.total_pages = data.get('total_pages', 1)
        self.current_page = data.get('current_page', 1)

        from kivymd.uix.list import ThreeLineAvatarIconListItem, IconRightWidget
        for b in bins:
            status_text = " [IN STOCK]" if b['published'] else " [SOLD]"
            status_color = "[color=4CAF50]" if b['published'] else "[color=F44336]" # Green vs Red
            
            item = ThreeLineAvatarIconListItem(
                text=f"ID: #{b['id']} | {b['price_lak']:,.0f} LAK" + f"{status_color}{status_text}[/color]",
                secondary_text=f"Name: {b['name']}",
                tertiary_text=f"PW: {b['pw']} | Rate: {b['lad'] if b['lad'] else 'N/A'}",
                on_release=lambda x, bin_data=b: self.show_item_options(bin_data)
            )
            item.markup = True
            # Add a cart icon to signify selling
            icon = IconRightWidget(icon="dots-vertical", on_release=lambda x, bin_data=b: self.show_item_options(bin_data))
            item.add_widget(icon)
            self.list_container.add_widget(item)
            
        if self.current_page < self.total_pages:
            load_more_btn = MDFillRoundFlatButton(
                text="ໂຫຼດຕື່ມ... / Load More",
                font_name="LaoFont" if os.path.exists(font_path) else None,
                pos_hint={'center_x': 0.5},
                on_release=self.load_more
            )
            # Find and remove any old Load More button first
            for child in self.list_container.children:
                if isinstance(child, MDFillRoundFlatButton) and child.text == "ໂຫຼດຕື່ມ... / Load More":
                    self.list_container.remove_widget(child)
            self.list_container.add_widget(load_more_btn)

    def show_item_options(self, bin_data):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        self.options_dialog = MDDialog(
            title=f"ຕົວເລືອກ / Options: #{bin_data['id']}",
            text=f"ບິນ: {bin_data['name']}\nເລືອກສິ່ງທີ່ຕ້ອງການເຮັດ:",
            buttons=[
                MDFlatButton(
                    text="ຂາຍບິນນີ້ (Sell)",
                    theme_text_color="Primary",
                    font_name="LaoFont" if os.path.exists(font_path) else None,
                    on_release=lambda x: self.confirm_sale_from_options(bin_data)
                ),
                MDFlatButton(
                    text="ລຶບ (Delete)",
                    theme_text_color="Error",
                    font_name="LaoFont" if os.path.exists(font_path) else None,
                    on_release=lambda x: self.confirm_delete_from_options(bin_data)
                ),
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: self.options_dialog.dismiss()
                ),
            ],
        )
        if os.path.exists(font_path):
            self.options_dialog.ids.title.font_name = "LaoFont"
            self.options_dialog.ids.text.font_name = "LaoFont"
        self.options_dialog.open()

    def confirm_sale_from_options(self, bin_data):
        self.options_dialog.dismiss()
        self.confirm_sale(bin_data)

    def confirm_delete_from_options(self, bin_data):
        self.options_dialog.dismiss()
        # Delay opening the next dialog to ensure the previous one is fully dismissed
        Clock.schedule_once(lambda dt: self.confirm_delete(bin_data), 0.2)

    def confirm_delete(self, bin_data):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        self.del_dialog = MDDialog(
            title="ຢືນຢັນການລຶບ / Confirm?",
            text=f"ຕ້ອງການລຶບບິນ ID: #{bin_data['id']} ແມ່ນບໍ່?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.del_dialog.dismiss()),
                MDFlatButton(text="DELETE", theme_text_color="Error", on_release=lambda x: self.execute_delete(bin_data))
            ],
        )
        if os.path.exists(font_path):
            self.del_dialog.ids.title.font_name = "LaoFont"
            self.del_dialog.ids.text.font_name = "LaoFont"
        self.del_dialog.open()

    def execute_delete(self, bin_data):
        self.del_dialog.dismiss()
        threading.Thread(target=self._do_delete, args=(bin_data['id'],)).start()

    def _do_delete(self, bin_id):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        try:
            resp = requests.delete(f"{app.base_url}/api/v1/bins/{bin_id}/", headers=headers, timeout=10)
            if resp.status_code == 204:
                Clock.schedule_once(lambda dt: self.refresh_data())
                # Using MDDialog instead of Snackbar for feedback
                def show_success_dialog(dt):
                    d = MDDialog(
                        title="ສຳເລັດ / Success",
                        text="ລຶບສຳເລັດແລ້ວ! / Deleted Successfully",
                        buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())]
                    )
                    if os.path.exists(font_path):
                        d.ids.title.font_name = "LaoFont"
                        d.ids.text.font_name = "LaoFont"
                    d.open()
                Clock.schedule_once(show_success_dialog)
            else:
                def show_err(dt):
                    d = MDDialog(text=f"Error: {resp.status_code}", buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())])
                    d.open()
                Clock.schedule_once(show_err)
        except Exception as e:
            msg = str(e)
            def show_ex(dt):
                d = MDDialog(text=f"Error: {msg}", buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())])
                d.open()
            Clock.schedule_once(show_ex)

    def confirm_sale(self, bin_data):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        self.dialog = MDDialog(
            title="ຢືນຢັນການຂາຍ?",
            text=f"ຂາຍບິນ ID: #{bin_data['id']}\nລາຄາ: {bin_data['price_lak']:,.0f} LAK",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="CONFIRM", on_release=lambda x, b=bin_data: self.execute_sale(b))
            ],
        )
        self.dialog.open()

    def execute_sale(self, bin_data):
        self.dialog.dismiss()
        dashboard = self.manager.parent.parent # Accessing DashboardScreen methods
        # Create a fake qty dict to reuse existing logic
        dashboard.selected_quantities = {float(bin_data['price_lak']): 1}
        # Override grouped_data temporarily if needed, but easier to just use the one bin
        dashboard.grouped_data[float(bin_data['price_lak'])] = [bin_data]
        dashboard.process_payment()

class OrdersScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="ປະຫວັດການຂາຍ / Orders", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.list_container = MDList()
        self.scroll.add_widget(self.list_container)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)
        self.current_page = 1
        self.total_pages = 1
        self._init_loading_overlay()

    def _init_loading_overlay(self):
        from kivymd.uix.spinner import MDSpinner
        from kivy.uix.modalview import ModalView
        from kivy.uix.anchorlayout import AnchorLayout
        modal = ModalView(background_color=[1,1,1,0.6], overlay_color=[0,0,0,0], auto_dismiss=False, size_hint=(1,1))
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(MDSpinner(size_hint=(None,None), size=(dp(48),dp(48)), active=True))
        modal.add_widget(anchor)
        self._loading_modal = modal

    def show_loading(self): self._loading_modal.open()
    def hide_loading(self):
        if self._loading_modal.parent: self._loading_modal.dismiss()

    def on_enter(self):
        self.show_loading()
        self.refresh_data()

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def refresh_data(self):
        self.current_page = 1
        self.show_loading()
        threading.Thread(target=self._fetch_orders, args=(1,), daemon=True).start()

    def load_more(self, *args):
        if self.current_page < self.total_pages:
            self.current_page += 1
            threading.Thread(target=self._fetch_orders, args=(self.current_page,)).start()

    def _fetch_orders(self, page=1):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        try:
            resp = requests.get(f"{app.base_url}/api/v1/orders/?page={page}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                Clock.schedule_once(lambda dt: self.update_ui(data, append=(page > 1)))
        except Exception as e:
            print(f"Orders fetch error: {e}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def update_ui(self, data, append=False):
        if not append:
            self.list_container.clear_widgets()
            
        orders = data.get('results', [])
        self.total_pages = data.get('total_pages', 1)
        self.current_page = data.get('current_page', 1)

        from kivymd.uix.list import TwoLineListItem
        for o in orders:
            item = TwoLineListItem(
                text=f"Sale #{o['id']} | {o['total_sale_price_lak']:,.0f} LAK",
                secondary_text=f"Date: {o['sale_datetime'][:19].replace('T', ' ')}",
                on_release=lambda x, order=o: self.show_order_detail(order)
            )
            self.list_container.add_widget(item)
            
        if self.current_page < self.total_pages:
            load_more_btn = MDFillRoundFlatButton(
                text="ໂຫຼດຕື່ມ... / Load More",
                font_name="LaoFont" if os.path.exists(font_path) else None,
                pos_hint={'center_x': 0.5},
                on_release=self.load_more
            )
            # Remove old button if exists
            for child in self.list_container.children:
                if isinstance(child, MDFillRoundFlatButton) and child.text == "ໂຫຼດຕື່ມ... / Load More":
                    self.list_container.remove_widget(child)
            self.list_container.add_widget(load_more_btn)

    def show_order_detail(self, order):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        
        rate = order.get('execution_exchange_rate', 0)
        detail_text = f"ວັນທີ: {order['sale_datetime'][:19].replace('T', ' ')}\n"
        if rate: detail_text += f"Rate: {rate:,.0f}\n"
        detail_text += "------------------\n"
        
        for item in order.get('items_detail', []):
            detail_text += f"• {item['bin_name']}\n"
            detail_text += f"  {item['sale_price_lak']:,.0f} LAK | {item['sale_price_thb']:,.2f} THB\n"
            if item.get('sale_bonus'): detail_text += f"  Bonus: {item['sale_bonus']:,.2f}\n"
        
        detail_text += "------------------\n"
        detail_text += f"ລວມ LAK: {order['total_sale_price_lak']:,.0f}\n"
        detail_text += f"ລວມ THB: {order['total_sale_price_thb']:,.2f}\n"
        if order.get('total_sale_bonus'): detail_text += f"ລວມ Bonus: {order['total_sale_bonus']:,.2f}"

        self.detail_dialog = MDDialog(
            title=f"ບິນທີ #{order['id']}",
            text=detail_text,
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: self.detail_dialog.dismiss()),
                MDFlatButton(text="REPRINT", theme_text_color="Primary", on_release=lambda x: self.reprint_order(order)),
            ]
        )
        self.detail_dialog.open()

    def reprint_order(self, order):
        self.detail_dialog.dismiss()
        app = MDApp.get_running_app()
        shop_name = app.config_data.get('shop_name', 'Bin888 Shop')
        
        # Format items to match what setup_voucher expects (bin_name -> name, etc.)
        items = []
        for item in order.get('items_detail', []):
            items.append({
                'name': item.get('bin_name', 'Item'),
                'price_lak': item.get('sale_price_lak', 0),
                'price_thb': item.get('sale_price_thb', 0),
                'price_bonus': item.get('sale_bonus', 0),
                'pw': item.get('pw', 'N/A'),
                'lad': order.get('execution_exchange_rate', 0)
            })
            
        totals = {
            'lak': order['total_sale_price_lak'],
            'thb': order['total_sale_price_thb'],
            'bonus': order.get('total_sale_bonus', 0)
        }
        
        # Switch to voucher preview screen (Accessing via Root ScreenManager)
        root_sm = app.root
        voucher_screen = root_sm.get_screen('voucher')
        voucher_screen.setup_voucher(
            shop_name, 
            items, 
            order['id'], 
            totals, 
            received=order['total_sale_price_lak'], # For reprint, assume received = total
            exchange_rate=order.get('execution_exchange_rate', 650.0)
        )
        root_sm.current = 'voucher'

class SummaryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1]
        self.layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="ສະຫຼຸບຍອດຄ້າຍ / Summary", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.content = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(20), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        
        # --- Chart Section ---
        self.chart_card = MDCard(
            orientation='vertical', padding=dp(10), spacing=dp(10),
            size_hint_y=None, height=dp(250), radius=dp(15), elevation=2,
            md_bg_color=get_color_from_hex("#F8F9FA")
        )
        self.chart_card.add_widget(MDLabel(text="ກຣາບຍອດຂາຍ 7 ວັນ (LAK)", font_style="Subtitle2", halign="center", font_name="LaoFont" if os.path.exists(font_path) else None))
        
        self.chart_layout = MDBoxLayout(orientation='horizontal', spacing=dp(8), padding=[dp(5), dp(10), dp(5), dp(10)])
        self.chart_card.add_widget(self.chart_layout)
        self.content.add_widget(self.chart_card)
        
        # --- Stats List Section ---
        self.stats_card = MDCard(
            orientation='vertical', padding=dp(15), spacing=dp(10),
            size_hint_y=None, radius=dp(15), elevation=1
        )
        self.stats_card.bind(minimum_height=self.stats_card.setter('height'))
        
        self.info_label = MDLabel(
            text="ກຳລັງໂຫຼດຂໍ້ມູນ...", 
            halign="center", 
            theme_text_color="Secondary",
            font_name="LaoFont" if os.path.exists(font_path) else None,
            size_hint_y=None
        )
        self.info_label.bind(texture_size=self.info_label.setter('size'))
        
        self.stats_card.add_widget(self.info_label)
        self.content.add_widget(self.stats_card)
        
        self.scroll.add_widget(self.content)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)
        self._init_loading_overlay()

    def _init_loading_overlay(self):
        from kivymd.uix.spinner import MDSpinner
        from kivy.uix.modalview import ModalView
        from kivy.uix.anchorlayout import AnchorLayout
        modal = ModalView(background_color=[1,1,1,0.6], overlay_color=[0,0,0,0], auto_dismiss=False, size_hint=(1,1))
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(MDSpinner(size_hint=(None,None), size=(dp(48),dp(48)), active=True))
        modal.add_widget(anchor)
        self._loading_modal = modal

    def show_loading(self): self._loading_modal.open()
    def hide_loading(self):
        if self._loading_modal.parent: self._loading_modal.dismiss()

    def on_enter(self):
        self.show_loading()
        self.refresh_data()

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def refresh_data(self):
        self.show_loading()
        threading.Thread(target=self._fetch_summary, daemon=True).start()

    def _fetch_summary(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        try:
            resp = requests.get(f"{app.base_url}/api/v1/summary/", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                Clock.schedule_once(lambda dt: self.update_ui(data))
        except Exception as e:
            print(f"Summary fetch error: {e}")
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def update_ui(self, data):
        daily_stats = data.get('daily_stats', [])
        
        # 1. Update Text Label
        text = "ສະຫຼຸບ 7 ວັນຫຼ້າສຸດ:\n\n"
        for s in daily_stats:
            text += f"{s['label']}: {float(s['total_lak']):,.0f} LAK ({s['total_thb']:,.2f} THB)\n"
            
        text += f"\n------------------\n"
        text += f"ມື້ນີ້: {data.get('today_total_lak', 0):,.0f} LAK\n"
        text += f"ມື້ວານ: {data.get('yesterday_total_lak', 0):,.0f} LAK"
        self.info_label.text = text
        
        # 2. Update Visual Chart
        self.chart_layout.clear_widgets()
        if not daily_stats:
            return
            
        max_val = max([s['total_lak'] for s in daily_stats] + [1]) # Prevent div by zero
        max_plot_height = dp(160)
        
        for s in daily_stats:
            val = float(s['total_lak'])
            # Scale bar height
            h_ratio = val / max_val
            bar_h = max(dp(5), h_ratio * max_plot_height) # Min height 5dp
            
            # Container for Bar + Label
            bar_container = MDBoxLayout(orientation='vertical', spacing=dp(5), size_hint_x=1)
            
            # The Bar itself (Using a card for nice look)
            bar_card = MDCard(
                size_hint_y=None, height=bar_h,
                md_bg_color=get_color_from_hex("#311B92") if s != daily_stats[-1] else get_color_from_hex("#FFB300"), # Gold for today
                radius=dp(4), elevation=0
            )
            
            # Label for date
            date_lbl = MDLabel(
                text=s['label'], halign="center", font_style="Overline",
                theme_text_color="Hint", size_hint_y=None, height=dp(15)
            )
            
            # Align bar to bottom
            spacer = MDBoxLayout() # Takes up remaining space at top
            
            bar_container.add_widget(spacer)
            bar_container.add_widget(bar_card)
            bar_container.add_widget(date_lbl)
            
            self.chart_layout.add_widget(bar_container)

class ProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="ແກ້ໄຂໂປຣໄຟລ໌ / Edit Profile", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.form = MDBoxLayout(orientation='vertical', size_hint_y=None, padding=dp(20), spacing=dp(15))
        self.form.bind(minimum_height=self.form.setter('height'))
        
        self.shop_name = MDTextField(hint_text="ຊື່ຮ້ານ / Shop Name", mode="rectangle")
        self.phone = MDTextField(hint_text="ເບີໂທ / Phone", mode="rectangle")
        self.rate = MDTextField(hint_text="Exchange Rate (LAK/1 THB)", mode="rectangle", input_filter="float")
        self.bonus = MDTextField(hint_text="Bonus %", mode="rectangle", input_filter="float")
        
        if os.path.exists(font_path):
            for f in [self.shop_name, self.phone, self.rate, self.bonus]:
                f.font_name = "LaoFont"
                f.font_name_hint_text = "LaoFont"

        self.form.add_widget(self.shop_name)
        self.form.add_widget(self.phone)
        self.form.add_widget(self.rate)
        self.form.add_widget(self.bonus)
        
        self.save_btn = MDRaisedButton(
            text="ບັນທຶກ / SAVE PROFILE",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            on_release=self.save_profile
        )
        self.form.add_widget(self.save_btn)
        
        self.scroll.add_widget(self.form)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def on_enter(self):
        threading.Thread(target=self._fetch_profile).start()

    def _fetch_profile(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        try:
            resp = requests.get(f"{app.base_url}/api/v1/profile/", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                Clock.schedule_once(lambda dt: self._update_fields(data))
        except: pass

    def _update_fields(self, data):
        self.shop_name.text = str(data.get('shop_name', ''))
        self.phone.text = str(data.get('phone_number', ''))
        self.rate.text = str(data.get('exchange_rate', ''))
        self.bonus.text = str(data.get('bonus_percentage', ''))

    def save_profile(self, *args):
        threading.Thread(target=self._do_save).start()

    def _do_save(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        payload = {
            "shop_name": self.shop_name.text,
            "phone_number": self.phone.text,
            "exchange_rate": self.rate.text or 650,
            "bonus_percentage": self.bonus.text or 3
        }
        try:
            resp = requests.post(f"{app.base_url}/api/v1/profile/", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Update local config too
                app.config_data['shop_name'] = self.shop_name.text
                app.save_config()
                Clock.schedule_once(lambda dt: MDApp.get_running_app().show_error_dialog("ບັນທຶກສຳເລັດ! / Saved!"))
            else:
                Clock.schedule_once(lambda dt: MDApp.get_running_app().show_error_dialog("Error: " + resp.text))
        except Exception as e:
            Clock.schedule_once(lambda dt: MDApp.get_running_app().show_error_dialog(str(e)))

class ChangePasswordScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title="ປ່ຽນລະຫັດຜ່ານ / Change Password", left_action_items=[["arrow-left", lambda x: self.back_to_home()]])
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.form = MDBoxLayout(orientation='vertical', size_hint_y=None, padding=dp(20), spacing=dp(15))
        self.form.bind(minimum_height=self.form.setter('height'))
        
        self.old_pass = MDTextField(hint_text="ລະຫັດຜ່ານເກົ່າ / Old Password", password=True, mode="rectangle")
        self.new_pass = MDTextField(hint_text="ລະຫັດຜ່ານໃໝ່ / New Password", password=True, mode="rectangle")
        self.confirm_pass = MDTextField(hint_text="ຢືນຢັນລະຫັດຜ່ານໃໝ່ / Confirm Password", password=True, mode="rectangle")
        
        if os.path.exists(font_path):
            for f in [self.old_pass, self.new_pass, self.confirm_pass]:
                f.font_name = "LaoFont"
                f.font_name_hint_text = "LaoFont"

        self.form.add_widget(self.old_pass)
        self.form.add_widget(self.new_pass)
        self.form.add_widget(self.confirm_pass)
        
        self.save_btn = MDRaisedButton(
            text="ປ່ຽນລະຫັດຜ່ານ / CHANGE PASSWORD",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            on_release=self.change_password
        )
        self.form.add_widget(self.save_btn)
        
        self.scroll.add_widget(self.form)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def back_to_home(self):
        self.manager.current = 'dashboard_screen'

    def change_password(self, *args):
        if not all([self.old_pass.text, self.new_pass.text, self.confirm_pass.text]):
            MDApp.get_running_app().show_error_dialog("ກະລຸນາປ້ອນຂໍ້ມູນໃຫ້ຄົບ / Please fill all fields")
            return
        if self.new_pass.text != self.confirm_pass.text:
            MDApp.get_running_app().show_error_dialog("ລະຫັດໃໝ່ບໍ່ຕົງກັນ / Passwords do not match")
            return
            
        threading.Thread(target=self._do_change).start()

    def _do_change(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        headers = {'Authorization': f'Token {token}', 'X-App-Access-Key': app.APP_KEY, 'X-App-Version': app.APP_VERSION}
        payload = {
            "old_password": self.old_pass.text,
            "new_password": self.new_pass.text,
            "confirm_password": self.confirm_pass.text
        }
        try:
            resp = requests.post(f"{app.base_url}/api/v1/change-password/", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                def success_notice(dt):
                    app.show_error_dialog("ປ່ຽນລະຫັດສຳເລັດແລ້ວ! / Password Changed!")
                    self.old_pass.text = ""
                    self.new_pass.text = ""
                    self.confirm_pass.text = ""
                Clock.schedule_once(success_notice)
            else:
                try:
                    err = resp.json().get('error', 'Error occurred')
                except:
                    err = f"Error: {resp.status_code}"
                Clock.schedule_once(lambda dt: app.show_error_dialog(err))
        except Exception as e:
            Clock.schedule_once(lambda dt: app.show_error_dialog(str(e)))

class DashboardScreen(MDScreen):
    grouped_data = {} # {price_lak: [list_of_bin_objects]}
    selected_quantities = {} # {price_lak: quantity}

    def on_enter(self):
        self.clear_cart()
        self.refresh_ui()

    def refresh_ui(self):
        config = MDApp.get_running_app().config_data
        shop_name = config.get('shop_name', 'Bin888 Shop')
        self.toolbar.title = shop_name
        
        if self.grouped_data:
            # Show cached data immediately (Stale-While-Revalidate)
            # Then silently refresh in background without blocking UI
            threading.Thread(target=self.fetch_bins, daemon=True).start()
        else:
            # First load — show spinner while waiting
            self.show_loading()
            threading.Thread(target=self.fetch_bins, daemon=True).start()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1] # Ensure Solid White Background
        from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
        from kivymd.uix.screenmanager import MDScreenManager
        from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
        
        self.nav_layout = MDNavigationLayout()
        self.screen_manager = MDScreenManager()
        self.dashboard_main = MDScreen(name='dashboard_screen')
        
        self.layout = MDBoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Bin888 POS",
            elevation=4,
            left_action_items=[["menu", lambda x: self.nav_drawer.set_state("open")]],
            right_action_items=[
                ["magnify", lambda x: self.toggle_search()],
                ["refresh", lambda x: (self.show_loading(), threading.Thread(target=self.fetch_bins, daemon=True).start())],
                ["logout", lambda x: self.logout()]
            ]
        )
        self.layout.add_widget(self.toolbar)
        
        # Dashboard Search - HIDDEN BY DEFAULT
        self.search_container = MDBoxLayout(
            size_hint_y=None, height=0, 
            opacity=0, disabled=True,
            padding=[dp(10), 0, dp(10), 5],
            spacing=dp(5)
        )
        self.main_search_field = MDTextField(
            hint_text="ຄົ້ນຫາບິນ ຫຼື ລາຄາ...",
            mode="round",
            size_hint_y=None, height=dp(40),
            multiline=False
        )
        # Bind for live search and Enter key
        self.main_search_field.bind(text=self.filter_shelf)
        self.main_search_field.bind(on_text_validate=lambda x: self.filter_shelf(x, x.text))
        
        if os.path.exists(font_path):
            self.main_search_field.font_name = "LaoFont"
            self.main_search_field.font_name_hint_text = "LaoFont"
            
        btn_submit = MDIconButton(
            icon="magnify",
            on_release=lambda x: self.filter_shelf(self.main_search_field, self.main_search_field.text)
        )
        
        self.search_container.add_widget(self.main_search_field)
        self.search_container.add_widget(btn_submit)
        self.layout.add_widget(self.search_container)
        
        # Items Grid (2 Columns)
        self.scroll = MDScrollView()
        from kivymd.uix.gridlayout import MDGridLayout
        self.item_grid = MDGridLayout(cols=2, spacing=dp(5), padding=dp(5), size_hint_y=None)
        self.item_grid.bind(minimum_height=self.item_grid.setter('height'))
        self.scroll.add_widget(self.item_grid)
        self.layout.add_widget(self.scroll)
        
        # Bottom Bar
        self.bottom_bar = MDCard(
            size_hint_y=None, height=dp(70),
            padding=[dp(15), dp(5), dp(15), dp(5)], radius=[20, 20, 0, 0],
            elevation=12,
            md_bg_color=get_color_from_hex("#311B92")
        )
        
        self.total_label = MDLabel(
            text="ລວມ: 0 ກີບ",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_name="LaoFont" if os.path.exists(font_path) else None,
            font_style="Subtitle1", bold=True
        )
        
        self.clear_btn = MDIconButton(
            icon="cart-off",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            on_release=self.clear_cart,
            pos_hint={"center_y": .5}
        )

        self.print_btn = MDRaisedButton(
            text="ຕັດສະຕ໋ອກຂາຍ",
            font_name="LaoFont" if os.path.exists(font_path) else None,
            md_bg_color=(1, 0.7, 0, 1), # Amber/Orange
            on_release=self.process_payment,
            pos_hint={"center_y": .5}
        )
        
        container = MDBoxLayout(orientation='vertical', spacing=dp(0))
        footer_layout = MDBoxLayout(spacing=dp(10))
        footer_layout.add_widget(self.total_label)
        footer_layout.add_widget(self.clear_btn)
        footer_layout.add_widget(self.print_btn)
        
        self.cart_info = MDLabel(
            text="ຈຳນວນ: 0",
            theme_text_color="Custom",
            text_color=(0.8, 0.8, 0.8, 1),
            font_name="LaoFont" if os.path.exists(font_path) else None,
            font_style="Caption",
            size_hint_y=None, height=dp(20)
        )
        
        container.add_widget(self.cart_info)
        container.add_widget(footer_layout)
        
        self.bottom_bar.add_widget(container)
        self.layout.add_widget(self.bottom_bar)
        
        self.dashboard_main.add_widget(self.layout)
        self.screen_manager.add_widget(self.dashboard_main)
        
        # Add Other Screens
        self.recycle_screen = RecycleScreen(name='recycle_screen')
        self.data_screen = DataScreen(name='data_screen')
        self.orders_screen = OrdersScreen(name='orders_screen')
        self.summary_screen = SummaryScreen(name='summary_screen')
        self.add_bin_screen = AddBinScreen(name='add_bin_screen')
        self.calculator_screen = CalculatorScreen(name='calculator_screen')
        self.profile_screen = ProfileScreen(name='profile_screen')
        self.change_pass_screen = ChangePasswordScreen(name='change_pass_screen')
        
        self.screen_manager.add_widget(self.recycle_screen)
        self.screen_manager.add_widget(self.data_screen)
        self.screen_manager.add_widget(self.orders_screen)
        self.screen_manager.add_widget(self.summary_screen)
        self.screen_manager.add_widget(self.add_bin_screen)
        self.screen_manager.add_widget(self.calculator_screen)
        self.screen_manager.add_widget(self.profile_screen)
        self.screen_manager.add_widget(self.change_pass_screen)
        
        self.nav_layout.add_widget(self.screen_manager)
        
        # Navigation Drawer setup
        self.nav_drawer = MDNavigationDrawer()
        
        nav_box = MDBoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        nav_box.add_widget(MDLabel(text="BIN888 MENU", font_style="H6", size_hint_y=None, height=dp(40), padding=[dp(10), 0]))
        
        nav_list = MDList()
        menu_items = [
            ("ໜ້າຫຼັກ / Home", "home", lambda x: self.reset_to_home()),
            ("ເພີ່ມ / Add", "plus-box", lambda x: self.switch_to_add_bin()),
            ("ຂໍ້ມູນ / Data", "database", lambda x: self.switch_to_data()),
            ("ຄຳນວນ / Calculator", "calculator", lambda x: self.switch_to_calculator()),
            ("ລາຍການ / Orders", "format-list-bulleted", lambda x: self.switch_to_orders()),
            ("ສະຫຼຸບ / Summary", "chart-bar", lambda x: self.switch_to_summary()),
            ("ໂປຣໄຟລ໌ / Profile", "account-edit", lambda x: self.switch_to_profile()),
            ("ປ່ຽນລະຫັດຜ່ານ / Password", "lock-reset", lambda x: self.switch_to_change_password()),
            ("Recycle", "recycle", lambda x: self.switch_to_recycle()),
            ("ຕັ້ງຄ່າເຄື່ອງພິມ / Reset Printer", "printer-settings", lambda x: self.reset_printer_setting()),
            ("ອອກຈາກລະບົບ / Logout", "logout", lambda x: self.logout())
        ]
        
        for text, icon, callback in menu_items:
            item = OneLineIconListItem(text=text, on_release=callback)
            item.add_widget(IconLeftWidget(icon=icon))
            item.font_name = "LaoFont" if os.path.exists(font_path) else None
            nav_list.add_widget(item)

        scroll_nav = MDScrollView()
        scroll_nav.add_widget(nav_list)
        nav_box.add_widget(scroll_nav)
        
        self.nav_drawer.add_widget(nav_box)
        self.nav_layout.add_widget(self.nav_drawer)
        
        self.add_widget(self.nav_layout)
        self.loading_dialog = None
        self._init_loading_overlay()

    def _init_loading_overlay(self):
        from kivymd.uix.spinner import MDSpinner
        from kivy.uix.modalview import ModalView
        from kivy.uix.anchorlayout import AnchorLayout
        modal = ModalView(background_color=[1,1,1,0.6], overlay_color=[0,0,0,0], auto_dismiss=False, size_hint=(1,1))
        anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        anchor.add_widget(MDSpinner(size_hint=(None,None), size=(dp(48),dp(48)), active=True))
        modal.add_widget(anchor)
        self._loading_modal = modal

    def show_loading(self): self._loading_modal.open()
    def hide_loading(self):
        if self._loading_modal.parent: self._loading_modal.dismiss()

    def switch_to_recycle(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'recycle_screen'
        self.recycle_screen.refresh_data()

    def switch_to_data(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'data_screen'
        self.data_screen.refresh_data()

    def switch_to_orders(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'orders_screen'
        self.orders_screen.refresh_data()

    def switch_to_summary(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'summary_screen'
        self.summary_screen.refresh_data()

    def switch_to_add_bin(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'add_bin_screen'

    def switch_to_calculator(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'calculator_screen'

    def switch_to_profile(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'profile_screen'

    def switch_to_change_password(self):
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'change_pass_screen'

    def toggle_search(self):
        if self.search_container.height == 0:
            self.search_container.height = dp(50)
            self.search_container.opacity = 1
            self.search_container.disabled = False
            self.main_search_field.focus = True
        else:
            self.search_container.height = 0
            self.search_container.opacity = 0
            self.search_container.disabled = True
            self.main_search_field.text = ""
            self.filter_shelf(None, "")

    def filter_shelf(self, instance, value):
        query = value.lower()
        self.item_grid.clear_widgets()
        sorted_prices = sorted(self.grouped_data.keys())
        for p in sorted_prices:
            # Check if any bin in this group matches
            matches = [b for b in self.grouped_data[p] if query in b['name'].lower() or query in str(p)]
            if matches:
                widget = BinGroupWidget(
                    price_lak=p,
                    stock_count=len(matches),
                    on_qty_change=self.handle_qty_change
                )
                self.item_grid.add_widget(widget)

    def toggle_search(self, *args):
        if self.search_container.height == 0:
            self.search_container.height = dp(50)
            self.search_container.opacity = 1
            self.search_container.disabled = False
            self.main_search_field.focus = True
        else:
            self.search_container.height = 0
            self.search_container.opacity = 0
            self.search_container.disabled = True
            self.main_search_field.text = ""
            self.filter_shelf(None, "")

    def filter_shelf(self, instance, value):
        query = value.lower()
        self.item_grid.clear_widgets()
        sorted_prices = sorted(self.grouped_data.keys())
        for p in sorted_prices:
            # Check if any bin in this group matches
            matches = [b for b in self.grouped_data[p] if query in b['name'].lower() or query in str(p)]
            if matches:
                widget = BinGroupWidget(
                    price_lak=p,
                    stock_count=len(matches),
                    on_qty_change=self.handle_qty_change
                )
                self.item_grid.add_widget(widget)

    def show_loading_dialog(self):
        if not self.loading_dialog:
            from kivymd.uix.dialog import MDDialog
            from kivy.uix.boxlayout import BoxLayout
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(10))
            spinner = SpinningLogo(source='app_icon.png', size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={'center_x': .5})
            spinner.start()
            box.add_widget(spinner)
            box.add_widget(MDLabel(text="ກຳລັງປະມວນຜົນ...", halign="center", font_name="LaoFont" if os.path.exists(font_path) else None))
            
            self.loading_dialog = MDDialog(
                title="",
                type="custom",
                content_cls=box,
                auto_dismiss=False
            )
        self.loading_dialog.open()
        
    def hide_loading_dialog(self):
        if self.loading_dialog:
            self.loading_dialog.dismiss()

    def fetch_bins(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        url = f"{app.base_url}/api/v1/bins/?all=1"
        
        try:
            headers = {
                'Authorization': f'Token {token}',
                'X-App-Access-Key': app.APP_KEY,
                'X-App-Version': app.APP_VERSION
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                print("Session expired or logged in elsewhere")
                Clock.schedule_once(lambda dt: app.force_logout(), 0)
                return

            if response.status_code == 403 and "APP_UPDATE_REQUIRED" in response.text:
                Clock.schedule_once(lambda dt: app.show_update_dialog(), 0)
                return

            if response.status_code == 200:
                bins = response.json()
                
                # Group bins by price_lak
                grouped = {}
                for b in bins:
                    price = float(b['price_lak'])
                    if price not in grouped:
                        grouped[price] = []
                    grouped[price].append(b)
                self.grouped_data = grouped
                
                def _update_ui(dt):
                    self.item_grid.clear_widgets()
                    for p in sorted(self.grouped_data.keys()):
                        widget = BinGroupWidget(
                            price_lak=p,
                            stock_count=len(self.grouped_data[p]),
                            on_qty_change=self.handle_qty_change
                        )
                        self.item_grid.add_widget(widget)
                Clock.schedule_once(_update_ui, 0)
                
        except Exception as e:
            print("Error fetching bins:", str(e))
        finally:
            Clock.schedule_once(lambda dt: self.hide_loading(), 0)

    def handle_qty_change(self, price, qty):
        self.selected_quantities[price] = qty
        self.update_total()

    def reset_to_home(self):
        """Reset cart and reload data (Home behavior)"""
        self.nav_drawer.set_state("close")
        self.screen_manager.current = 'dashboard_screen'
        self.clear_cart()
        self.show_loading()
        threading.Thread(target=self.fetch_bins, daemon=True).start()

    def show_in_dev_dialog(self):
        self.nav_drawer.set_state("close")
        self.show_error_dialog("ກຳລັງພັດທະນາ / In Development")

    def clear_cart(self, *args):
        self.selected_quantities = {}
        if hasattr(self, 'item_grid'):
            for widget in self.item_grid.children:
                if isinstance(widget, BinGroupWidget):
                    widget.reset()
        self.update_total()

    def update_total(self):
        total_lak = 0
        total_count = 0
        for price, qty in self.selected_quantities.items():
            total_lak += price * qty
            total_count += qty
            
        self.total_label.text = f"ລວມ: {total_lak:,.0f} ກີບ"
        self.cart_info.text = f"ຈຳນວນ: {total_count}"

    def process_payment(self, *args):
        total_count = sum(self.selected_quantities.values())
        if total_count == 0:
            return
            
        total_lak = sum(price * qty for price, qty in self.selected_quantities.items() if qty > 0)
        
        # Build Cash Received Dialog
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(120))
        content.add_widget(MDLabel(text=f"ຍອດລວມ: {total_lak:,.0f} ກີບ", font_style="Subtitle1", font_name="LaoFont" if os.path.exists(font_path) else None))
        
        cash_input = MDTextField(
            hint_text="ຮັບເງິນທັງໝົດ (ຄ່າເລີ່ມຕົ້ນ = ພໍດີ)",
            input_filter="int",
            mode="fill"
        )
        if os.path.exists(font_path): cash_input.font_name_hint_text = "LaoFont"
        content.add_widget(cash_input)
        
        def confirm_payment(instance):
            try:
                recv_amt = int(cash_input.text.strip()) if cash_input.text.strip() else total_lak
            except:
                recv_amt = total_lak
                
            self.payment_dialog.dismiss()
            self.show_loading_dialog()
            threading.Thread(target=self._do_checkout_thread, args=(total_lak, recv_amt), daemon=True).start()

        self.payment_dialog = MDDialog(
            title="ຮັບເງິນ ແລະ ທອນເງິນ",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="ຍົກເລີກ", on_release=lambda x: self.payment_dialog.dismiss(), font_name="LaoFont" if os.path.exists(font_path) else None),
                MDFlatButton(text="ຢືນຢັນການຂາຍ", on_release=confirm_payment, font_name="LaoFont" if os.path.exists(font_path) else None)
            ]
        )
        if os.path.exists(font_path) and hasattr(self.payment_dialog, 'ids') and 'title' in self.payment_dialog.ids:
            try: self.payment_dialog.ids.title.font_name = "LaoFont"
            except: pass
            
        self.payment_dialog.open()

    def _do_checkout_thread(self, expected_total_lak, received_amount):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        url = f"{app.base_url}/api/v1/create-sale/"
        
        # Pick the actual Bin IDs to sell
        final_bin_ids = []
        final_items_for_receipt = []
        
        total_lak = 0
        total_thb = 0
        total_bonus = 0

        for price, qty in self.selected_quantities.items():
            if qty > 0:
                bins_in_group = self.grouped_data[price][:qty]
                for b in bins_in_group:
                    final_bin_ids.append(b['id'])
                    final_items_for_receipt.append(b)
                    total_lak += float(b['price_lak'])
                    total_thb += float(b['price_thb'])
                    total_bonus += float(b['price_bonus'])

        payload = {
            "bin_ids": final_bin_ids,
            "total_thb": total_thb,
            "total_lak": total_lak,
            "total_bonus": total_bonus
        }

        try:
            headers = {
                'Authorization': f'Token {token}',
                'X-App-Access-Key': app.APP_KEY,
                'X-App-Version': app.APP_VERSION
            }
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            Clock.schedule_once(lambda dt: self._handle_checkout_result(response, total_lak, total_thb, total_bonus, received_amount, final_items_for_receipt))
        except Exception as e:
            print(f"App error during sale process: {str(e)}")
            Clock.schedule_once(lambda dt: self._handle_checkout_error(str(e)))
            
    def _handle_checkout_error(self, error_msg):
        self.hide_loading_dialog()
        self.show_error_dialog(f"Error: {error_msg}")

    def _handle_checkout_result(self, response, total_lak, total_thb, total_bonus, received_amount, final_items_for_receipt):
        app = MDApp.get_running_app()
        
        if response.status_code == 401:
            print("Session expired or logged in elsewhere")
            self.hide_loading_dialog()
            app.force_logout()
            return

        if response.status_code == 403 and "APP_UPDATE_REQUIRED" in response.text:
            self.hide_loading_dialog()
            app.show_update_dialog()
            return

        if response.status_code == 201:
            try:
                sale_id = response.json().get('sale_id')
                exchange_rate = response.json().get('exchange_rate', 650.0)
                
                totals = {"lak": total_lak, "thb": total_thb, "bonus": total_bonus}
                shop_name = app.config_data.get('shop_name', 'Bin888')
                
                voucher_screen = self.manager.get_screen('voucher')
                voucher_screen.setup_voucher(shop_name, final_items_for_receipt, sale_id, totals, received=received_amount, exchange_rate=exchange_rate)
                self.manager.current = 'voucher'
                self.hide_loading_dialog()
                
                self.clear_cart()
                self.fetch_bins()
            except Exception as e:
                import traceback
                err = traceback.format_exc()
                print(f"CRASH IN VOUCHER RENDER: {err}")
                self.hide_loading_dialog()
                self.show_error_dialog(f"Error rendering receipt:\n{str(e)}")
        else:
            self.hide_loading_dialog()
            try:
                resp_json = response.json()
                error_msg = resp_json.get('error', "เกิดข้อผิดพลาดในการทำรายการ")
            except:
                error_msg = "เกิดข้อผิดพลาดในการเชื่อมต่อ หรือเซิร์ฟเวอร์มีปัญหา"
                
            print(f"Sale Failed: {error_msg}")
            self.show_error_dialog(error_msg)

    def show_error_dialog(self, text):
        dialog = MDDialog(
            title="Sale Error",
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def show_success_dialog(self, amount):
        dialog = MDDialog(
            title="Sale Successful",
            text=f"Total: {amount:,.0f} LAK\nReceipt has been sent to printer.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
        dialog.open()

    def logout(self):
        self.manager.current = 'login'
        app = MDApp.get_running_app()
        app.config_data = {}
        path = app.get_config_path()
        if os.path.exists(path):
            os.remove(path)

    def reset_printer_setting(self):
        self.nav_drawer.set_state("close")
        app = MDApp.get_running_app()
        if 'selected_printer_mac' in app.config_data:
            del app.config_data['selected_printer_mac']
        if 'selected_printer_name' in app.config_data:
            del app.config_data['selected_printer_name']
        app.save_config()
        
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        dialog = MDDialog(
            title="ຣີເຊັດເຄື່ອງພິມ / Printer Reset",
            text="ລຶບການເຊື່ອມຕໍ່ເຄື່ອງພິມເກົ່າແລ້ວ\n(Saved printer has been cleared.)",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        if hasattr(dialog, 'ids') and 'title' in dialog.ids and os.path.exists(font_path):
            try: dialog.ids.title.font_name = "LaoFont"
            except: pass
        dialog.open()


class Bin888App(MDApp):
    DEBUG = 1 
    RAISE_ERROR = True
    config_data = {}
    base_url = "https://bm9999.pythonanywhere.com"
    APP_KEY = "Bin888-Premium-Mobile-Key-2024"
    APP_VERSION = "1.0.7"
    brands_cache = []
    printer = PrinterManager()
    
    _last_activity = datetime.now()

    def show_error_dialog(self, text):
        from kivymd.uix.button import MDFlatButton
        d = MDDialog(
            title="Notification",
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: d.dismiss())]
        )
        if os.path.exists(font_path):
            try:
                d.ids.title.font_name = "LaoFont"
                d.ids.text.font_name = "LaoFont"
            except: pass
        d.open()

    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        
        # Track activity for Auto-Logout
        Window.bind(on_touch_down=self._reset_activity)
        from kivy.clock import Clock
        Clock.schedule_interval(self._check_idle_timeout, 60) # Check every minute
        
        # We will fetch brands AFTER loading config to ensure correct base_url
        
        if os.path.exists(font_path):
            self.theme_cls.font_styles["H1"] = ["LaoFont", 96, False, -1.5]
            self.theme_cls.font_styles["H2"] = ["LaoFont", 60, False, -0.5]
            self.theme_cls.font_styles["H3"] = ["LaoFont", 48, False, 0]
            self.theme_cls.font_styles["H4"] = ["LaoFont", 34, False, 0.25]
            self.theme_cls.font_styles["H5"] = ["LaoFont", 24, False, 0]
            self.theme_cls.font_styles["H6"] = ["LaoFont", 20, False, 0.15]
            self.theme_cls.font_styles["Subtitle1"] = ["LaoFont", 16, False, 0.15]
            self.theme_cls.font_styles["Subtitle2"] = ["LaoFont", 14, False, 0.1]
            self.theme_cls.font_styles["Body1"] = ["LaoFont", 16, False, 0.5]
            self.theme_cls.font_styles["Body2"] = ["LaoFont", 14, False, 0.25]
            self.theme_cls.font_styles["Button"] = ["LaoFont", 14, True, 1.25]
            self.theme_cls.font_styles["Caption"] = ["LaoFont", 12, False, 0.4]
            self.theme_cls.font_styles["Overline"] = ["LaoFont", 10, False, 1.5]

        sm = MDScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(VoucherScreen(name='voucher'))
        
        # Persistence Logic: Auto-Login & Screen Restore
        self.load_config()
        # Fetch brands from correct backend
        self.fetch_brands()
        
        if self.config_data.get('token'):
            # If we have a token, skip login
            last_screen = self.config_data.get('last_screen', 'dashboard')
            sm.current = last_screen
        
        # Track screen changes to save state
        sm.bind(current=self._on_screen_change)
        return sm

    def _on_screen_change(self, instance, value):
        if self.config_data.get('token'):
            self.config_data['last_screen'] = value
            self.save_config()

    def get_config_path(self):
        return os.path.join(self.user_data_dir, "last_session.json")

    def save_config(self):
        try:
            with open(self.get_config_path(), "w") as f:
                json.dump({
                    "config_data": self.config_data,
                    "base_url": self.base_url
                }, f)
        except Exception as e:
            print(f"Save Config Error: {e}")

    def load_config(self):
        path = self.get_config_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    self.config_data = data.get("config_data", {})
                    self.base_url = data.get("base_url", self.base_url)
            except Exception as e:
                print(f"Load Config Error: {e}")

    def _reset_activity(self, *args):
        self._last_activity = datetime.now()

    def _check_idle_timeout(self, *args):
        if not self.config_data.get('token'):
            return
            
        elapsed = (datetime.now() - self._last_activity).total_seconds()
        if elapsed > 1800: # 30 minutes
            print("Auto-logout due to inactivity")
            self.force_logout()

    def force_logout(self):
        sm = self.root
        if sm and sm.current != 'login':
            dashboard = sm.get_screen('dashboard')
            dashboard.logout()

    def show_update_dialog(self):
        if not hasattr(self, 'update_dialog') or not self.update_dialog:
            self.update_dialog = MDDialog(
                title="ແຈ້ງເຕືອນອັບເດດ (Update!)",
                text="ມີເວີຊັນໃໝ່ໃຫ້ອັບເດດແລ້ວ\nກະລຸນາຕິດຕໍ່ Admin ເພື່ອຂໍເວີຊັນໃໝ່.",
                auto_dismiss=False,  # Force user to acknowledge
                buttons=[
                    MDFlatButton(
                        text="ຕົກລົງ",
                        on_release=lambda x: self.force_logout()
                    )
                ],
            )
            # Use LaoFont if available
            if os.path.exists(font_path) and hasattr(self.update_dialog, 'ids'):
                # Try to apply font to the dialog text elements
                try:
                    self.update_dialog.ids.title.font_name = "LaoFont"
                    self.update_dialog.ids.text.font_name = "LaoFont"
                except: pass
        if not self.update_dialog._is_open:
            self.update_dialog.open()

    def fetch_brands(self):
        try:
            # Simple fetch to populate categories/logos
            headers = {
                'X-App-Access-Key': self.APP_KEY,
                'X-App-Version': self.APP_VERSION
            }
            print(f"Fetching brands from: {self.base_url}/api/v1/brands/")
            response = requests.get(f"{self.base_url}/api/v1/brands/", headers=headers, timeout=5)
            if response.status_code == 200:
                self.brands_cache = response.json()
                print(f"Loaded {len(self.brands_cache)} brands from server")
            else:
                print(f"Failed to fetch brands. Status: {response.status_code}, Msg: {response.text}")
        except Exception as e:
            print(f"Could not fetch brands: {e}")

if __name__ == "__main__":
    Bin888App().run()

