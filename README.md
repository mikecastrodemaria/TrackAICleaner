# TrackWasher

Remove AI-generated fingerprints from audio tracks.

AI music generators (Suno, Udio, etc.) leave detectable artifacts in their output — phase symmetry, spectral comb patterns, sterile stereo imaging, perfect timing grids, and unnaturally clean noise floors. TrackWasher applies seven audio processing stages to neutralize these signatures while preserving musical quality.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-green)

---

## What it does

| Stage | What it targets | Why it matters |
|---|---|---|
| **Phase Decorrelation** | L/R channel symmetry | Neural vocoders produce unnaturally identical channels |
| **Stereo Widening** | Flat stereo image | Mid/Side expansion makes the mix sound more organic |
| **HF Artifact Smoothing** | Spectral combs >12kHz | HiFi-GAN / WaveNet leave repetitive high-frequency patterns |
| **Harmonic Enrichment** | Digital sterility | Soft saturation adds even harmonics for analog warmth |
| **Micro-Timing Jitter** | Perfect grid timing | AI places beats on mathematically perfect grids — humans don't |
| **Spectral Noise Shaping** | Clean noise floor | AI output has an unnaturally silent noise floor |
| **LUFS Normalization** | Loudness consistency | Normalizes to -14 LUFS (Spotify/YouTube) with true peak limiting |

All stages have adjustable intensity. Defaults are tuned for safe, transparent processing.

---

## Quick Start

### Install

> **MP3 support** requires [ffmpeg](https://ffmpeg.org/) installed on your system (`brew install ffmpeg` / `apt install ffmpeg` / `choco install ffmpeg`).

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

# With a generator preset
python trackwasher.py input.wav output.wav --preset suno

# Custom intensities
python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.5 --hf 0.7 --harmonic 0.3 --jitter 0.4 --noise 0.3 --lufs -14

# MP3/FLAC input (output is always WAV)
python trackwasher.py input.mp3 output.wav --preset udio
```

---

## Presets

Built-in presets tuned for specific AI generators:

| Preset | Phase | Stereo | HF | Harmonic | Jitter | Noise | LUFS |
|---|---|---|---|---|---|---|---|
| **Suno** | 0.7 | 1.4 | 0.7 | 0.3 | 0.4 | 0.3 | -14 |
| **Udio** | 0.6 | 1.3 | 0.8 | 0.2 | 0.3 | 0.25 | -14 |
| **Generic AI** | 0.6 | 1.3 | 0.5 | 0.25 | 0.3 | 0.2 | -14 |
| **Light Touch** | 0.3 | 1.1 | 0.3 | 0.1 | 0.2 | 0.1 | -14 |

In the CLI, use `--preset suno`, `--preset udio`, `--preset generic`, or `--preset light`. Individual parameters can still override preset values.

---

## Parameters

| Parameter | Default | Range | Effect when increased |
|---|---|---|---|
| `Phase Decorrelation` | 0.6 | 0.0 – 1.0 | More L/R separation |
| `Stereo Widening` | 1.3 | 1.0 – 2.0 | Wider stereo image |
| `HF Artifact Smoothing` | 0.5 | 0.0 – 1.0 | More high-frequency smoothing |
| `Harmonic Enrichment` | 0.25 | 0.0 – 1.0 | More analog warmth |
| `Micro-Timing Jitter` | 0.3 | 0.0 – 1.0 | More timing humanization |
| `Spectral Noise Shaping` | 0.2 | 0.0 – 1.0 | More noise floor masking |
| `Target LUFS` | -14.0 | -24.0 – -8.0 | Louder output |

> **Note:** Stereo widening above 1.6 may cause phase issues on mono playback.

---

## Features

- **7-stage processing chain** — from phase decorrelation to LUFS mastering
- **Generator presets** — one-click settings for Suno, Udio, and more
- **Before/after spectrogram** — visual comparison of the processing effect
- **Multi-format input** — WAV, FLAC, MP3, OGG (output is always lossless WAV)
- **LUFS normalization** — broadcast/streaming-ready loudness with true peak limiting
- **Streamlit web UI** — drag-and-drop interface with real-time progress
- **CLI** — scriptable batch processing with full parameter control

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
├── LICENSE
└── .gitignore
```

---

## License

**CC BY-NC 4.0** — Creative Commons Attribution-NonCommercial 4.0 International

- Free to use, modify, and share
- Commercial use prohibited (selling, SaaS, paid products)

See [LICENSE](LICENSE) for details.
