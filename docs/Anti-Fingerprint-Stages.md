# Anti-Fingerprint Stages (1-6)

These stages target the specific artifacts that AI music generators leave in their output. Each addresses a different detection vector.

---

## 1. Phase Decorrelation

**Parameter:** `--phase` (0.0 - 1.0, default: 0.6)

**Problem:** Neural vocoders (HiFi-GAN, WaveNet) produce left and right channels that are almost perfectly correlated. This unnatural symmetry is a strong fingerprint.

**Solution:** Introduces small all-pass phase shifts on the right channel using a 2nd-order Butterworth high-pass filter. The intensity controls how much of the phase-shifted signal is blended in.

**Technical details:**
- Normalized frequency: 0.02 + intensity * 0.03 (capped at 0.09)
- Blend factor: intensity * 0.4
- Only affects R channel; L remains untouched

**Recommended range:** 0.4 - 0.8. Below 0.4 has minimal effect. Above 0.8 may introduce audible phase artifacts.

---

## 2. Stereo Widening

**Parameter:** `--stereo` (1.0 - 2.0, default: 1.3)

**Problem:** AI-generated tracks have a flat, narrow stereo image that sounds "generated" rather than recorded/mixed.

**Solution:** Mid/Side processing — decodes to M/S, amplifies the Side signal by the width factor, then re-encodes to L/R.

**Technical details:**
- Mid = (L + R) / 2
- Side = (L - R) / 2
- New L = Mid + Side * width
- New R = Mid - Side * width
- Auto-normalizes if clipping occurs

**Warning:** Values above 1.6 may cause phase cancellation issues on mono playback (phone speakers, some Bluetooth). Test mono compatibility.

---

## 3. HF Artifact Smoothing

**Parameter:** `--hf` (0.0 - 1.0, default: 0.5)

**Problem:** Mel-spectrogram inversion (used by Suno, Udio, and most AI generators) creates repetitive "comb" patterns in the high frequencies above 12kHz. These are invisible to casual listening but clearly detectable by spectral analysis.

**Solution:** Splits the signal at 12kHz using 4th-order Butterworth filters. The high band is smoothed with a running average kernel (~2ms), then blended back with the original based on intensity.

**Technical details:**
- Crossover: 12kHz (4th-order Butterworth)
- Smoothing kernel: ~2ms running average
- Low band passes through untouched
- Intensity controls dry/wet blend of the high band

**Recommended range:** 0.3 - 0.7. This is the most important anti-fingerprint stage for Suno/Udio tracks.

---

## 4. Harmonic Enrichment

**Parameter:** `--harmonic` (0.0 - 1.0, default: 0.25)

**Solution:** Adds even harmonics via tanh soft-clip saturation, simulating the nonlinear behavior of analog equipment.

**Technical details:**
- Drive: 1.0 + intensity * 2.0
- Saturation: tanh(signal * drive) / (1 + intensity * 0.5)
- Blend: intensity * 0.3
- Auto-normalizes

**Recommended range:** 0.15 - 0.35. Cosmetic but effective at adding "life" to sterile AI audio. Higher values color the sound noticeably.

---

## 5. Micro-Timing Jitter

**Parameter:** `--jitter` (0.0 - 1.0, default: 0.3)

**Problem:** AI generators place every beat and note on a mathematically perfect grid. Real musicians have natural micro-timing variations.

**Solution:** Detects transients via energy envelope peak detection, then applies random sub-millisecond circular shifts to small regions around each transient.

**Technical details:**
- Energy envelope: 10ms frames, 5ms hop
- Transient threshold: mean + 1.5 * std of energy
- Max shift: +/-0.5ms * intensity (in samples)
- Deterministic RNG (seed=42) for reproducibility
- Circular shift of 2-frame region around each peak

**Recommended range:** 0.2 - 0.5. Very effective anti-detection measure. Above 0.5 may be audible on percussive material.

---

## 6. Spectral Noise Shaping

**Parameter:** `--noise` (0.0 - 1.0, default: 0.2)

**Problem:** AI-generated audio has an unnaturally clean noise floor. Real recordings always have some ambient noise from room tone, preamps, converters, etc.

**Solution:** Generates pink noise (1/f spectrum) via IIR filtering of white noise, then adds it at very low level to the signal.

**Technical details:**
- Pink noise: Paul Kellet's IIR filter coefficients
- Noise level: -80 dB (intensity=0) to -50 dB (intensity=1)
- Independent noise per channel
- Deterministic RNG (seed=123)

**Recommended range:** 0.1 - 0.3. Should be inaudible or barely perceptible. Above 0.5 becomes noticeable as hiss.
