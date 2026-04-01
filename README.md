# TrackWasher

Remove AI-generated fingerprints from audio tracks.

AI music generators (Suno, Udio, etc.) leave detectable artifacts in their output — phase symmetry, spectral comb patterns, sterile stereo imaging. TrackWasher applies four audio processing stages to neutralize these signatures while preserving musical quality.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What it does

| Stage | What it targets | Why it matters |
|---|---|---|
| **Phase Decorrelation** | L/R channel symmetry | Neural vocoders produce unnaturally identical channels |
| **Stereo Widening** | Flat stereo image | Mid/Side expansion makes the mix sound more organic |
| **HF Artifact Smoothing** | Spectral combs >12kHz | HiFi-GAN / WaveNet leave repetitive high-frequency patterns |
| **Harmonic Enrichment** | Digital sterility | Soft saturation adds even harmonics for analog warmth |

All four stages have adjustable intensity — defaults are tuned for safe, transparent processing.

---

## Quick Start

### Install

**macOS / Linux:**
```bash
git clone https://github.com/YOUR_USERNAME/TrackAICleaner.git
cd TrackAICleaner
./install.sh
```

**Windows (CMD):**
```cmd
git clone https://github.com/YOUR_USERNAME/TrackAICleaner.git
cd TrackAICleaner
install.bat
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/YOUR_USERNAME/TrackAICleaner.git
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

# Custom intensities
python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.5 --hf 0.7 --harmonic 0.3
```

---

## Parameters

| Parameter | Default | Range | Effect when increased |
|---|---|---|---|
| `Phase Decorrelation` | 0.6 | 0.0 – 1.0 | More L/R separation |
| `Stereo Widening` | 1.3 | 1.0 – 2.0 | Wider stereo image |
| `HF Artifact Smoothing` | 0.5 | 0.0 – 1.0 | More high-frequency smoothing |
| `Harmonic Enrichment` | 0.25 | 0.0 – 1.0 | More analog warmth |

> **Note:** Stereo widening above 1.6 may cause phase issues on mono playback.

---

## Requirements

- Python 3.9+
- Dependencies: `numpy`, `scipy`, `soundfile`, `streamlit`

All handled automatically by the install scripts.

---

## Project Structure

```
TrackAICleaner/
├── trackwasher.py      # Processing engine + Streamlit UI + CLI
├── requirements.txt
├── install.sh / .bat / .ps1
├── start.sh / .bat / .ps1
└── .gitignore
```

---

## License

MIT
