# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import sys
import traceback
import subprocess
import re # For basic URL validation

# Import logic and config modules
from downloader import Downloader
import config_manager

# --- Helper function for icon path ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError: # Use AttributeError for _MEIPASS check
        # Not running as PyInstaller bundle, use script directory
        base_path = os.path.dirname(os.path.abspath(__file__))
    except Exception as e:
        # Fallback or log error if needed
        print(f"Error getting base path: {e}")
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- Tkinter GUI Application ---
class DownloaderApp:
    """Main application class for the YT Downloader GUI."""

    def __init__(self, master):
        """Initialize the GUI application."""
        self.master = master
        self.downloader = Downloader() # Instantiate the downloader logic
        self.settings = config_manager.load_settings() # Load saved settings

        # --- Window Setup ---
        master.title("YT Downloader")
        # Adjusted geometry slightly as progress bar row is removed
        master.geometry("750x580")

        # Set Icon
        self._set_icon()

        # Configure closing behavior
        master.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Theming ---
        style = ttk.Style()
        available_themes = style.theme_names()
        preferred_themes = ['vista', 'clam', 'alt', 'default']
        theme_found = False
        for theme in preferred_themes:
            if theme in available_themes:
                try:
                    style.theme_use(theme)
                    print(f"Using theme: {theme}")
                    theme_found = True
                    break
                except tk.TclError:
                    continue
        if not theme_found:
             print("Using default theme.")


        # --- Grid Configuration ---
        master.columnconfigure(1, weight=1) # Column for entries/combos expands
        # Row 5 will now contain the log area and should expand
        master.rowconfigure(5, weight=1)

        # --- Widgets ---
        # URL Input
        tk.Label(master, text="URL:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(master, width=70)
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.url_entry.bind("<KeyRelease>", self._validate_url_visual)

        # Directory Input
        tk.Label(master, text="Directory:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.dir_entry = ttk.Entry(master, width=60)
        self.dir_entry.grid(row=1, column=1, padx=(5,0), pady=5, sticky=tk.EW)
        last_dir = self.settings.get(config_manager.LAST_DIR_KEY)
        if last_dir and os.path.isdir(last_dir):
            self.dir_entry.insert(0, last_dir)
        else:
             default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
             if not os.path.exists(default_download_dir):
                 try:
                     os.makedirs(default_download_dir, exist_ok=True)
                     print(f"Created default directory: {default_download_dir}")
                 except OSError:
                     print(f"Warning: Could not create default Downloads directory. Falling back to home.")
                     default_download_dir = os.path.expanduser("~")
             self.dir_entry.insert(0, default_download_dir)

        self.browse_button = ttk.Button(master, text="Browse...", command=self._browse_directory)
        self.browse_button.grid(row=1, column=2, padx=(2, 10), pady=5, sticky=tk.W)

        # Format Selection
        tk.Label(master, text="Format:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.extension_var = tk.StringVar()
        format_options = ['mp4', 'mkv', 'mp3']
        self.extension_combo = ttk.Combobox(master, textvariable=self.extension_var,
                                            values=format_options,
                                            state='readonly', width=10)
        self.extension_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.extension_combo.set('mp4')

        # Download Button
        self.download_button = ttk.Button(master, text="Download", command=self._start_download_thread)
        self.download_button.grid(row=3, column=0, columnspan=3, padx=10, pady=15)

        # Status Label (Progress Bar Removed)
        tk.Label(master, text="Status:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.progress_label = ttk.Label(master, text="Waiting for you", anchor=tk.W)
        # Status label is now in row 4
        self.progress_label.grid(row=4, column=1, columnspan=3, padx=10, pady=(5,5), sticky=tk.EW)

        # --- Progress Bar REMOVED ---
        # self.progress_bar = ttk.Progressbar(...)
        # self.progress_bar.grid(...)

        # Log Area
        tk.Label(master, text="Log Output:").grid(row=5, column=0, padx=10, pady=(5,0), sticky=tk.NW) # Log area moved to row 5
        self.log_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, height=15, relief=tk.SUNKEN, borderwidth=1, font=("Courier New", 9))
        # Log area now in row 5
        self.log_area.grid(row=5, column=1, columnspan=2, padx=5, pady=(5,10), sticky=tk.NSEW)
        self.log_area.configure(state='disabled')

    def _set_icon(self):
        """Sets the application window icon."""
        try:
            icon_name = "YtDownloaderGUI.ico"
            if sys.platform == "darwin": icon_name = "YtDownloaderGUI.icns"
            elif sys.platform.startswith("linux"): icon_name = "YtDownloaderGUI.png"

            icon_path = get_resource_path(icon_name)
            if os.path.exists(icon_path):
                if sys.platform == "win32":
                     self.master.iconbitmap(icon_path)
                else:
                    try:
                        img = tk.PhotoImage(file=icon_path)
                        self.master.iconphoto(True, img)
                    except tk.TclError as photo_error:
                         print(f"Warning: Could not load icon '{icon_path}' with PhotoImage. Error: {photo_error}")
            else:
                print(f"Warning: Icon file not found at {icon_path}")
        except tk.TclError as e:
            print(f"Warning: Could not set icon. TclError: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error setting icon. Error: {e}")


    def _validate_url_visual(self, event=None):
        """Provides basic visual feedback on URL entry."""
        url = self.url_entry.get().strip()
        if re.match(r'^https?://\S+$', url):
             self.url_entry.config(foreground='')
        elif url == "":
             self.url_entry.config(foreground='')
        else:
             self.url_entry.config(foreground='red')

    def _browse_directory(self):
        """Opens directory selection dialog."""
        initial_dir = self.dir_entry.get()
        if not initial_dir or not os.path.isdir(initial_dir):
            initial_dir = self.settings.get(config_manager.LAST_DIR_KEY)
            if not initial_dir or not os.path.isdir(initial_dir):
                initial_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.isdir(initial_dir):
                     initial_dir = os.path.expanduser("~")

        directory = filedialog.askdirectory(initialdir=initial_dir,
                                            title="Select Download Directory",
                                            parent=self.master)
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self._log_message('info', f"Selected directory: {directory}")

    def _log_message(self, level, message):
        """Thread-safe method to append messages to the log area."""
        prefix = f"[{level.upper()}] ".ljust(10) if level != 'info' else "[INFO]    ".ljust(10)
        full_message = f"{prefix}{message}"

        def append_log():
            if self.log_area.winfo_exists():
                current_state = self.log_area.cget('state')
                self.log_area.configure(state='normal')
                self.log_area.insert(tk.END, full_message + "\n")
                self.log_area.configure(state=current_state)
                self.log_area.see(tk.END)
        try:
            if self.master.winfo_exists():
                self.master.after(0, append_log)
            else:
                 print(f"Log (window closed): {full_message}")
        except tk.TclError:
             print(f"Log (TclError, window closed?): {full_message}")
        except Exception as e:
            print(f"Error logging message: {e}")
            print(f"Log message was: {full_message}")


    def _update_progress(self, percent, message, status, filename):
        """Thread-safe method to update the status label (Progress Bar Removed)."""
        # 'percent' argument is kept for compatibility with downloader module, but ignored here.
        def update_gui():
            # Check if label widget exists before updating
            if not self.progress_label.winfo_exists():
                return

            # --- Progress Bar Logic Removed ---

            # --- Update Status Label ---
            is_final_state = (status == 'finished' or status == 'error')
            status_text = f"{status.capitalize()}"
            if message:
                status_text += f" - {message}"
            if filename and not is_final_state and status != 'idle':
                 max_len = 45
                 display_filename = os.path.basename(filename)
                 if len(display_filename) > max_len:
                      display_filename = display_filename[:max_len-3] + '...'
                 if status in ['downloading', 'processing']:
                      status_text = f"{status.capitalize()} [{display_filename}] - {message}"

            self.progress_label.config(text=status_text)

        try:
            # Schedule the GUI update in the main thread
            if self.master.winfo_exists():
                 self.master.after(0, update_gui)
            else:
                 print("Status Update (window closed)")
        except tk.TclError:
             print("Status Update (TclError, window closed?)")
        except Exception as e:
            print(f"Error updating status label: {e}")


    def _start_download_thread(self):
        """Validates inputs and starts the download in a background thread."""
        url = self.url_entry.get().strip()
        directory = self.dir_entry.get().strip()
        extension = self.extension_var.get()

        # --- Input Validation ---
        if not url or not re.match(r'^https?://\S+$', url):
            messagebox.showerror("Invalid Input", "Please enter a valid URL starting with http:// or https://.", parent=self.master)
            self.url_entry.focus(); return
        if not directory:
            messagebox.showerror("Invalid Input", "Please select or enter a download directory.", parent=self.master)
            self.dir_entry.focus(); return
        if not extension:
            messagebox.showerror("Invalid Input", "Please select a download format.", parent=self.master)
            self.extension_combo.focus(); return

        # --- Directory Writability Check ---
        try:
            target_dir = os.path.abspath(directory)
            if os.path.exists(target_dir):
                if not os.path.isdir(target_dir): raise OSError(f"Path exists but is not a directory: '{target_dir}'")
                if not os.access(target_dir, os.W_OK): raise OSError(f"Permission denied: Directory '{target_dir}' is not writable.")
            else:
                parent_dir = os.path.dirname(target_dir)
                if not parent_dir: parent_dir = os.getcwd()
                if not os.path.isdir(parent_dir): raise OSError(f"Parent directory does not exist: '{parent_dir}'")
                if not os.access(parent_dir, os.W_OK): raise OSError(f"Permission denied: Cannot create directory, parent '{parent_dir}' is not writable.")
        except OSError as e:
             messagebox.showerror("Directory Error", f"Directory issue:\n{e}", parent=self.master); return
        except Exception as e:
             messagebox.showerror("Directory Error", f"Unexpected error checking directory '{directory}':\n{e}", parent=self.master); return

        # --- Start Thread ---
        self.download_button.config(state=tk.DISABLED)

        # --- Progress Bar Reset Logic Removed ---

        # Update status label before starting thread
        self._update_progress(None, "Preparing...", "starting", None)

        # Log messages
        self._log_message('info', "-" * 25 + " Download Initiated " + "-" * 25)
        self._log_message('info', f"Requested URL: {url}")
        self._log_message('info', f"Target Directory: {target_dir}")
        self._log_message('info', f"Requested Format: {extension}")

        # Create and start the background thread
        thread = threading.Thread(
            target=self._run_download_wrapper,
            args=(url, target_dir, extension),
            daemon=True
        )
        thread.start()

    def _run_download_wrapper(self, url, directory, extension):
        """
        Wrapper function executed in the background thread.
        Calls the downloader logic and handles GUI updates upon completion.
        """
        overall_success = False
        final_status = "error"
        final_message = "An unexpected error occurred in the download thread."
        try:
            # Execute the actual download logic from the downloader module
            # Note: _update_progress now ignores the 'percent' value it receives
            overall_success = self.downloader.download_media(
                url,
                directory,
                extension,
                self._update_progress, # Pass GUI update callback
                self._log_message    # Pass GUI logging callback
            )

            # --- Determine final status based on success ---
            if overall_success:
                 self._log_message('info',"Download process completed (check logs for details on individual files).")
                 final_status = "finished"
                 final_message = "Download complete."
                 self._open_directory_safely(directory)
            else:
                 self._log_message('error', "Download process failed or encountered critical errors. See log.")
                 final_status = "error"
                 final_message = "Download failed. See log."

        except Exception as e:
            self._log_message('error', f"CRITICAL ERROR in GUI download thread wrapper: {e}")
            self._log_message('error', f"Traceback:\n{traceback.format_exc()}")
            final_status = "error"
            final_message = "Critical internal error during download."
            overall_success = False

        finally:
            # --- Final GUI Updates (Scheduled via 'after' for thread safety) ---
            final_percent = None # Percent is no longer used by _update_progress
            if self.master.winfo_exists():
                # Update status label to final state
                self.master.after(0, lambda: self._update_progress(final_percent, final_message, final_status, None))
                # Re-enable the download button
                self.master.after(0, lambda: self.download_button.config(state=tk.NORMAL) if self.download_button.winfo_exists() else None)
                # Automatic reset to Idle is removed as requested
            else:
                 print("Download finished, but main window no longer exists.")


    def _open_directory_safely(self, directory):
        """Opens the specified directory in the system's file explorer."""
        try:
            abs_path = directory
            if not os.path.isdir(abs_path):
                 self._log_message('warning', f"Directory '{abs_path}' not found after download. Cannot open.")
                 if self.master.winfo_exists(): messagebox.showwarning("Cannot Open Folder", f"The download directory was not found:\n{abs_path}", parent=self.master)
                 return

            self._log_message('info', f"Attempting to open directory: {abs_path}")
            if sys.platform == "win32": os.startfile(abs_path)
            elif sys.platform == "darwin": subprocess.run(["open", abs_path], check=True)
            else: subprocess.run(["xdg-open", abs_path], check=True)

        except FileNotFoundError:
             self._log_message('error', f"Cannot open directory. Command not found for platform '{sys.platform}'.")
             if self.master.winfo_exists(): messagebox.showerror("Cannot Open Folder", f"Could not find the necessary command to open the folder automatically on your system.\n\nPlease navigate to:\n{abs_path}", parent=self.master)
        except subprocess.CalledProcessError as e:
             self._log_message('error', f"Command to open directory failed with code {e.returncode}: {e}")
             if self.master.winfo_exists(): messagebox.showerror("Cannot Open Folder", f"The command to open the folder failed.\nError: {e}\n\nPlease navigate to:\n{abs_path}", parent=self.master)
        except Exception as e:
             self._log_message('error', f"Unexpected error opening directory '{abs_path}': {e}")
             if self.master.winfo_exists(): messagebox.showerror("Cannot Open Folder", f"An unexpected error occurred while trying to open the folder.\nError: {e}\n\nPlease navigate to:\n{abs_path}", parent=self.master)


    def _on_closing(self):
        """Handles window close event: save settings."""
        self._log_message('info', "Application closing, saving settings...")
        try:
            current_dir = self.dir_entry.get()
            if current_dir and os.path.isdir(current_dir):
                 self.settings[config_manager.LAST_DIR_KEY] = current_dir
                 config_manager.save_settings(self.settings)
                 self._log_message('info', f"Saved last used directory: {current_dir}")
            else:
                 self._log_message('info', "Last directory not saved (path in entry is invalid or empty).")
        except Exception as e:
            print(f"Error saving settings on close: {e}")
        finally:
             if self.master: self.master.destroy()