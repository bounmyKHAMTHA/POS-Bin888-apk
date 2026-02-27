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

    def print_receipt(self, shop_name, items, total_lak):
        print(f"Printing to Bluetooth: {shop_name}")
        
        from kivy.utils import platform
        if platform != 'android':
            print("Fallback for desktop: print to terminal")
            print(f"--- {shop_name} ---")
            for item in items:
                print(f"{item['name']} - {item['price_lak']:,} LAK")
            print(f"TOTAL: {total_lak:,.0f} LAK")
            print("-------------------")
            return

        try:
            from jnius import autoclass
            # Android Bluetooth API
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            UUID = autoclass('java.util.UUID')
            
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter:
                print("Bluetooth not supported on this device")
                return
                
            if not adapter.isEnabled():
                print("Bluetooth is disabled")
                return

            # Standard Serial Port Profile UUID
            SERIAL_UUID = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb")
            
            paired_devices = adapter.getBondedDevices().toArray()
            target_device = None
            for device in paired_devices:
                # Look for typical printer names or just take the first paired if none found
                if "Printer" in device.getName() or "MPT" in device.getName():
                    target_device = device
                    break
            
            if not target_device and paired_devices:
                target_device = paired_devices[0]

            if not target_device:
                print("No paired Bluetooth printer found")
                return

            socket = target_device.createRfcommSocketToServiceRecord(SERIAL_UUID)
            socket.connect()
            ostream = socket.getOutputStream()

            # ESC/POS commands
            # Initialize: ESC @
            ostream.write(bytes([0x1B, 0x40]))
            # Center Align: ESC a 1
            ostream.write(bytes([0x1B, 0x61, 0x01]))
            # Bold On: ESC E 1
            ostream.write(bytes([0x1B, 0x45, 0x01]))
            ostream.write(f"{shop_name}\n\n".encode('utf-8'))
            # Bold Off
            ostream.write(bytes([0x1B, 0x45, 0x00]))
            # Left Align: ESC a 0
            ostream.write(bytes([0x1B, 0x61, 0x00]))
            
            for item in items:
                line = f"{item['name']}\n{item['price_lak']:,.0f} LAK\n"
                ostream.write(line.encode('utf-8'))
            
            ostream.write(f"\nTOTAL: {total_lak:,.0f} LAK\n".encode('utf-8'))
            ostream.write(b"\n\n\n\n") # Feed lines
            
            ostream.flush()
            socket.close()
            print("Print successful")
            
        except Exception as e:
            print(f"Printer Error: {str(e)}")
            # Fallback for desktop: print to terminal
            print(f"--- {shop_name} ---")
            for item in items:
                print(f"{item['name']} - {item['price_lak']:,} LAK")
            print(f"TOTAL: {total_lak:,} LAK")
            print("-------------------")

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1] # Ensure Solid White Background
        layout = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Header Area
        header = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(10))
        header.add_widget(MDLabel(
            text="BIN888",
            halign="center",
            font_style="H3",
            theme_text_color="Primary"
        ))
        header.add_widget(MDLabel(
            text="Mobile POS System",
            halign="center",
            font_style="Subtitle1",
            theme_text_color="Secondary"
        ))
        layout.add_widget(header)

        # Form Area
        content = MDBoxLayout(orientation='vertical', spacing=dp(15))
        
        self.url_field = MDTextField(
            text="https://bm9999.pythonanywhere.com",
            hint_text="Server URL (e.g., http://yourserver.com)",
            icon_right="server",
            mode="fill"
        )
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
        
        content.add_widget(self.url_field)
        content.add_widget(self.user_field)
        content.add_widget(self.pass_field)
        
        self.login_btn = MDFillRoundFlatButton(
            text="LOGIN TO SYSTEM",
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
        base_url = self.url_field.text.strip("/")
        username = self.user_field.text
        password = self.pass_field.text
        
        if not username or not password:
            self.user_field.error = True
            return

        self.login_btn.text = "CONNECTING..."
        self.login_btn.disabled = True
        
        try:
            app = MDApp.get_running_app()
            headers = {'X-App-Access-Key': app.APP_KEY}
            response = requests.post(
                f"{base_url}/api/v1/login/",
                data={"username": username, "password": password},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                MDApp.get_running_app().config_data = data
                MDApp.get_running_app().base_url = base_url
                MDApp.get_running_app().save_config() # Save for hot reload
                self.manager.current = 'dashboard'
            else:
                print("Login Failed:", response.text)
                self.login_btn.text = "LOGIN FAILED - RETRY"
        except Exception as e:
            print("Error connecting to server:", str(e))
            self.login_btn.text = "SERVER ERROR"
        finally:
            self.login_btn.disabled = False

class VoucherItemCard(MDCard):
    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(260)
        self.padding = 0
        self.spacing = 0
        self.elevation = 1
        
        # Brand styling
        name_lower = str(item.get('name', '')).lower()
        header_color = [0.2, 0.2, 0.2, 1]
        brand_label = "GIFT CARD"
        logo_url = None
        
        app = MDApp.get_running_app()
        matched_brand = None
        for b in app.brands_cache:
            if b.get('keyword') and b['keyword'].lower() in name_lower:
                matched_brand = b
                break
        if not matched_brand and app.brands_cache:
            import random
            matched_brand = random.choice(app.brands_cache)
            
        if matched_brand:
            brand_label = matched_brand['name'].upper()
            logo_url = matched_brand.get('logo')
            kw = matched_brand.get('keyword', '').lower()
            if 'apple' in kw: header_color = [0.17, 0.24, 0.31, 1]
            elif 'google' in kw: header_color = [0.2, 0.66, 0.32, 1]
            elif 'garena' in kw: header_color = [0.93, 0.11, 0.14, 1]

        # Apply Header Color to the Entire Card to ensure smooth top corners
        self.md_bg_color = header_color
        self.radius = [10, 10, 10, 10]

        # Header Text Holder (Centered in the top part)
        header_text_area = MDBoxLayout(size_hint_y=None, height=dp(28), padding=[0, dp(2)])
        header_text_area.add_widget(MDLabel(
            text=brand_label, halign="center", 
            theme_text_color="Custom", text_color=[1,1,1,1], 
            font_style="Caption", bold=True
        ))
        self.add_widget(header_text_area)

        # Content Area (White Background, Rounded Bottom)
        content = MDBoxLayout(
            orientation="vertical", 
            md_bg_color=[1, 1, 1, 1], # Pure White
            radius=[0, 0, 10, 10],   # Round only bottom corners
            padding=[dp(10), dp(0), dp(10), dp(10)], # Top padding 0 for tighter fit
            spacing=dp(5),
            size_hint_y=1 # Fill the rest of the card
        )
        
        # Logo if available
        if logo_url:
            from kivy.uix.image import AsyncImage
            full_logo_url = logo_url if logo_url.startswith('http') else f"{app.base_url}{logo_url}"
            # Logo (Fixed size block)
            logo_img = AsyncImage(
                source=full_logo_url, 
                size_hint=(1, None), 
                height=dp(35), # Clear height
                allow_stretch=True,
                keep_ratio=True
            )
            content.add_widget(logo_img)
            # Product Name (Increased 30% to H6)
            content.add_widget(MDLabel(text=item['name'], halign="center", font_style="H6", bold=True, size_hint_y=None, height=dp(25)))
        else:
            content.add_widget(MDLabel(text=item['name'], halign="center", font_style="H6", bold=True, size_hint_y=None, height=dp(25)))
        
        # Display LAK / THB + Bonus (Match Web - Using Lao Unicode)
        price_lak = float(item['price_lak'])
        price_thb = float(item['price_thb'])
        price_bonus = float(item.get('price_bonus', 0))
        
        bonus_text = f" + ໂບນັດ {price_bonus:,.2f} THB" if price_bonus > 0 else ""
        prices = MDLabel(
            text=f"{price_lak:,.0f} ກີບ / {price_thb:,.2f} THB{bonus_text}",
            halign="center", theme_text_color="Primary", font_style="Caption",
            font_name="LaoFont" if os.path.exists(font_path) else None,
            size_hint_y=None, height=dp(20) # Add fixed height to prevent overlap
        )
        content.add_widget(prices)
        
        # PIN BOX (Larger for visibility)
        pin_box = MDCard(
            orientation="vertical", padding=dp(10), 
            md_bg_color=[0.96, 0.96, 0.96, 1],
            line_color=[0, 0, 0, 1], line_width=1,
            size_hint_y=None, height=dp(70)
        )
        pin_box.add_widget(MDLabel(text="PIN CODE / REDEEM CODE", halign="center", font_style="Caption", theme_text_color="Secondary"))
        # PIN reduced to match Product Name style (H6 Bold)
        pin_box.add_widget(MDLabel(text=str(item.get('pw', 'N/A')), halign="center", font_style="H6", bold=True, theme_text_color="Primary"))
        
        content.add_widget(pin_box)
        
        # Mock Barcode (Restored & Optimized)
        content.add_widget(MDIcon(
            icon="barcode", halign="center", 
            theme_text_color="Primary", font_size=dp(55),
            pos_hint={"center_x": .5}, size_hint=(None, None), size=(dp(120), dp(35))
        ))

        self.add_widget(content)
        
        # Dashed separator with scissors icon (Premium Look)
        sep_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20), padding=[dp(10), 0])
        sep_layout.add_widget(MDIcon(icon="content-cut", font_size=dp(18), theme_text_color="Secondary", pos_hint={"center_y": .5}))
        sep_layout.add_widget(MDLabel(text="-" * 45, halign="center", theme_text_color="Secondary"))
        content.add_widget(sep_layout)

