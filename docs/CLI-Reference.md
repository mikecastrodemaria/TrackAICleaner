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
| `--preset` | `suno`, `udio`, `generic`, `light` | Apply a generator-specific preset |

### Anti-Fingerprint

| Flag | Default | Range | Description |
|---|---|---|---|
| `--phase` | 0.6 | 0.0 - 1.0 | Phase decorrelation intensity |
| `--stereo` | 1.3 | 1.0 - 2.0 | Stereo widening factor |
| `--hf` | 0.5 | 0.0 - 1.0 | HF artifact smoothing intensity |
| `--harmonic` | 0.25 | 0.0 - 1.0 | Harmonic enrichment intensity |
| `--jitter` | 0.3 | 0.0 - 1.0 | Micro-timing jitter intensity |
| `--noise` | 0.2 | 0.0 - 1.0 | Spectral noise shaping intensity |

### Mastering

| Flag | Default | Range | Description |
|---|---|---|---|
| `--multiband` | 0.3 | 0.0 - 1.0 | Multiband compressor intensity |
| `--tape` | 0.25 | 0.0 - 1.0 | Tape saturation intensity |
| `--glue` | 0.3 | 0.0 - 1.0 | Glue compressor intensity |
| `--mseq` | 0.25 | 0.0 - 1.0 | Mid/Side EQ intensity |
| `--clip` | 0.2 | 0.0 - 1.0 | Soft clipper intensity |
| `--lufs` | -14.0 | -24 to -8 | Target LUFS level |

## Examples

```bash
# Minimal processing
python trackwasher.py input.wav output.wav --preset light

# Heavy anti-fingerprint, default mastering
python trackwasher.py input.wav output.wav --phase 0.9 --hf 0.8 --jitter 0.5 --noise 0.4

# Skip anti-fingerprint, mastering only
python trackwasher.py input.wav output.wav --phase 0 --stereo 1.0 --hf 0 --harmonic 0 --jitter 0 --noise 0 --multiband 0.5 --tape 0.3 --glue 0.4 --lufs -14

# Loud master for club use
python trackwasher.py input.wav output.wav --preset suno --lufs -11 --clip 0.4 --multiband 0.5

# MP3 input
python trackwasher.py track.mp3 track_washed.wav --preset generic
```

## Web UI

Launch the Streamlit web interface:

```bash
streamlit run trackwasher.py
```

Or use the platform-specific start scripts (`./start.sh`, `start.bat`, `.\start.ps1`).
