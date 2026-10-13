import os
import subprocess
import time

import pyperclip
import pytesseract
from PIL import ImageGrab
from pynput import keyboard
from winotify import Notification, audio


TEMP_PATH = os.path.join(os.environ.get("TEMP", "/tmp"), "ocr_screenshot.png")
COMBINATION = {keyboard.Key.ctrl, keyboard.KeyCode.from_char("k")}
current_keys = set()


def capture_screen_region():
    """Opens Windows screen snipping and waits for the selected image."""
    subprocess.Popen(["explorer.exe", "ms-screenclip:"])

    # Wait for the user to select a region and for Windows to place it on the clipboard.
    for _ in range(300):
        image = ImageGrab.grabclipboard()
        if image is not None and hasattr(image, "save"):
            image.save(TEMP_PATH)
            return True
        time.sleep(0.1)

    return False


def run_ocr(image_path):
    """Uses Tesseract OCR to read text from the selected image."""
    return pytesseract.image_to_string(image_path, config="--psm 6")


def clean_text(text):
    """Cleans common OCR punctuation issues."""
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("“", '"').replace("”", '"')
    return text.strip()


def notify(message):
    toast = Notification(
        app_id="Math OCR",
        title="Text Copied",
        msg=message,
    )
    toast.set_audio(audio.Default, loop=False)
    toast.show()


def process_ocr():
    if not capture_screen_region():
        print("No screenshot was selected.")
        return

    try:
        raw_text = run_ocr(TEMP_PATH)
        final_text = clean_text(raw_text)

        if final_text:
            pyperclip.copy(final_text)
            display_msg = final_text[:150] + ("..." if len(final_text) > 150 else "")
            notify(display_msg)
            print(f"Copied:\n{final_text}")
        else:
            notify("No text was detected.")
            print("No text was detected.")
    except Exception as error:
        print(f"Error: {error}")
    finally:
        if os.path.exists(TEMP_PATH):
            os.remove(TEMP_PATH)


def on_press(key):
    if key in COMBINATION:
        current_keys.add(key)
        if all(key_item in current_keys for key_item in COMBINATION):
            process_ocr()


def on_release(key):
    current_keys.discard(key)


print("Math OCR for Windows is ready!")
print("Press Ctrl + K, then select a region of the screen.")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
