# TrackWasher

Pre-mastering and audio enhancement for AI-generated music.

AI music platforms like Suno and Udio produce impressive results, but the raw output often needs polish before it's ready for release. TrackWasher bridges the gap between AI generation and professional-quality audio with a 12-stage processing chain — enhancing stereo depth, adding analog warmth, humanizing timing, and delivering broadcast-ready loudness.

![Version](https://img.shields.io/badge/Version-3.4-purple)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-green)

---

## What it does

### Audio Enhancement (stages 1-6)

| Stage | What it does | Why it matters |
|---|---|---|
| **Stereo Depth** | Enriches the stereo field with natural L/R variation | Gives the mix a more three-dimensional, immersive feel |
| **Stereo Width** | Mid/Side expansion for a spacious mix | Makes the track sound wider and more open |
| **HF Refinement** | Smooths and refines clarity above 12kHz | Cleans up harsh high frequencies for a polished top end |
| **Harmonic Enrichment** | Adds subtle even harmonics | Brings analog warmth and musical richness |
| **Timing Humanizer** | Introduces natural micro-timing variations | Gives performances a more human, groovy feel |
| **Ambience Shaping** | Adds organic room character | Makes the noise floor sound natural, like a real recording environment |

### Pre-Mastering (stages 7-12)

| Stage | What it does | Why it matters |
|---|---|---|
| **Multiband Compressor** | 3-band dynamics (low/mid/high) | Tightens the mix and balances frequency ranges |
| **Tape Saturation** | Analog tape warmth and character | Adds the musical nonlinearity of vintage equipment |
| **Glue Compressor** | Stereo bus compression | Makes all elements feel cohesive, like a professional mix |
| **Mid/Side EQ** | Spatial frequency shaping | Tightens bass, adds air and presence for clarity |
| **Soft Clipper** | Transparent loudness maximization | Extra headroom without audible distortion |
| **LUFS Normalization** | Loudness + true peak limiting | Meets streaming platform standards (-14 LUFS) |

All stages have adjustable intensity (0.0 to 1.0). Defaults are tuned for transparent, musical processing.

---

## Quick Start

### One-Click Install with Pinokio

The easiest way to install and run TrackWasher. No terminal, no Python setup — just click.

1. Install [Pinokio](https://pinokio.computer/) if you don't have it
2. In Pinokio, go to **Download** and paste:

```
https://github.com/mikecastrodemaria/trackwasher.pinokio.git
```

3. Click **Install**, then **Start** — that's it!

### Manual Install

> **MP3 support** requires [ffmpeg](https://ffmpeg.org/) installed on your system (`brew install ffmpeg` / `apt install ffmpeg` / `choco install ffmpeg`).
>
> **Windows note:** The install scripts automatically detect and use native Windows Python, even if MSYS2/Cygwin Python is also installed.

**macOS / Linux:**
```bash
git clone https://github.com/mikecastrodemaria/TrackAICleaner.git
cd TrackAICleaner
./install.sh
```

**Windows (CMD):**
```cmd
git clone https://github.com/mikecastrodemaria/TrackAICleaner.git
cd TrackAICleaner
install.bat
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/mikecastrodemaria/TrackAICleaner.git
cd TrackAICleaner
.\install.ps1
```

### Run

**Web UI (Streamlit):**
```bash
# macOS / Linux
./start.sh

# Windows CMD
start.bat

# Windows PowerShell
.\start.ps1
```

Opens `http://localhost:8501` in your browser.

**CLI:**
```bash
# Default settings
python trackwasher.py input.wav output.wav

# With a platform preset
python trackwasher.py input.wav output.wav --preset suno

# Custom enhancement + mastering
python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.5 --hf 0.7 --multiband 0.5 --tape 0.4 --glue 0.4 --lufs -14

# Disable specific stages
python trackwasher.py input.wav output.wav --disable jitter tape glue

# MP3/FLAC input (output is always WAV)
python trackwasher.py input.mp3 output.wav --preset udio
```

---

## Presets

Optimized settings for music from specific AI platforms:

| Preset | Stereo Depth | Width | HF | Harmonics | Humanizer | Ambience | Multiband | Tape | Glue | M/S EQ | Clip | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Suno** | 0.7 | 1.4 | 0.7 | 0.3 | 0.4 | 0.3 | 0.5 | 0.4 | 0.4 | 0.4 | 0.3 | -14 |
| **Udio** | 0.6 | 1.3 | 0.8 | 0.2 | 0.3 | 0.25 | 0.4 | 0.35 | 0.35 | 0.3 | 0.25 | -14 |
| **Generic AI** | 0.6 | 1.3 | 0.5 | 0.25 | 0.3 | 0.2 | 0.3 | 0.25 | 0.3 | 0.25 | 0.2 | -14 |
| **Light Touch** | 0.3 | 1.1 | 0.3 | 0.1 | 0.2 | 0.1 | 0.15 | 0.1 | 0.15 | 0.1 | 0.1 | -14 |

CLI: `--preset suno`, `--preset udio`, `--preset generic`, or `--preset light`. Individual parameters can still override preset values.

---

## Parameters

### Audio Enhancement

| Parameter | CLI flag | Default | Range | Effect when increased |
|---|---|---|---|---|
| Stereo Depth | `--phase` | 0.6 | 0.0 – 1.0 | Richer stereo depth |
| Stereo Width | `--stereo` | 1.3 | 1.0 – 2.0 | Wider stereo image |
| HF Refinement | `--hf` | 0.5 | 0.0 – 1.0 | Smoother high frequencies |
| Harmonic Enrichment | `--harmonic` | 0.25 | 0.0 – 1.0 | More analog warmth |
| Timing Humanizer | `--jitter` | 0.3 | 0.0 – 1.0 | More natural timing feel |
| Ambience Shaping | `--noise` | 0.2 | 0.0 – 1.0 | More room character |

### Pre-Mastering

| Parameter | CLI flag | Default | Range | Effect when increased |
|---|---|---|---|---|
| Multiband Compressor | `--multiband` | 0.3 | 0.0 – 1.0 | Tighter per-band dynamics |
| Tape Saturation | `--tape` | 0.25 | 0.0 – 1.0 | More analog character |
| Glue Compressor | `--glue` | 0.3 | 0.0 – 1.0 | More mix cohesion |
| Mid/Side EQ | `--mseq` | 0.25 | 0.0 – 1.0 | More spatial shaping |
| Soft Clipper | `--clip` | 0.2 | 0.0 – 1.0 | More loudness headroom |
| Target LUFS | `--lufs` | -14.0 | -24 – -8 | Louder output |

> **Note:** Stereo width above 1.6 may affect mono compatibility (phone speakers, some Bluetooth).

---

## Features

- **12-stage processing chain** — 6 audio enhancement + 6 pre-mastering stages, each individually toggleable
- **Platform presets** — optimized for Suno, Udio, and other AI music platforms
- **Before/after spectrogram** — visual comparison of the processing effect
- **Multi-format input** — WAV, FLAC, MP3, OGG (output is always lossless WAV)
- **Full pre-mastering chain** — multiband compression, tape saturation, glue compressor, Mid/Side EQ, soft clipper, LUFS normalization
- **Batch processing** — upload and process multiple tracks at once, download individually or as ZIP
- **Streamlit web UI** — drag-and-drop interface with real-time progress
- **CLI** — scriptable processing with full parameter control

---

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (for MP3 input support)
- Dependencies: `numpy`, `scipy`, `soundfile`, `streamlit`, `pyloudnorm`, `matplotlib`, `pydub`

All Python dependencies are handled automatically by the install scripts.

---

## Project Structure

```
TrackAICleaner/
├── trackwasher.py          # Processing engine + Streamlit UI + CLI
├── requirements.txt
├── install.sh / .bat / .ps1
├── start.sh / .bat / .ps1
├── docs/                   # Full documentation
├── LICENSE
└── .gitignore
```

---

## Documentation

See the [`docs/`](docs/) folder for detailed documentation:

- [Getting Started](docs/Getting-Started.md)
- [Audio Enhancement Stages](docs/Audio-Enhancement-Stages.md) — technical details for stages 1-6
- [Pre-Mastering Stages](docs/Pre-Mastering-Stages.md) — technical details for stages 7-12
- [Presets Guide](docs/Presets-Guide.md) — how to choose and customize presets
- [CLI Reference](docs/CLI-Reference.md) — all flags and examples
- [Tips & Best Practices](docs/Tips-&-Best-Practices.md) — recommended settings for common scenarios

---

## License

**CC BY-NC 4.0** — Creative Commons Attribution-NonCommercial 4.0 International

- Free to use, modify, and share
- Commercial use prohibited (selling, SaaS, paid products)

See [LICENSE](LICENSE) for details.
