# main.py
import tkinter as tk
import sys
import os
import shutil # For ffmpeg check

# Import the GUI application class
from gui import DownloaderApp, get_resource_path

def check_ffmpeg():
    """Checks if ffmpeg and ffprobe are accessible."""
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")

    if not ffmpeg_path or not ffprobe_path:
        warning_message = (
            "Warning: FFmpeg/FFprobe not found in system PATH.\n\n"
            "Merging formats (MP4/MKV) and audio conversion (MP3) "
            "might fail.\n\n"
            "Download from: https://ffmpeg.org/download.html\n"
            "Ensure ffmpeg.exe/ffprobe.exe are in PATH or packaged."
        )
        print(warning_message)
        # Consider showing a non-blocking warning in the GUI later if needed
        return False
    else:
        print(f"FFmpeg found at: {ffmpeg_path}")
        print(f"FFprobe found at: {ffprobe_path}")
        return True

def set_dpi_awareness():
    """Sets DPI awareness on Windows for better scaling."""
    if sys.platform == "win32":
        try:
            from ctypes import windll
            # Values: 0=unaware, 1=System Aware, 2=Per-Monitor Aware
            # System aware (1) is usually sufficient and safer
            windll.shcore.SetProcessDpiAwareness(1)
            print("Set DPI awareness to System Aware.")
        except ImportError:
            print("ctypes not available, cannot set DPI awareness.")
        except AttributeError:
             print("shcore.SetProcessDpiAwareness not available (older Windows?), cannot set DPI awareness.")
        except Exception as e:
            print(f"Note: Could not set DPI awareness. Error: {e}")

if __name__ == "__main__":
    print("Starting YT Downloader...")

    # Perform pre-checks
    check_ffmpeg()

    # Setup Tkinter root window
    root = tk.Tk()

    # Set DPI awareness before creating GUI elements
    set_dpi_awareness()

    # Create and run the application
    app = DownloaderApp(root)
    root.mainloop()

    print("Application finished.")