import os
import sys
import subprocess
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import serial.tools.list_ports

# ===========================
# PyInstaller Path Handling
# ===========================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def find_avrdude():
    return resource_path("avrdude.exe")

def get_avrdude_conf():
    return resource_path("avrdude.conf")

def detect_arduino_ports():
    ports = []
    for port in serial.tools.list_ports.comports():
        desc = port.description.lower()
        hwid = port.hwid.lower()
        if any(kw in desc or kw in hwid for kw in [
            'ch340', 'ft232', 'arduino', 'usb serial', 'cdc', 'atmega', 'usb2.0-serial', 'leonardo', 'promicro', 'mega'
        ]):
            ports.append((port.description, port.device))
    return ports

def trigger_1200_baud_reset(port):
    try:
        ser = serial.Serial(port, 1200)
        ser.close()
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Failed to perform 1200 baud reset: {e}")

# ===========================
# Main Application
# ===========================
class ArduinoHexUploaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Arduino HEX Flasher 🛠️")
        self.geometry("740x680")
        self.resizable(False, False)

        # Board definitions: (display_name, key, image_file)
        self.boards = [
            ("Arduino Uno", "uno", "arduino_uno.png"),
            ("Arduino Nano", "nano", "arduino_nano.png"),
            ("Arduino Leonardo", "leonardo", "arduino_leonardo.png"),
            ("Arduino Pro Micro", "promicro", "arduino_promicro.png"),
            ("Arduino Mega 2560", "mega", "arduino_mega.png"),
        ]

        self.board_key = ctk.StringVar(value="uno")  # stores key, e.g., "uno"
        self.hex_path = ctk.StringVar()
        self.port = ctk.StringVar()

        self.load_images()
        self.create_widgets()
        self.update_board_image()

    def load_images(self):
        self.photos = {}
        size = (200, 130)
        for _, key, img_file in self.boards:
            path = resource_path(img_file)
            if os.path.isfile(path):
                try:
                    img = Image.open(path)
                    self.photos[key] = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                except Exception as e:
                    print(f"⚠️ Error loading {path}: {e}")

    def create_widgets(self):
        title_label = ctk.CTkLabel(self, text="Arduino HEX Flasher", font=ctk.CTkFont(size=22, weight="bold"))
        title_label.pack(pady=(15, 10))

        # === Arduino Board Selection ===
        board_frame = ctk.CTkFrame(self, fg_color="transparent")
        board_frame.pack(pady=5)

        ctk.CTkLabel(board_frame, text="Select Arduino board:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)

        # Create list of names to display
        board_names = [name for name, _, _ in self.boards]
        self.board_combo = ctk.CTkComboBox(
            board_frame,
            values=board_names,
            command=self.on_board_select,  # called on change
            width=300,
            state="readonly"
        )
        self.board_combo.pack(pady=5)
        self.board_combo.set("Arduino Uno")  # default

        # Image
        self.image_label = ctk.CTkLabel(board_frame, text="")
        self.image_label.pack(pady=10)

        # === COM Port ===
        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(port_frame, text="COM Port:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=5)
        com_entry_frame = ctk.CTkFrame(port_frame, fg_color="transparent")
        com_entry_frame.pack(fill="x", pady=5)
        self.port_combo = ctk.CTkComboBox(com_entry_frame, variable=self.port, width=420, state="readonly")
        self.port_combo.pack(side="left", padx=(0, 10))
        ctk.CTkButton(com_entry_frame, text="🔍 Detect", command=self.detect_ports, width=90).pack(side="left")

        # === HEX File ===
        hex_frame = ctk.CTkFrame(self, fg_color="transparent")
        hex_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(hex_frame, text="HEX file:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=5)
        file_entry_frame = ctk.CTkFrame(hex_frame, fg_color="transparent")
        file_entry_frame.pack(fill="x", pady=5)
        ctk.CTkEntry(file_entry_frame, textvariable=self.hex_path, width=520, state="readonly").pack(side="left", padx=(0, 10))
        ctk.CTkButton(file_entry_frame, text="📂 Browse", command=self.browse_hex, width=100).pack(side="left")

        # === Upload Button ===
        ctk.CTkButton(self, text="🚀 Upload to Arduino", command=self.upload, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)

        # === Logs ===
        ctk.CTkLabel(self, text="Logs:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20)
        self.log_text = ctk.CTkTextbox(self, height=180, width=700, font=ctk.CTkFont(family="Courier", size=10))
        self.log_text.pack(padx=20, pady=(5, 15))
        self.log_text.configure(state="disabled")

    def on_board_select(self, choice):
        """Called when ComboBox selection changes."""
        # Find key for selected name
        for name, key, _ in self.boards:
            if name == choice:
                self.board_key.set(key)
                break
        self.update_board_image()

    def update_board_image(self):
        key = self.board_key.get()
        img = self.photos.get(key)
        if img:
            self.image_label.configure(image=img, text="")
        else:
            self.image_label.configure(image=None, text="⚠️ No image")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update()

    def detect_ports(self):
        self.log("🔍 Detecting Arduino ports...")
        ports = detect_arduino_ports()
        if ports:
            self.port_combo.configure(values=[p[0] for p in ports])
            self.port.set(ports[0][0])
            self.log(f"✅ Found {len(ports)} possible Arduino devices.")
        else:
            self.port_combo.configure(values=[])
            self.port.set("")
            self.log("⚠️ No Arduino devices found.")

    def browse_hex(self):
        file = filedialog.askopenfilename(title="Select HEX file", filetypes=[("Intel HEX", "*.hex")])
        if file:
            self.hex_path.set(file)

    def run_avrdude(self, mcu, programmer, baud, port_device, hex_file):
        avrdude = find_avrdude()
        conf = get_avrdude_conf()
        if not os.path.isfile(avrdude):
            raise Exception("avrdude.exe not found!")
        if not os.path.isfile(conf):
            raise Exception("avrdude.conf not found!")

        cmd = [
            avrdude,
            "-C", conf,
            "-v",
            "-p", mcu,
            "-c", programmer,
            "-P", port_device,
            "-b", str(baud),
            "-D",
            "-U", f"flash:w:{hex_file}:i"
        ]

        self.log(f"🔧 Command: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                line = process.stdout.readline()
                if line == "" and process.poll() is not None:
                    break
                if line:
                    self.log(line.strip())
            return process.returncode == 0
        except Exception as e:
            self.log(f"💥 Error: {e}")
            return False

    def upload(self):
        if not self.hex_path.get():
            messagebox.showerror("Error", "Select a HEX file!")
            return
        if not os.path.isfile(self.hex_path.get()):
            messagebox.showerror("Error", "HEX file does not exist!")
            return
        if not self.port.get():
            messagebox.showerror("Error", "Select a COM port!")
            return

        port_device = None
        for desc, dev in detect_arduino_ports():
            if desc == self.port.get():
                port_device = dev
                break
        if not port_device:
            port_device = self.port.get().split('(')[-1].rstrip(')')

        board = self.board_key.get()
        hex_file = self.hex_path.get()

        if board == "uno":
            success = self.run_avrdude("atmega328p", "arduino", 115200, port_device, hex_file)
            self.show_result(success, "Firmware uploaded to Arduino Uno!")

        elif board == "nano":
            self.log("\n➡️ Attempt 1/2: old bootloader (57600 baud)...")
            if self.run_avrdude("atmega328p", "arduino", 57600, port_device, hex_file):
                self.show_result(True, "Firmware uploaded to Arduino Nano (old bootloader)!")
                return
            self.log("➡️ Attempt 2/2: new bootloader (115200 baud)...")
            if self.run_avrdude("atmega328p", "arduino", 115200, port_device, hex_file):
                self.show_result(True, "Firmware uploaded to Arduino Nano (new bootloader)!")
            else:
                self.show_result(False, "Failed to upload to Arduino Nano.")

        elif board in ("leonardo", "promicro"):
            self.log("🔄 Forcing 1200 baud reset...")
            trigger_1200_baud_reset(port_device)
            self.log("⏳ Waiting for port after reset...")
            time.sleep(2)
            success = self.run_avrdude("atmega32u4", "avr109", 57600, port_device, hex_file)
            name = "Leonardo" if board == "leonardo" else "Pro Micro"
            self.show_result(success, f"Firmware uploaded to Arduino {name}!")

        elif board == "mega":
            success = self.run_avrdude("atmega2560", "wiring", 115200, port_device, hex_file)
            self.show_result(success, "Firmware uploaded to Arduino Mega 2560!")

    def show_result(self, success, message):
        if success:
            self.log("\n✅ Success!")
            messagebox.showinfo("Success", message)
        else:
            self.log("\n❌ Failure!")
            messagebox.showerror("Error", message)

if __name__ == "__main__":
    app = ArduinoHexUploaderApp()
    app.mainloop()
