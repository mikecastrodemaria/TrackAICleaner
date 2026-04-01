# TrackWasher

Remove AI-generated fingerprints from audio tracks and master them for release.

AI music generators (Suno, Udio, etc.) leave detectable artifacts — phase symmetry, spectral comb patterns, sterile stereo imaging, perfect timing grids, and unnaturally clean noise floors. TrackWasher applies a 12-stage processing chain to neutralize these signatures and deliver mastered, release-ready audio.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-green)

---

## What it does

### Anti-Fingerprint (stages 1-6)

| Stage | What it targets | Why it matters |
|---|---|---|
| **Phase Decorrelation** | L/R channel symmetry | Neural vocoders produce unnaturally identical channels |
| **Stereo Widening** | Flat stereo image | Mid/Side expansion makes the mix sound more organic |
| **HF Artifact Smoothing** | Spectral combs >12kHz | HiFi-GAN / WaveNet leave repetitive high-frequency patterns |
| **Harmonic Enrichment** | Digital sterility | Soft saturation adds even harmonics for analog warmth |
| **Micro-Timing Jitter** | Perfect grid timing | AI places beats on mathematically perfect grids — humans don't |
| **Spectral Noise Shaping** | Clean noise floor | AI output has an unnaturally silent noise floor |

### Mastering (stages 7-12)

| Stage | What it does | Why it matters |
|---|---|---|
| **Multiband Compressor** | 3-band dynamics (low/mid/high) | Tightens dynamics per frequency range, changes detection profile |
| **Tape Saturation** | Analog tape emulation | Asymmetric saturation + HF rolloff for organic nonlinearity |
| **Glue Compressor** | Stereo bus compression | Makes elements sound cohesive, like a human-mixed track |
| **Mid/Side EQ** | Spatial frequency shaping | Tightens bass center, adds air on sides, presence boost |
| **Soft Clipper** | Transparent clipping | Extra 1-2 dB of loudness without audible distortion |
| **LUFS Normalization** | Loudness + true peak limiting | -14 LUFS (Spotify/YouTube standard) with -1 dBTP ceiling |

All stages have adjustable intensity (0.0 to 1.0). Defaults are tuned for safe, transparent processing.

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

# Custom — anti-fingerprint + mastering
python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.5 --hf 0.7 --multiband 0.5 --tape 0.4 --glue 0.4 --lufs -14

# MP3/FLAC input (output is always WAV)
python trackwasher.py input.mp3 output.wav --preset udio
```

---

## Presets

Built-in presets tuned for specific AI generators:

| Preset | Phase | Stereo | HF | Harmonic | Jitter | Noise | Multiband | Tape | Glue | M/S EQ | Clip | LUFS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Suno** | 0.7 | 1.4 | 0.7 | 0.3 | 0.4 | 0.3 | 0.5 | 0.4 | 0.4 | 0.4 | 0.3 | -14 |
| **Udio** | 0.6 | 1.3 | 0.8 | 0.2 | 0.3 | 0.25 | 0.4 | 0.35 | 0.35 | 0.3 | 0.25 | -14 |
| **Generic AI** | 0.6 | 1.3 | 0.5 | 0.25 | 0.3 | 0.2 | 0.3 | 0.25 | 0.3 | 0.25 | 0.2 | -14 |
| **Light Touch** | 0.3 | 1.1 | 0.3 | 0.1 | 0.2 | 0.1 | 0.15 | 0.1 | 0.15 | 0.1 | 0.1 | -14 |

CLI: `--preset suno`, `--preset udio`, `--preset generic`, or `--preset light`. Individual parameters can still override preset values.

---

## Parameters

### Anti-Fingerprint

| Parameter | CLI flag | Default | Range | Effect when increased |
|---|---|---|---|---|
| Phase Decorrelation | `--phase` | 0.6 | 0.0 – 1.0 | More L/R separation |
| Stereo Widening | `--stereo` | 1.3 | 1.0 – 2.0 | Wider stereo image |
| HF Artifact Smoothing | `--hf` | 0.5 | 0.0 – 1.0 | More high-frequency smoothing |
| Harmonic Enrichment | `--harmonic` | 0.25 | 0.0 – 1.0 | More analog warmth |
| Micro-Timing Jitter | `--jitter` | 0.3 | 0.0 – 1.0 | More timing humanization |
| Spectral Noise Shaping | `--noise` | 0.2 | 0.0 – 1.0 | More noise floor masking |

### Mastering

| Parameter | CLI flag | Default | Range | Effect when increased |
|---|---|---|---|---|
| Multiband Compressor | `--multiband` | 0.3 | 0.0 – 1.0 | Tighter per-band dynamics |
| Tape Saturation | `--tape` | 0.25 | 0.0 – 1.0 | More analog character |
| Glue Compressor | `--glue` | 0.3 | 0.0 – 1.0 | More mix cohesion |
| Mid/Side EQ | `--mseq` | 0.25 | 0.0 – 1.0 | More spatial shaping |
| Soft Clipper | `--clip` | 0.2 | 0.0 – 1.0 | More loudness headroom |
| Target LUFS | `--lufs` | -14.0 | -24 – -8 | Louder output |

> **Note:** Stereo widening above 1.6 may cause phase issues on mono playback.

---

## Features

- **12-stage processing chain** — 6 anti-fingerprint + 6 mastering stages
- **Generator presets** — one-click settings for Suno, Udio, and more
- **Before/after spectrogram** — visual comparison of the processing effect
- **Multi-format input** — WAV, FLAC, MP3, OGG (output is always lossless WAV)
- **Full mastering chain** — multiband compression, tape saturation, glue compressor, Mid/Side EQ, soft clipper, LUFS normalization
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
├── LICENSE
└── .gitignore
```

---

## Documentation

See the [`docs/`](docs/) folder for detailed documentation:

- [Getting Started](docs/Getting-Started.md)
- [Anti-Fingerprint Stages](docs/Anti-Fingerprint-Stages.md) — technical details for stages 1-6
- [Mastering Stages](docs/Mastering-Stages.md) — technical details for stages 7-12
- [Presets Guide](docs/Presets-Guide.md) — how to choose and customize presets
- [CLI Reference](docs/CLI-Reference.md) — all flags and examples
- [Tips & Best Practices](docs/Tips-&-Best-Practices.md) — recommended settings for common scenarios

---

## License

**CC BY-NC 4.0** — Creative Commons Attribution-NonCommercial 4.0 International

- Free to use, modify, and share
- Commercial use prohibited (selling, SaaS, paid products)

See [LICENSE](LICENSE) for details.
