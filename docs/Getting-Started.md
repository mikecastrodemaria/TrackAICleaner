# Getting Started

## Requirements

- **Python 3.9+**
- **ffmpeg** (only needed for MP3 input) — install via `brew install ffmpeg` (macOS), `apt install ffmpeg` (Linux), or `choco install ffmpeg` (Windows)

## Installation

```bash
git clone https://github.com/mikecastrodemaria/TrackAICleaner.git
cd TrackAICleaner
```

| Platform | Install | Start |
|---|---|---|
| macOS / Linux | `./install.sh` | `./start.sh` |
| Windows CMD | `install.bat` | `start.bat` |
| Windows PowerShell | `.\install.ps1` | `.\start.ps1` |

The install scripts create a `.venv` virtual environment and install all Python dependencies automatically.

## Running the Web UI

After install, run the start script. It opens `http://localhost:8501` in your browser.

1. Upload a WAV, FLAC, MP3, or OGG file
2. Select a platform preset or adjust sliders manually
3. Click **Wash Track**
4. Listen to the result, view the spectrogram comparison
5. Download the enhanced WAV file

## Running via CLI

```bash
# Basic usage
python trackwasher.py input.wav output.wav

# With a platform preset
python trackwasher.py input.wav output.wav --preset suno

# Custom parameters
python trackwasher.py input.wav output.wav --phase 0.8 --multiband 0.5 --lufs -14
```

Output is always lossless WAV (16-bit PCM), regardless of input format.
