# Tips & Best Practices

## General Guidelines

1. **Start with a preset, then adjust.** Don't try to dial in all 12 parameters from scratch. Pick the closest preset and tweak from there.

2. **Less is more.** The default values are designed to be transparent. If you can hear the processing, you've probably gone too far (unless that's what you want).

3. **Always A/B compare.** Use the spectrogram comparison in the Streamlit UI to verify changes are working. Listen critically on good headphones.

## Anti-Fingerprint Priority

If you care most about removing AI detection signatures, prioritize these stages:

1. **HF Artifact Smoothing** (most impactful for spectral analysis tools)
2. **Micro-Timing Jitter** (most impactful for rhythm analysis tools)
3. **Phase Decorrelation** (most impactful for L/R correlation analysis)
4. **Spectral Noise Shaping** (masks noise floor analysis)

## Mastering Priority

If you care most about release-ready sound quality:

1. **LUFS Normalization** (essential for streaming platforms)
2. **Multiband Compressor** (tightens the overall sound)
3. **Glue Compressor** (makes the mix cohesive)
4. **Mid/Side EQ** (professional spatial balance)

## Common Scenarios

### "I want maximum anti-fingerprint effect"

```bash
python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.5 --hf 0.8 --harmonic 0.3 --jitter 0.5 --noise 0.4 --multiband 0.4 --tape 0.3 --lufs -14
```

### "I want clean mastering without changing the sound too much"

```bash
python trackwasher.py input.wav output.wav --preset light --multiband 0.3 --glue 0.3 --mseq 0.2 --lufs -14
```

### "I want the loudest possible master"

```bash
python trackwasher.py input.wav output.wav --preset generic --multiband 0.6 --glue 0.5 --clip 0.4 --lufs -9
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

If stereo widening is above 1.5, test mono playback carefully. The Mid/Side EQ's bass tightening (side HP at 200Hz) helps maintain mono compatibility.

## Sample Rate

TrackWasher works at the input file's native sample rate. No resampling is performed. For best quality, start with the highest quality source available (WAV or FLAC, 44.1kHz or higher).

## Output Format

Output is always 16-bit PCM WAV. This is the universal standard for distribution. If you need 24-bit or 32-bit float output, you can modify the `subtype` parameter in the `sf.write()` call in the source code.
