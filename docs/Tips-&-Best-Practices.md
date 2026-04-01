# Tips & Best Practices

## General Guidelines

1. **Start with a preset, then adjust.** Don't try to dial in all 12 parameters from scratch. Pick the closest preset and tweak from there.

2. **Less is more.** The default values are designed to be transparent. If you can hear the processing as "processing" rather than "improvement," you've probably gone too far.

3. **Always A/B compare.** Use the spectrogram comparison in the Streamlit UI to verify changes. Listen critically on good headphones.

## Enhancement Priority

For the best sonic improvement, prioritize:

1. **HF Refinement** — biggest impact on overall polish and clarity
2. **Stereo Width** — immediately makes the mix feel more spacious
3. **Timing Humanizer** — adds natural groove and feel
4. **Harmonic Enrichment** — brings analog warmth

## Pre-Mastering Priority

For release-ready loudness and dynamics:

1. **LUFS Normalization** — essential for streaming platforms
2. **Multiband Compressor** — tightens the overall balance
3. **Glue Compressor** — makes the mix cohesive
4. **Mid/Side EQ** — professional spatial balance

## Common Scenarios

### "I want the best possible quality for Spotify/YouTube release"

```bash
python trackwasher.py input.wav output.wav --preset suno --lufs -14
```

### "I want a warm, analog-sounding master"

```bash
python trackwasher.py input.wav output.wav --preset generic --tape 0.5 --harmonic 0.4 --glue 0.4
```

### "I want maximum loudness for club/radio"

```bash
python trackwasher.py input.wav output.wav --preset generic --multiband 0.6 --glue 0.5 --clip 0.4 --lufs -9
```

### "I want subtle polish without changing the character"

```bash
python trackwasher.py input.wav output.wav --preset light
```

### "I want to keep the original dynamics"

```bash
python trackwasher.py input.wav output.wav --preset generic --multiband 0 --glue 0 --clip 0 --lufs -16
```

## Mono Compatibility

Always check your output in mono if it will be played on:
- Phone speakers
- Some Bluetooth speakers
- PA systems in mono configuration

If stereo width is above 1.5, test mono playback. The Mid/Side EQ stage helps maintain mono compatibility by tightening bass in the center.

## Sample Rate

TrackWasher works at the input file's native sample rate. No resampling is performed. For best quality, use the highest quality source available (WAV or FLAC, 44.1kHz or higher).

## Output Format

Output is always 16-bit PCM WAV — the universal standard for digital distribution. If you need 24-bit or 32-bit float output, you can modify the `subtype` parameter in the `sf.write()` call in the source code.
