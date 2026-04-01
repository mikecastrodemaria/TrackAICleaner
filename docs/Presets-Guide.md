# Presets Guide

TrackWasher includes built-in presets optimized for music from specific AI platforms. Each preset adjusts all 12 processing stages based on the typical characteristics of that platform's output.

## Choosing a Preset

### Suno
Optimized for Suno-generated music. Suno output benefits from stronger HF refinement and wider stereo enhancement. This preset applies more polish to the top end and broader spatial enhancement.

```bash
python trackwasher.py input.wav output.wav --preset suno
```

### Udio
Tuned for Udio tracks. Udio output typically has a brighter top end, so HF refinement is set higher at 0.8. Other parameters are balanced for a natural result.

```bash
python trackwasher.py input.wav output.wav --preset udio
```

### Generic AI
A balanced preset that works well for music from any AI platform. Good starting point if you're unsure which settings to use or if you're working with output from lesser-known tools.

```bash
python trackwasher.py input.wav output.wav --preset generic
```

### Light Touch
Minimal processing for situations where you want subtle enhancement without changing the character of the music. Useful for high-quality output that just needs a light polish before release.

```bash
python trackwasher.py input.wav output.wav --preset light
```

## Preset Values

| Parameter | Suno | Udio | Generic AI | Light Touch |
|---|---|---|---|---|
| Stereo Depth | 0.7 | 0.6 | 0.6 | 0.3 |
| Stereo Width | 1.4 | 1.3 | 1.3 | 1.1 |
| HF Refinement | 0.7 | 0.8 | 0.5 | 0.3 |
| Harmonic Enrichment | 0.3 | 0.2 | 0.25 | 0.1 |
| Timing Humanizer | 0.4 | 0.3 | 0.3 | 0.2 |
| Ambience Shaping | 0.3 | 0.25 | 0.2 | 0.1 |
| Multiband Compressor | 0.5 | 0.4 | 0.3 | 0.15 |
| Tape Saturation | 0.4 | 0.35 | 0.25 | 0.1 |
| Glue Compressor | 0.4 | 0.35 | 0.3 | 0.15 |
| Mid/Side EQ | 0.4 | 0.3 | 0.25 | 0.1 |
| Soft Clipper | 0.3 | 0.25 | 0.2 | 0.1 |
| Target LUFS | -14 | -14 | -14 | -14 |

## Overriding Preset Values

You can start from a preset and override individual parameters:

```bash
# Start from Suno preset but use louder mastering
python trackwasher.py input.wav output.wav --preset suno --lufs -11 --clip 0.4

# Start from Generic but skip tape saturation
python trackwasher.py input.wav output.wav --preset generic --tape 0
```

CLI overrides always take priority over preset values.
