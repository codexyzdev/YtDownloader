import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import sys
import traceback
import subprocess # Needed for opening file explorer
import io # To capture print output (though not strictly used now with callbacks)

# --- Global variable for icon ---
# Make sure 'YtDownloaderGUI.ico' exists in the same directory or provide the full path
try:
    # Get base path for PyInstaller data files
    if getattr(sys, 'frozen', False):
        # If running as a bundled exe (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # If running as a normal script
        base_path = os.path.dirname(os.path.abspath(__file__))
    icono = os.path.join(base_path, "YtDownloaderGUI.ico")
    # Check if icon actually exists to prevent error later
    if not os.path.exists(icono):
         print(f"Warning: Icon file not found at {icono}. Using default icon.")
         icono = None # Fallback to default if not found
except NameError:
     # __file__ is not defined, e.g. in interactive interpreter
     print("Warning: Could not determine script path. Icon path might be incorrect.")
     icono = "YtDownloaderGUI.ico" # Try relative path as fallback
     if not os.path.exists(icono):
          print(f"Warning: Icon file not found at {icono}. Using default icon.")
          icono = None


# --- Try importing yt_dlp ---
try:
    import yt_dlp
except ImportError:
    # Attempt to show message box, but tkinter might not be fully ready
    # Printing to console is a safer fallback during early import errors
    print("ERROR: yt-dlp library not found. Please install it using: pip install yt-dlp")
    try:
        root = tk.Tk()
        root.withdraw() # Hide the main window
        messagebox.showerror("Error", "yt-dlp library not found.\nPlease install it using: pip install yt-dlp")
    except tk.TclError:
        pass # If tkinter itself fails
    sys.exit(1) # Exit if yt-dlp is missing

