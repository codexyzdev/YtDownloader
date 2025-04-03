# downloader.py
import os
import traceback
import yt_dlp

# --- Custom Logger Class (interno a este módulo) ---
class _YdlpLogger:
    """Internal logger to route yt-dlp messages via callback."""
    def __init__(self, log_callback):
        self._log = log_callback

    def debug(self, msg):
        # Remove "[debug] " prefix for cleaner logging if shown
        if msg.startswith('[debug] '):
            msg = msg[len('[debug] '):]
        # Pass debug messages only if explicitly needed by caller (e.g., via log level)
        # self._log('debug', msg)
        pass

    def info(self, msg):
         # Exclude progress hook messages if they start with standard download prefix
         if not msg.startswith('[download] Destination:'):
              self._log('info', msg)

    def warning(self, msg):
        self._log('warning', msg)

    def error(self, msg):
        self._log('error', msg)

# --- Main Downloader Class ---
class Downloader:
    """Handles the yt-dlp download process."""

    def __init__(self):
        """Initializes the Downloader."""
        # Could potentially load yt-dlp parameters here if needed globally
        pass

    def _progress_hook(self, d, progress_callback):
        """Internal progress hook to relay info via progress_callback."""
        if not progress_callback:
            return

        status = d.get('status')
        filename = d.get('filename', 'N/A')
        short_filename = (filename[:50] + '...') if len(filename) > 53 else filename

        if status == 'downloading':
            percent_str = d.get('_percent_str', 'N/A').strip()
            speed_str = d.get('_speed_str', 'N/A').strip()
            eta_str = d.get('_eta_str', 'N/A').strip()
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            
            percent = None
            if total_bytes and downloaded_bytes is not None:
                try:
                    percent = (downloaded_bytes / total_bytes) * 100
                except ZeroDivisionError:
                    percent = 0 # Avoid error if total_bytes is somehow 0

            message = f"{percent_str} | {speed_str} | ETA: {eta_str}"
            progress_callback(percent, message, status, short_filename)

        elif status == 'finished':
            total_bytes_str = d.get('_total_bytes_str', 'N/A')
            message = f"Finished: {short_filename} ({total_bytes_str})"
            # Signal 100% completion for this file
            progress_callback(100.0, message, status, short_filename)
            
        elif status == 'error':
            message = f"Error downloading: {short_filename}"
             # Signal error, maybe reset progress or show error state
            progress_callback(None, message, status, short_filename)
            
        elif status == 'processing':
             processor = d.get('processor', 'postprocessor')
             message = f"Processing ({processor})..."
             # Indicate processing, maybe indeterminate progress
             progress_callback(None, message, status, short_filename)


    def download_media(self, url, directory, extension, progress_callback, log_callback):
        """
        Downloads media from the given URL using specified format options.

        Args:
            url (str): The URL of the media to download.
            directory (str): The target directory to save the file.
            extension (str): The desired file extension ('mp3', 'mp4', etc.).
            progress_callback (callable): Function to call with progress updates.
                                          Expected signature: func(percent, message, status, filename)
                                          'percent' is float (0-100) or None if indeterminate.
            log_callback (callable): Function to call for logging messages.
                                     Expected signature: func(level, message)
                                     'level' is str ('info', 'warning', 'error').

        Returns:
            bool: True if the download process completed without critical errors, False otherwise.
        """
        log_callback('info', f"Preparing download: URL={url}, Dir={directory}, Format={extension}")

        # --- Create directory ---
        try:
            os.makedirs(directory, exist_ok=True)
            log_callback('info', f"Ensured output directory exists: {directory}")
        except OSError as e:
            log_callback('error', f"Fatal: Cannot create directory {directory}: {e}")
            return False # Cannot proceed

        # --- Build yt-dlp Options ---
        # Use internal logger and progress hook wrappers
        internal_logger = _YdlpLogger(log_callback)
        internal_progress_hook = lambda d: self._progress_hook(d, progress_callback)

        ydl_opts = {
            'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
            'verbose': False, # Control verbosity via logger
            'progress_hooks': [internal_progress_hook],
            'logger': internal_logger,
            'cookiefile': 'cookies.txt', # yt-dlp handles existence check
            'nocheckcertificate': True, # Use with caution
            'addmetadata': True,
            'ignoreerrors': True, # Critical for playlists; errors logged by hook/logger
            # Optional: Specify ffmpeg path if needed
            # 'ffmpeg_location': '/path/to/ffmpeg'
        }

        # --- Format Specific Options ---
        requested_format = extension.lower()
        if requested_format == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192', # Standard MP3 quality
                }],
            })
            log_callback('info', "Configured for MP3 download.")
        elif requested_format in ['mp4', 'mkv', 'webm',]:
             # Prioritize direct format match if possible, then merge
            format_pref = f'bestvideo[height<=?1080][ext={requested_format}]+bestaudio[ext=m4a]/bestvideo[ext={requested_format}]+bestaudio/bestvideo[height<=?1080]+bestaudio/best'
            if requested_format == 'mp4': # Explicit MP4 preference
                format_pref = 'bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/bestvideo[height<=?1080]+bestaudio/best'

            ydl_opts.update({
                'format': format_pref,
                'merge_output_format': requested_format,
            })
            log_callback('info', f"Configured for {requested_format.upper()} video download.")
        else:
            log_callback('warning', f"Unsupported extension '{extension}'. Defaulting to MKV video.")
            ydl_opts.update({
                'format': 'bestvideo[height<=?1080]+bestaudio/best', # Limit height slightly
                'merge_output_format': 'mkv',
            })

        # --- Log Final Options ---
        log_callback('info', "\n--- Effective yt-dlp Options ---")
        for key, value in ydl_opts.items():
            if key != 'logger' and key != 'progress_hooks': # Avoid logging objects
                 log_callback('info', f"{key}: {value}")
        log_callback('info', "------------------------------\n")

        # --- Execute Download ---
        download_successful = False
        try:
            log_callback('info', "Initiating download with yt-dlp...")
            # Use context manager for proper cleanup
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # download() returns 0 on success, 1 if errors occurred (even with ignoreerrors)
                return_code = ydl.download([url])
                if return_code == 0:
                     log_callback('info', "yt-dlp download process completed successfully.")
                     download_successful = True
                else:
                     # Errors occurred but were ignored (e.g., playlist item failed)
                     log_callback('warning', f"yt-dlp process finished, but some errors occurred (return code: {return_code}). Check logs.")
                     # Consider it 'successful' in terms of the process finishing
                     # The calling GUI should rely on logs/progress for item status
                     download_successful = True # Or False, depending on desired strictness

        except yt_dlp.utils.DownloadError as e:
            # This catches errors *not* ignored by 'ignoreerrors' (e.g., critical failures)
            log_callback('error', f"DownloadError encountered: {e}")
            # Log hint about FFmpeg if relevant
            if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
                 log_callback('error', "Hint: Check FFmpeg installation and PATH.")
        except Exception as e:
            # Catch any other unexpected error during yt-dlp execution
            log_callback('error', f"Unexpected error during download: {e}")
            log_callback('error', f"Traceback:\n{traceback.format_exc()}")
        finally:
            log_callback('info', f"Download attempt finished. Overall success: {download_successful}")

        return download_successful