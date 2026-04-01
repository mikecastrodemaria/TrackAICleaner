# CLI Reference

## Basic Syntax

```
python trackwasher.py <input> <output> [options]
```

- **input**: Path to input audio file (WAV, FLAC, MP3, OGG)
- **output**: Path for output WAV file (always 16-bit PCM)

## Options

### Preset

| Flag | Values | Description |
|---|---|---|
| `--preset` | `suno`, `udio`, `generic`, `light` | Apply platform-optimized settings |

### Audio Enhancement

| Flag | Default | Range | Description |
|---|---|---|---|
| `--phase` | 0.6 | 0.0 - 1.0 | Stereo depth enrichment |
| `--stereo` | 1.3 | 1.0 - 2.0 | Stereo width expansion |
| `--hf` | 0.5 | 0.0 - 1.0 | High-frequency refinement |
| `--harmonic` | 0.25 | 0.0 - 1.0 | Harmonic enrichment |
| `--jitter` | 0.3 | 0.0 - 1.0 | Timing humanizer |
| `--noise` | 0.2 | 0.0 - 1.0 | Ambience shaping |

### Pre-Mastering

| Flag | Default | Range | Description |
|---|---|---|---|
| `--multiband` | 0.3 | 0.0 - 1.0 | Multiband compressor |
| `--tape` | 0.25 | 0.0 - 1.0 | Tape saturation |
| `--glue` | 0.3 | 0.0 - 1.0 | Glue compressor |
| `--mseq` | 0.25 | 0.0 - 1.0 | Mid/Side EQ |
| `--clip` | 0.2 | 0.0 - 1.0 | Soft clipper |
| `--lufs` | -14.0 | -24 to -8 | Target LUFS level |

## Examples

```bash
# Minimal enhancement
python trackwasher.py input.wav output.wav --preset light

# Full enhancement with warm character
python trackwasher.py input.wav output.wav --phase 0.8 --harmonic 0.4 --tape 0.4 --glue 0.4 --lufs -14

# Pre-mastering only (skip enhancement)
python trackwasher.py input.wav output.wav --phase 0 --stereo 1.0 --hf 0 --harmonic 0 --jitter 0 --noise 0 --multiband 0.5 --tape 0.3 --glue 0.4 --lufs -14

# Loud master for club use
python trackwasher.py input.wav output.wav --preset suno --lufs -11 --clip 0.4 --multiband 0.5

# MP3 input
python trackwasher.py track.mp3 track_enhanced.wav --preset generic
```

## Web UI

Launch the Streamlit web interface:

```bash
streamlit run trackwasher.py
```

Or use the platform-specific start scripts (`./start.sh`, `start.bat`, `.\start.ps1`).