# --- Download Function ---
def download(url, directory, extension, log_callback):
    """Downloads media using yt-dlp with specified format."""

    def log(message):
        """Helper to call the GUI logging function."""
        if log_callback:
            log_callback(message)
        else:
            print(message) # Fallback to console if no callback

    log(f"Starting download process for URL: {url}")
    log(f"Target directory: {directory}")
    log(f"Requested format: {extension}")

    # Create directory if it doesn't exist
    try:
        os.makedirs(directory, exist_ok=True)
        log(f"Ensured directory exists: {directory}")
    except OSError as e:
        log(f"Error creating directory {directory}: {e}")
        return # Stop if directory creation fails

    # --- Options configuration based on extension ---
    ydl_opts = {
        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
        'verbose': False, # Keep False for less GUI clutter
        'progress_hooks': [lambda d: progress_hook(d, log_callback)],
        'cookiefile': 'cookies.txt', # Use cookies if file exists
        'nocheckcertificate': True,  # Use with caution
        'addmetadata': True,
        'logger': YdlpLogger(log_callback),
        'ignoreerrors': True, # Continue on download errors for playlists
        # Consider adding ffmpeg location if not in PATH or packaged
        # 'ffmpeg_location': '/path/to/your/ffmpeg',
    }

    requested_format = extension.lower()

    if requested_format == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
        log("Configured for MP3 download...")

    elif requested_format in ['mp4', 'mkv', 'webm', 'avi', 'flv', 'mov']:
        ydl_opts.update({
            # More robust format selection for wider compatibility
            'format': f'bestvideo[ext={requested_format}]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'merge_output_format': requested_format,
        })
        # If the requested format is mp4, explicitly prefer mp4 container if available
        if requested_format == 'mp4':
             ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'

        log(f"Configured for {requested_format.upper()} video download...")

    else:
        log(f"Warning: Unsupported extension '{extension}'. Defaulting to MKV video download.")
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mkv',
        })

    # --- Log Final Options ---
    log("\n--- yt-dlp Effective Options ---")
    for key, value in ydl_opts.items():
         # Avoid logging potentially sensitive info like cookies content
         if key != 'cookiefile' or not os.path.exists(ydl_opts.get('cookiefile', '')):
              log(f"{key}: {value}")
         else:
              log(f"{key}: {value} (exists)")
    log("------------------------------\n")

    # --- Download process ---
    log("Attempting download...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # The download method can raise DownloadError on failure
            # It might return 0 on success, 1 on error (depends on ignoreerrors)
            result_code = ydl.download([url])
            # Note: With ignoreerrors=True, result_code might be 0 even if some items failed.
            # A more robust check would involve analyzing ydl.extract_info results if needed.
        log("\nDownload process finished.")

    except yt_dlp.utils.DownloadError as e:
        log(f"\n--- Download Error ---")
        log(f"yt-dlp reported an error: {e}")
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
             log("\nHint: This error might be related to FFmpeg.")
             log("Ensure FFmpeg is installed correctly and in your system's PATH,")
             log("or packaged with the application.")
             log("Download FFmpeg from: https://ffmpeg.org/download.html")
        log("----------------------")
        # Re-raise the exception so the calling function knows it failed
        raise e
    except Exception as e:
        log(f"\n--- Unexpected Error During Download ---")
        log(f"An unexpected error occurred in yt-dlp: {e}")
        log("\n--- Traceback ---")
        log(traceback.format_exc())
        log("------------------")
        # Re-raise the exception
        raise e


# --- yt-dlp Progress Hook ---
def progress_hook(d, log_callback):
    """Callback function for yt-dlp progress updates."""
    if d['status'] == 'downloading':
        filename = d.get('filename', 'N/A')
        short_filename = (filename[:50] + '...') if len(filename) > 53 else filename
        percent_str = d.get('_percent_str', 'N/A')
        speed_str = d.get('_speed_str', 'N/A')
        eta_str = d.get('_eta_str', 'N/A')
        log_callback(f"  Downloading: {short_filename} | {percent_str} | Speed: {speed_str} | ETA: {eta_str}")
    elif d['status'] == 'finished':
        filename = d.get('filename', 'N/A')
        total_bytes_str = d.get('_total_bytes_str', 'N/A')
        log_callback(f"  Finished downloading: {filename} ({total_bytes_str})")
    elif d['status'] == 'error':
        filename = d.get('filename', 'N/A')
        # This might be redundant if ignoreerrors is False, as it would raise DownloadError
        log_callback(f"  ERROR downloading: {filename}")
    elif d['status'] == 'processing':
         processor = d.get('processor')
         log_callback(f"  Processing: Running {processor if processor else 'postprocessor'}...")


# --- Custom Logger for yt-dlp ---
class YdlpLogger:
    """Routes yt-dlp's internal logs to our GUI."""
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def debug(self, msg):
        # Clean up debug messages a bit for the log
        if msg.startswith('[debug] '):
            msg = msg[len('[debug] '):]
        # Uncomment line below to show debug messages in GUI log (can be very verbose)
        # self.log_callback(f"[ydl-debug] {msg}")
        pass # Ignore debug messages by default

    def info(self, msg):
        # Route general info messages (often includes download start/end)
        # Exclude messages handled by progress hook to avoid duplicates
         if not msg.startswith('[download]'):
              self.log_callback(f"[ydl-info] {msg}")

    def warning(self, msg):
        self.log_callback(f"[ydl-warning] {msg}")

    def error(self, msg):
        self.log_callback(f"[ydl-error] {msg}")


# --- Tkinter GUI Application ---
class DownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Yt Downloader GUI") # Changed title
        master.geometry("700x550") # Slightly increased height for log visibility

        # Set Icon if available
        if icono:
            try:
                master.iconbitmap(icono)
            except tk.TclError as e:
                 print(f"Warning: Could not set icon '{icono}'. Error: {e}")
                 # Optionally show a messagebox warning
                 # messagebox.showwarning("Icon Error", f"Could not load icon file:\n{icono}\n\nError: {e}")

        # --- Configure Grid ---
        master.columnconfigure(1, weight=1)
        master.rowconfigure(4, weight=1) # Allow log area row to expand

        # --- Widgets ---
        # URL
        tk.Label(master, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = tk.Entry(master, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW) # Span 2 cols

        # Directory
        tk.Label(master, text="Directory:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_entry = tk.Entry(master, width=50)
        self.dir_entry.grid(row=1, column=1, padx=(5,0), pady=5, sticky=tk.EW)
        self.browse_button = ttk.Button(master, text="Browse...", command=self.browse_directory)
        self.browse_button.grid(row=1, column=2, padx=(2,5), pady=5, sticky=tk.W)

        # Extension/Format
        tk.Label(master, text="Format:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.extension_var = tk.StringVar()
        self.extension_combo = ttk.Combobox(master, textvariable=self.extension_var,
                                            values=['mp3', 'mp4', 'mkv', 'webm', 'avi', 'flv', 'mov'],
                                            state='readonly', width=10) # Added width
        self.extension_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W) # Use W align
        self.extension_combo.set('mp4') # Default value

        # Download Button
        self.download_button = ttk.Button(master, text="Download", command=self.start_download_thread)
        self.download_button.grid(row=3, column=0, columnspan=3, padx=5, pady=10)

        # Log Area
        tk.Label(master, text="Log Output:").grid(row=4, column=0, padx=5, pady=(5,0), sticky=tk.NW)
        self.log_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, height=18, width=80, relief=tk.SUNKEN, borderwidth=1)
        self.log_area.grid(row=4, column=1, columnspan=2, padx=5, pady=(5,5), sticky=tk.NSEW)
        self.log_area.configure(state='disabled')

    def browse_directory(self):
        """Opens a directory selection dialog."""
        # Optionally suggest the current directory entry as initialdir
        initial_dir = self.dir_entry.get()
        if not os.path.isdir(initial_dir):
             initial_dir = os.path.expanduser("~") # Default to home dir if invalid

        directory = filedialog.askdirectory(initialdir=initial_dir)
        if directory: # Only update if a directory was selected
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.log_message(f"Selected directory: {directory}")

    def log_message(self, message):
        """Appends a message to the log area in a thread-safe way."""
        def append_log():
            if self.log_area.winfo_exists(): # Check if widget still exists
                self.log_area.configure(state='normal') # Enable writing
                self.log_area.insert(tk.END, message + "\n")
                self.log_area.configure(state='disabled') # Disable writing
                self.log_area.see(tk.END) # Scroll to the end
        try:
            # `after` schedules the function `append_log` to be called by the Tkinter main loop
            self.master.after(0, append_log)
        except tk.TclError:
             # Handle case where the window might be destroyed while logging
             print(f"Log (window closed?): {message}")


    def start_download_thread(self):
        """Gets inputs, validates, and starts the download in a new thread."""
        url = self.url_entry.get().strip()
        directory = self.dir_entry.get().strip()
        extension = self.extension_var.get()

        # --- Input Validation ---
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        if not directory:
            messagebox.showerror("Error", "Please select a download directory.")
            return
        if not extension:
            messagebox.showerror("Error", "Please select a download format.")
            return
        # Basic check if directory seems valid (exists or can be created)
        if not os.path.isdir(directory) and not os.access(os.path.dirname(directory) or '.', os.W_OK):
            messagebox.showerror("Error", f"Cannot write to directory:\n{directory}\nCheck permissions or path.")
            return


        # --- Disable button and start thread ---
        self.download_button.config(state=tk.DISABLED)
        # Clear log area for new download (optional)
        # self.log_area.configure(state='normal')
        # self.log_area.delete('1.0', tk.END)
        # self.log_area.configure(state='disabled')
        self.log_message("-" * 20 + " Starting Download " + "-" * 20)

        # Create and start the download thread
        download_thread = threading.Thread(
            target=self.run_download,
            args=(url, directory, extension),
            daemon=True
        )
        download_thread.start()

    def run_download(self, url, directory, extension):
        """Wrapper function to run the download and re-enable the button."""
        download_successful = False # Flag to track if download completed without major exceptions
        try:
            # Call the core download function, passing our GUI logger
            download(url, directory, extension, self.log_message)
            # If download() finished without raising an exception, mark as generally successful
            # Note: Individual item errors might still occur if ignoreerrors=True
            download_successful = True
            self.log_message("-" * 20 + " Download Attempt Finished " + "-" * 20)

            # --- Open directory in file explorer on success ---
            if download_successful:
                self.log_message(f"Attempting to open download directory: {directory}")
                try:
                    # Use os.path.realpath to ensure the path is absolute and resolved
                    abs_directory_path = os.path.realpath(directory)

                    if sys.platform == "win32":
                        # Use explorer.exe for more reliability on Windows, handles spaces well
                        # subprocess.run(['explorer', abs_directory_path], check=False)
                        # os.startfile is simpler if it works reliably for your cases
                        os.startfile(abs_directory_path)
                    elif sys.platform == "darwin": # macOS
                        subprocess.run(["open", abs_directory_path], check=False)
                    else: # Linux and other Unix-like systems
                        subprocess.run(["xdg-open", abs_directory_path], check=False)
                    self.log_message(f"Successfully requested to open directory: {abs_directory_path}")
                except FileNotFoundError:
                     self.log_message(f"Error: Could not find command (startfile, open, xdg-open) to open file explorer for platform {sys.platform}.")
                except Exception as open_err:
                     self.log_message(f"Error trying to open directory '{abs_directory_path}': {open_err}")
            # --- End of open directory code ---

        except yt_dlp.utils.DownloadError:
            # Specifically catch DownloadError which 'download' function might raise
            # Error message already logged inside 'download' function's except block
            self.log_message("-" * 20 + " Download Failed (DownloadError) " + "-" * 20)
            # download_successful remains False
        except Exception as e:
            # Catch any unexpected error in the download function itself or during setup
            self.log_message(f"\n--- Critical Error during download execution ---")
            self.log_message(f"Error: {e}")
            self.log_message("\n--- Traceback ---")
            # Ensure traceback is logged via the GUI logger
            tb_lines = traceback.format_exc().splitlines()
            for line in tb_lines:
                 self.log_message(line)
            self.log_message("------------------------------------------------")
            # download_successful remains False
        finally:
            # --- Re-enable button in the main thread ---
            # Use `after` to ensure this runs in the Tkinter main loop
            self.master.after(0, lambda: self.download_button.config(state=tk.NORMAL))


# --- Main Execution ---
if __name__ == "__main__":
    # Check for FFmpeg (optional but good practice on startup)
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")

    if ffmpeg_path is None or ffprobe_path is None:
         warning_message = ("Warning: FFmpeg or FFprobe not found in system PATH.\n\n"
                           "yt-dlp may not be able to merge formats (like MP4/MKV) "
                           "or convert audio (like MP3).\n\n"
                           "Please download from: https://ffmpeg.org/download.html\n"
                           "and ensure ffmpeg.exe and ffprobe.exe are in your system's PATH "
                           "or packaged with this application.")
         print(warning_message) # Print to console regardless
         # Show warning popup only after root window is potentially created
         # Use a flag or schedule it after mainloop starts if needed,
         # but printing is usually sufficient for startup checks.
         # messagebox.showwarning("FFmpeg Missing", warning_message) # Can cause issues if tk isn't fully ready

    root = tk.Tk()
    # Set DPI awareness for better scaling on high-res displays (Windows)
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1) # Try basic awareness
        except Exception as dpi_e:
             print(f"Note: Could not set DPI awareness. GUI might appear blurry on high-res screens. Error: {dpi_e}")

    app = DownloaderApp(root)
    root.mainloop()