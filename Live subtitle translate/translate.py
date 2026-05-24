import time
import threading
import tkinter as tk

from PIL import ImageGrab

from deep_translator import GoogleTranslator

# Windows OCR
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter


SCAN_INTERVAL = 0.1

selected_region = None
last_text = ""


# =========================
# WINDOWS OCR
# =========================

async def recognize_pil_image(pil_image):
    import io

    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    data = buffer.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(data)

    await writer.store_async()
    writer.detach_stream()

    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    engine = OcrEngine.try_create_from_language(Language("zh-Hans"))

    result = await engine.recognize_async(bitmap)

    return result.text.strip()


# =========================
# TK OVERLAY
# =========================

root = tk.Tk()
root.withdraw()

overlay = tk.Toplevel()
overlay.withdraw()

overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-alpha", 0.92)

label = tk.Label(
    overlay,
    text="",
    bg="black",
    fg="white",
    font=("Segoe UI", 14),
    justify="left",
    padx=10,
    pady=8,
    wraplength=500
)

label.pack()


def update_overlay(text):
    global selected_region

    label.config(text=text)

    x1, y1, x2, y2 = selected_region

    overlay.geometry(f"+{x2 + 20}+{y1}")

    overlay.deiconify()


# =========================
# REGION SELECTOR
# =========================

class Selector:
    def __init__(self):
        self.start_x = 0
        self.start_y = 0

        self.win = tk.Toplevel()
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-alpha", 0.25)
        self.win.configure(bg="gray")
        self.win.attributes("-topmost", True)

        self.canvas = tk.Canvas(self.win, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="red",
            width=2
        )

    def on_drag(self, event):
        self.canvas.coords(
            self.rect,
            self.start_x,
            self.start_y,
            event.x,
            event.y
        )

    def on_release(self, event):
        global selected_region

        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        selected_region = (x1, y1, x2, y2)

        self.win.destroy()


# =========================
# OCR LOOP
# =========================

def worker():
    global last_text

    import asyncio

    translator = GoogleTranslator(source='zh-CN', target='en')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            if selected_region:
                img = ImageGrab.grab(bbox=selected_region)

                text = loop.run_until_complete(
                    recognize_pil_image(img)
                )

                text = text.strip()

                if not text:
                    time.sleep(SCAN_INTERVAL)
                    continue

                if text == last_text:
                    time.sleep(SCAN_INTERVAL)
                    continue

                last_text = text

                translated = translator.translate(text)

                update_overlay(translated)

        except Exception as e:
            update_overlay(str(e))

        time.sleep(SCAN_INTERVAL)


# =========================
# START
# =========================

print("Select subtitle area...")

Selector()

threading.Thread(target=worker, daemon=True).start()

root.mainloop()
