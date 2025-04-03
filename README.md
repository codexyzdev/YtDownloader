# YtDownloader

A desktop application with a graphical interface for easily and quickly downloading YouTube videos and audio.

![YtDownloader GUI](screenshots/app.png) *(Application screenshot)*

## Features

- 🎥 Download videos in multiple formats (MP4, MKV, WEBM, AVI, FLV, MOV)
- 🎵 Extract audio in MP3 format
- 📁 Choose destination directory
- 📊 Real-time progress bar
- 📝 Detailed download logging
- 🔄 Playlist support
- 🎨 Intuitive graphical interface

## Requirements

- Python 3.6 or higher
- FFmpeg (required for format conversion)
- Required Python libraries:
  - yt-dlp
  - tkinter (included with Python)

## Installation

1. Clone or download this repository

1. Install dependencies:

```bash
pip install yt-dlp
```

1. Install FFmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Usage

1. Run the application:

```bash
python app.tkinter.py
```

1. Paste the YouTube video URL
1. Select desired format (MP3 or video)
1. Choose destination directory
1. Click "Download"

## Notes

- The application will automatically create the destination directory if it doesn't exist
- Files are named according to the original video title
- Cookie support included (optional) via `cookies.txt` file

## Troubleshooting

- If FFmpeg is not installed, the application will show a warning at startup
- Errors and important messages are shown in the log area
- For download issues, verify your internet connection and URL validity

## License

This project is available as open source.

## Contributing

Contributions are welcome. Please feel free to:

- Report bugs
- Suggest new features
- Submit pull requests