class VoucherScreen(MDScreen):
    def setup_voucher(self, shop_name, items, sale_id, totals, received=0):
        self.items_container.clear_widgets()
        self.shop_label.text = shop_name
        app = MDApp.get_running_app()
        self.phone_text.text = f" {app.config_data.get('phone', '977 18 595')}"
        
        # Current Date Time for header
        from datetime import datetime
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Safe float conversion for display
        lak_total = float(totals.get('lak', 0))
        self.sale_info.text = f"ID: #{sale_id} | {now_str}"
        
        for item in items:
            self.items_container.add_widget(VoucherItemCard(item))
            
        # Update Summary Table with float casting to avoid format errors
        self.summary_lak.text = f"{float(totals['lak']):,.0f} LAK"
        self.summary_thb.text = f"{float(totals['thb']):,.2f} THB"
        
        # Received and Change logic
        received = float(received)
        change = received - lak_total if received > lak_total else 0
        self.summary_receive.text = f"{received:,.0f} LAK"
        self.summary_change.text = f"{change:,.0f} LAK"

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
        self._print_phone = app.config_data.get('phone', '977 18 595')

        if float(totals.get('bonus', 0)) > 0:
            self.summary_bonus.text = f"+ {float(totals['bonus']):,.2f} THB"
            self.summary_bonus_row.height = dp(30)
            self.summary_bonus_row.opacity = 1
        else:
            self.summary_bonus_row.height = 0
            self.summary_bonus_row.opacity = 0

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
        
        # Shop Info Header (More compact)
        header = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(80), spacing=dp(2))
        self.shop_label = MDLabel(text="SHOP NAME", halign="center", font_style="H6", bold=True)
        self.shop_phone = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(25), adaptive_width=True, pos_hint={"center_x": .5})
        self.shop_phone.add_widget(MDIcon(icon="whatsapp", size_hint=(None, None), size=(dp(20), dp(20)), theme_text_color="Custom", text_color=[0.2, 0.6, 0.2, 1]))
        self.phone_text = MDLabel(text="Phone", halign="left", font_style="Caption", adaptive_width=True)
        self.shop_phone.add_widget(self.phone_text)
        
        self.sale_info = MDLabel(text="ID: #0000", halign="center", theme_text_color="Secondary", font_style="Overline")
        header.add_widget(self.shop_label)
        header.add_widget(self.shop_phone)
        header.add_widget(self.sale_info)
        content.add_widget(header)
        
        # Items Container
        self.items_container = MDBoxLayout(orientation="vertical", spacing=dp(15), size_hint_y=None)
        self.items_container.bind(minimum_height=self.items_container.setter('height'))
        content.add_widget(self.items_container)
        
        # Summary Table (Ultra Compact - Font size reduced by ~20%)
        summary_card = MDCard(orientation="vertical", padding=dp(5), spacing=dp(2), size_hint_y=None, height=dp(140), elevation=2)
        
        def create_row(label, val_attr):
            row = MDBoxLayout(size_hint_y=None, height=dp(23))
            row.add_widget(MDLabel(text=label, font_style="Caption"))
            val_label = MDLabel(text="0", halign="right", font_style="Subtitle2", bold=True)
            setattr(self, val_attr, val_label)
            row.add_widget(val_label)
            return row

        summary_card.add_widget(create_row("Total LAK:", "summary_lak"))
        summary_card.add_widget(create_row("Total THB:", "summary_thb"))
        self.summary_bonus_row = create_row("Total Bonus:", "summary_bonus")
        summary_card.add_widget(self.summary_bonus_row)
        
        # Add Receive/Change rows
        summary_card.add_widget(MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=[0,0,0,0.1])) # Separation
        summary_card.add_widget(create_row("Received:", "summary_receive"))
        change_row = create_row("Change:", "summary_change")
        change_row.children[0].theme_text_color = "Primary"
        change_row.children[0].bold = True
        summary_card.add_widget(change_row)
        
        content.add_widget(summary_card)
        
        # Info Text (Compact)
        footer_text = (
            "*** ທຸກບິນທີ່ຂາຍໄປຢູ່ໄດ້ບໍ່ເກີນ 3 ວັນຈະໝົດອາຍຸ ຫາກໝົດອາຍຸແລ້ວຕິດຕໍ່ຮ້ານຄ້າເພື່ອແກ້ໄຂ ***\n"
            "ຂອບໃຈທີ່ໃຊ້ບໍລິການ / Thank You!"
        )
        content.add_widget(MDLabel(
            text=footer_text,
            halign="center", theme_text_color="Secondary", 
            font_style="Caption", height=dp(50), size_hint_y=None,
            font_name="LaoFont" if os.path.exists(font_path) else None
        ))
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        
        # Bottom Buttons (Cleaned up from testing)
        btns = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(10), spacing=dp(10))
        btns.add_widget(MDFillRoundFlatButton(text="DONE", size_hint_x=0.4, on_release=self.go_back))
        btns.add_widget(MDFillRoundFlatButton(text="PRINT RECEIPT", size_hint_x=0.6, md_bg_color=[0, 0.5, 1, 1], on_release=self.print_action))
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
            self._print_via_socket(mac, name)
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

    def _print_via_socket(self, mac, name):
        """Connect and print using PROVEN Android JNI UUID method from test app."""
        import threading
        from kivy.clock import Clock
        
        shop_name = getattr(self, '_print_shop_name', 'Shop')
        items = getattr(self, '_print_items', [])
        total_lak = getattr(self, '_print_total_lak', 0)
        
        Snackbar(MDLabel(text=f"Connecting to {name}...", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
        
        def run():
            bt_socket = None
            try:
                from jnius import autoclass
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                UUID = autoclass('java.util.UUID')
                
                adapter = BluetoothAdapter.getDefaultAdapter()
                adapter.cancelDiscovery()  # CRITICAL for stability

                device = adapter.getRemoteDevice(mac)
                serial_uuid = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb")
                
                bt_socket = device.createInsecureRfcommSocketToServiceRecord(serial_uuid)
                bt_socket.connect()
                
                ostream = bt_socket.getOutputStream()
                
                # ========================================
                # 1. GENERATE RECEIPT IMAGE VIA PILLOW
                # ========================================
                from PIL import Image, ImageDraw, ImageFont
                global font_path
                
                # Fetch full data
                pt_thb = getattr(self, '_print_total_thb', 0)
                pt_bonus = getattr(self, '_print_total_bonus', 0)
                pt_rec = getattr(self, '_print_received', 0)
                pt_chg = getattr(self, '_print_change', 0)
                pt_sid = getattr(self, '_print_sale_id', '0000')
                pt_date = getattr(self, '_print_date', '')
                pt_phone = getattr(self, '_print_phone', '')
                
                img_w = 384 # 58mm printer width
                # Estimate height based on dynamic content length + 200 padding at the end
                height = 250 + (len(items) * 200) + 300 + 200
                img = Image.new('1', (img_w, height), 1)
                draw = ImageDraw.Draw(img)
                
                try:
                    f_h3 = ImageFont.truetype(font_path, 34)
                    f_h6 = ImageFont.truetype(font_path, 28)
                    f_body = ImageFont.truetype(font_path, 24)
                    f_small = ImageFont.truetype(font_path, 20)
                except Exception:
                    f_h3 = ImageFont.load_default()
                    f_h6 = f_h3
                    f_body = f_h3
                    f_small = f_h3

                def draw_center(text, y_pos, font):
                    bbox = draw.textbbox((0, 0), str(text), font=font)
                    tw = bbox[2] - bbox[0]
                    draw.text(((img_w - tw) // 2, y_pos), str(text), font=font, fill=0)
                    return y_pos + (bbox[3] - bbox[1]) + 10

                def draw_row(label, value, y_pos, font):
                    draw.text((10, y_pos), str(label), font=font, fill=0)
                    bbox = draw.textbbox((0, 0), str(value), font=font)
                    tw = bbox[2] - bbox[0]
                    draw.text((img_w - 10 - tw, y_pos), str(value), font=font, fill=0)
                    return y_pos + (bbox[3] - bbox[1]) + 10

                y = 10
                
                # 1. Header (Shop, Phone, ID, Date)
                y = draw_center(shop_name, y, f_h3) + 5
                y = draw_center(f"Phone: {pt_phone}", y, f_body)
                y = draw_center(f"ID: #{pt_sid} | {pt_date}", y, f_small) + 15
                
                # Top Demarcation
                draw.line((10, y, img_w-10, y), fill=0, width=2)
                y += 15
                
                # 2. Items
                for item in items:
                    y = draw_center("GIFT CARD", y, f_small)
                    y = draw_center(item['name'], y, f_h6)
                    
                    price_lak = float(item['price_lak'])
                    price_thb = float(item['price_thb'])
                    price_bonus = float(item.get('price_bonus', 0))
                    
                    bonus_text = f" + ໂບນັດ {price_bonus:,.2f} THB" if price_bonus > 0 else ""
                    sub_text = f"{price_lak:,.0f} ກີບ / {price_thb:,.2f} THB{bonus_text}"
                    y = draw_center(sub_text, y, f_small) + 15
                    
                    # PIN Outline Box
                    y = draw_center("PIN CODE / REDEEM CODE", y, f_small)
                    pw_str = str(item.get('pw', 'N/A'))
                    
                    bbox = draw.textbbox((0, 0), pw_str, font=f_h3)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                    
                    bx = (img_w - tw) // 2 - 20
                    by = y - 5
                    bw = tw + 40
                    bh = th + 20
                    
                    # Draw rounded rectangle equivalent using lines
                    draw.rectangle([bx, by, bx+bw, by+bh], outline=0, width=2)
                    draw.text(((img_w - tw) // 2, y + 2), pw_str, font=f_h3, fill=0)
                    y += bh + 25
                    
                    # Bottom Demarcation
                    draw.line((10, y, img_w-10, y), fill=0, width=1)
                    y += 15
                
                # 3. Summary
                y = draw_row("Total LAK:", f"{total_lak:,.0f} LAK", y, f_body)
                y = draw_row("Total THB:", f"{pt_thb:,.2f} THB", y, f_body)
                if pt_bonus > 0:
                    y = draw_row("Total Bonus:", f"+ {pt_bonus:,.2f} THB", y, f_body)
                
                y += 10
                draw.line((10, y, img_w-10, y), fill=0, width=1)
                y += 10
                
                y = draw_row("Received:", f"{pt_rec:,.0f} LAK", y, f_body)
                y = draw_row("Change:", f"{pt_chg:,.0f} LAK", y, f_h6) + 20
                
                # 4. Footer
                footer1 = "*** ທຸກບິນທີ່ຂາຍໄປຢູ່ໄດ້ບໍ່ເກີນ 3 ວັນຈະໝົດອາຍຸ"
                footer2 = "ຫາກໝົດອາຍຸແລ້ວຕິດຕໍ່ຮ້ານຄ້າເພື່ອແກ້ໄຂ ***"
                footer3 = "ຂອບໃຈທີ່ໃຊ້ບໍລິການ / Thank You!"
                
                y = draw_center(footer1, y, f_small)
                y = draw_center(footer2, y, f_small) + 10
                y = draw_center(footer3, y, f_small)
                
                # EXTRA PADDING AT THE BOTTOM (1-2 lines for tearing)
                y += 150 
                
                img = img.crop((0, 0, img_w, y))
                
                # ========================================
                # 2. CONVERT PILLOW IMAGE TO ESC/POS RASTER
                # ========================================
                w, h = img.size
                pad_w = ((w + 7) // 8) * 8
                if pad_w != w:
                    new_img = Image.new('1', (pad_w, h), 1)
                    new_img.paste(img, (0,0))
                    img = new_img
                    w = pad_w

                xL = (w // 8) % 256
                xH = (w // 8) // 256
                yL = h % 256
                yH = h // 256
                
                receipt = bytearray()
                receipt.extend([0x1B, 0x40]) # Init
                receipt.extend([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
                
                pixels = img.load()
                for py in range(h):
                    for px_byte in range(w // 8):
                        byte_val = 0
                        for bit in range(8):
                            idx = px_byte * 8 + bit
                            if pixels[idx, py] == 0:
                                byte_val |= (1 << (7 - bit))
                        receipt.append(byte_val)
                
                receipt.extend([0x0A, 0x0A, 0x0A, 0x0A, 0x0A]) # Feed lines
                
                # Write to stream
                # Try passing Python bytes directly (works in modern jnius)
                try:
                    ostream.write(bytes(receipt))
                except Exception:
                    # Fallback write byte-by-byte if type mapping fails
                    for b in receipt: ostream.write(b)
                    
                ostream.flush()
                bt_socket.close()
                
                Clock.schedule_once(lambda dt: Snackbar(MDLabel(text="\u2713 Print OK! (Check printer)", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open(), 0)
            except Exception as e:
                err = str(e)
                if bt_socket:
                    try: bt_socket.close()
                    except: pass
                Clock.schedule_once(lambda dt, m=f"BT Printer Error: {err[:60]}": Snackbar(MDLabel(text=m, theme_text_color="Custom", text_color=[1, 1, 1, 1])).open(), 0)
                
        threading.Thread(target=run, daemon=True).start()

    def print_action(self, *args):
        """Handle print button - request permissions then show printer picker."""
        from kivy.utils import platform
        if platform != 'android':
            Snackbar(MDLabel(text="Bluetooth printing is only supported on Android", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
            return
            
        try:
            from android.permissions import request_permissions, check_permission, Permission
            perms = [
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION,
            ]
            if not all(check_permission(p) for p in perms):
                def on_permission_result(permissions, grants):
                    if all(grants):
                        self.scan_and_pick_printer()
                    else:
                        Snackbar(MDLabel(text="Bluetooth permission denied.", theme_text_color="Custom", text_color=[1, 1, 1, 1])).open()
                request_permissions(perms, on_permission_result)
                return
        except ImportError:
            pass  

        self.scan_and_pick_printer()

class BinGroupWidget(MDCard): # Change to MDCard for better grid look
    def __init__(self, price_lak, stock_count, on_qty_change, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(110) # Square-ish for grid
        self.padding = dp(10)
        self.spacing = dp(5)
        self.elevation = 1
        self.price_lak = price_lak
        self.stock_count = stock_count
        self.quantity = 0
        self.on_qty_change = on_qty_change

        # Price and Stock Info
        self.price_label = MDLabel(
            text=f"{price_lak:,.0f} LAK",
            font_style="Subtitle1", bold=True,
            halign="center", theme_text_color="Primary"
        )
        self.stock_label = MDLabel(
            text=f"Stock: {stock_count}",
            font_style="Caption", halign="center",
            theme_text_color="Secondary"
        )
        self.add_widget(self.price_label)
        self.add_widget(self.stock_label)
        
        # Quantity Controls
        controls = MDBoxLayout(spacing=dp(2), pos_hint={"center_x": .5}, adaptive_width=True)
        
        btn_minus = MDIconButton(
            icon="minus-circle", icon_size=dp(20),
            theme_text_color="Custom", text_color=(1, 0, 0, 1),
            on_release=self.decrease
        )
        
        self.qty_label = MDLabel(
            text="0", halign="center", font_style="Subtitle1",
            width=dp(25), size_hint_x=None
        )
        
        btn_plus = MDIconButton(
            icon="plus-circle", icon_size=dp(20),
            theme_text_color="Custom", text_color=(0, 0.6, 0, 1),
            on_release=self.increase
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

class DashboardScreen(MDScreen):
    grouped_data = {} # {price_lak: [list_of_bin_objects]}
    selected_quantities = {} # {price_lak: quantity}

    def on_enter(self):
        self.clear_cart()
        self.refresh_ui()

    def refresh_ui(self):
        config = MDApp.get_running_app().config_data
        shop_name = config.get('shop_name', 'Bin888 Shop')
        self.toolbar.title = f"POS: {shop_name}"
        self.fetch_bins()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 1, 1, 1] # Ensure Solid White Background
        self.layout = MDBoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Bin888 POS",
            elevation=4,
            right_action_items=[
                ["home", lambda x: self.reset_to_home()],
                ["refresh", lambda x: self.fetch_bins()],
                ["logout", lambda x: self.logout()]
            ]
        )
        self.layout.add_widget(self.toolbar)
        
        # Categories Header
        actions = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        actions.add_widget(MDLabel(text="Available Items By Group", padding=(dp(10), 0)))
        self.layout.add_widget(actions)

        # Items Grid (2 Columns)
        self.scroll = MDScrollView()
        from kivymd.uix.gridlayout import MDGridLayout
        self.item_grid = MDGridLayout(cols=2, spacing=dp(10), padding=dp(10), size_hint_y=None)
        self.item_grid.bind(minimum_height=self.item_grid.setter('height'))
        self.scroll.add_widget(self.item_grid)
        self.layout.add_widget(self.scroll)
        
        # Bottom Bar
        self.bottom_bar = MDCard(
            size_hint_y=None, height=dp(100),
            padding=dp(15), radius=[20, 20, 0, 0],
            elevation=12,
            md_bg_color=get_color_from_hex("#311B92")
        )
        
        self.total_label = MDLabel(
            text="Total: 0 LAK",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_style="H6"
        )
        
        self.clear_btn = MDIconButton(
            icon="cart-off",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            on_release=self.clear_cart
        )

        self.print_btn = MDRaisedButton(
            text="PAY & PRINT",
            md_bg_color=(1, 0.7, 0, 1), # Amber/Orange
            on_release=self.process_payment
        )
        
        container = MDBoxLayout(orientation='vertical', spacing=dp(5))
        footer_layout = MDBoxLayout(spacing=dp(10))
        footer_layout.add_widget(self.total_label)
        footer_layout.add_widget(self.clear_btn)
        footer_layout.add_widget(self.print_btn)
        
        self.cart_info = MDLabel(
            text="Items in cart: 0",
            theme_text_color="Custom",
            text_color=(0.8, 0.8, 0.8, 1),
            font_style="Caption"
        )
        
        container.add_widget(self.cart_info)
        container.add_widget(footer_layout)
        
        self.bottom_bar.add_widget(container)
        self.layout.add_widget(self.bottom_bar)
        
        self.add_widget(self.layout)

    def fetch_bins(self):
        app = MDApp.get_running_app()
        token = app.config_data.get('token')
        url = f"{app.base_url}/api/v1/bins/"
        
        try:
            headers = {
                'Authorization': f'Token {token}',
                'X-App-Access-Key': app.APP_KEY
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                print("Session expired or logged in elsewhere")
                app.force_logout()
                return

            if response.status_code == 200:
                bins = response.json()
                
                # Group bins by price_lak
                self.grouped_data = {}
                for b in bins:
                    price = float(b['price_lak'])
                    if price not in self.grouped_data:
                        self.grouped_data[price] = []
                    self.grouped_data[price].append(b)
                
                # Update UI Grid
                self.item_grid.clear_widgets()
                # Sort by price
                sorted_prices = sorted(self.grouped_data.keys())
                for p in sorted_prices:
                    widget = BinGroupWidget(
                        price_lak=p,
                        stock_count=len(self.grouped_data[p]),
                        on_qty_change=self.handle_qty_change
                    )
                    self.item_grid.add_widget(widget)
                    
        except Exception as e:
            print("Error fetching bins:", str(e))

    def handle_qty_change(self, price, qty):
        self.selected_quantities[price] = qty
        self.update_total()

    def reset_to_home(self):
        """Reset cart and reload data (Home behavior)"""
        self.clear_cart()
        self.fetch_bins()

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
            
        self.total_label.text = f"Total: {total_lak:,.0f} LAK"
        self.cart_info.text = f"Items in cart: {total_count}"

    def process_payment(self, *args):
        total_count = sum(self.selected_quantities.values())
        if total_count == 0:
            return
            
        total_lak = sum(price * qty for price, qty in self.selected_quantities.items() if qty > 0)
        
        # SPEED IMPROVEMENT: Skip confirmation dialog and go straight to sale
        # (Using total_lak as received amount by default to skip the input step)
        self.finalize_sale(total_lak, received_override=total_lak)

    def finalize_sale(self, expected_total_lak, received_override=None):
        received_amount = received_override or expected_total_lak
        
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
                'X-App-Access-Key': app.APP_KEY
            }
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 401:
                print("Session expired or logged in elsewhere")
                app.force_logout()
                return

            if response.status_code == 201:
                sale_id = response.json().get('sale_id')
                
                totals = {"lak": total_lak, "thb": total_thb, "bonus": total_bonus}
                shop_name = app.config_data.get('shop_name', 'Bin888')
                
                voucher_screen = self.manager.get_screen('voucher')
                voucher_screen.setup_voucher(shop_name, final_items_for_receipt, sale_id, totals, received=received_amount)
                self.manager.current = 'voucher'
                
                app.printer.print_receipt(shop_name, final_items_for_receipt, total_lak)
                self.clear_cart()
                self.fetch_bins()
            else:
                resp_json = response.json()
                error_msg = resp_json.get('error', response.text)
                print(f"Sale Failed: {error_msg}")
                self.show_error_dialog(error_msg)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"App error during sale process: {str(e)}")

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
        if os.path.exists("last_session.json"):
            os.remove("last_session.json")


class Bin888App(MDApp):
    DEBUG = 1 
    RAISE_ERROR = True
    config_data = {}
    base_url = "https://bm9999.pythonanywhere.com"
    APP_KEY = "Bin888-Premium-Mobile-Key-2024"
    brands_cache = []
    printer = PrinterManager()
    
    _last_activity = datetime.now()

    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        
        # Track activity for Auto-Logout
        Window.bind(on_touch_down=self._reset_activity)
        from kivy.clock import Clock
        Clock.schedule_interval(self._check_idle_timeout, 60) # Check every minute
        
        # Initial brand fetch
        self.fetch_brands()
        
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

    def save_config(self):
        try:
            with open("last_session.json", "w") as f:
                json.dump({
                    "config_data": self.config_data,
                    "base_url": self.base_url
                }, f)
        except: pass

    def load_config(self):
        if os.path.exists("last_session.json"):
            try:
                with open("last_session.json", "r") as f:
                    data = json.load(f)
                    self.config_data = data.get("config_data", {})
                    self.base_url = data.get("base_url", self.base_url)
            except: pass

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

    def fetch_brands(self):
        try:
            # Simple fetch to populate categories/logos
            headers = {'X-App-Access-Key': self.APP_KEY}
            response = requests.get(f"{self.base_url}/api/v1/brands/", headers=headers, timeout=5)
            if response.status_code == 200:
                self.brands_cache = response.json()
                print(f"Loaded {len(self.brands_cache)} brands from server")
        except Exception as e:
            print(f"Could not fetch brands: {e}")

if __name__ == "__main__":
    Bin888App().run()

