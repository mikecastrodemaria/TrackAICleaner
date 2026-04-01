# Pre-Mastering Stages (7-12)

These stages prepare the audio for release with professional mastering techniques — dynamics control, tonal shaping, loudness optimization, and broadcast-standard normalization.

---

## 7. Multiband Compressor

**Parameter:** `--multiband` (0.0 - 1.0, default: 0.3)

**What it does:** Splits the audio into three frequency bands and compresses each independently, ensuring balanced dynamics across the entire spectrum.

**Technical details:**
- 3 bands: low (<250Hz), mid (250Hz-4kHz), high (>4kHz)
- 4th-order Butterworth crossover filters
- Threshold: -20 to -10 dB (scales with intensity)
- Ratio: 2:1 to 4:1 (scales with intensity)
- Per-band timing: low=30/200ms, mid=15/150ms, high=5/80ms (attack/release)

**Recommended range:** 0.2 - 0.5. Higher values give a more "produced" sound. Above 0.6 may sound obviously compressed.

---

## 8. Tape Saturation

**Parameter:** `--tape` (0.0 - 1.0, default: 0.25)

**What it does:** Emulates the musical characteristics of analog tape machines — warm saturation, gentle compression, and a natural high-frequency rolloff that adds depth and character.

**Technical details:**
- Asymmetric saturation: positive peaks saturate differently from negative (tape characteristic)
- Drive: 1.0 + intensity * 3.0
- Subtle HF rolloff at 15kHz (1st-order Butterworth)
- Dry/wet blend: intensity * 0.5

**Recommended range:** 0.15 - 0.4. Adds warmth and character. Above 0.5 gives a pronounced "lo-fi" or vintage flavor.

---

## 9. Glue Compressor

**Parameter:** `--glue` (0.0 - 1.0, default: 0.3)

**What it does:** Applies gentle stereo bus compression that makes all elements in the mix feel cohesive — the "glue" that turns separate sounds into a unified record.

**Technical details:**
- Linked stereo compression (shared envelope across both channels)
- Threshold: -18 to -8 dB (scales with intensity)
- Ratio: 1.5:1 to 3:1 (scales with intensity)
- Attack: 30ms to 10ms, Release: 250ms to 150ms

**Recommended range:** 0.2 - 0.4. Subtle but noticeable improvement in cohesion. Above 0.5 starts to pump audibly.

---

## 10. Mid/Side EQ

**Parameter:** `--mseq` (0.0 - 1.0, default: 0.25)

**What it does:** Applies separate EQ processing to the center (Mid) and stereo (Side) channels for surgical spatial control:
- **Center:** Bass tightening (HP at 80Hz) + presence boost (2-5kHz)
- **Sides:** Air boost (above 10kHz) + bass cleanup (HP at 200Hz for mono compatibility)

**Recommended range:** 0.15 - 0.4. Very effective at making mixes sound "mastered." Above 0.5 may thin out the low end.

---

## 11. Soft Clipper

**Parameter:** `--clip` (0.0 - 1.0, default: 0.2)

**What it does:** Drives the signal into a transparent soft clipper that maximizes loudness without the pumping artifacts of traditional limiting. Uses a cubic waveshaper for clean, musical clipping.

**Technical details:**
- Drive: 1.0 + intensity * 1.5
- Threshold: 0.85 (cubic waveshaper above threshold)
- Dry/wet blend: intensity * 0.6
- Gain compensation applied

**Recommended range:** 0.1 - 0.3. Above 0.4 may introduce audible distortion on transients.

---

## 12. LUFS Normalization

**Parameter:** `--lufs` (-24 to -8, default: -14.0)

**What it does:** Normalizes the track to a target loudness level using the ITU-R BS.1770 standard, then applies true peak limiting at -1 dBTP to prevent digital clipping on any playback system.

**Common targets:**
- **-14 LUFS:** Spotify, YouTube, Tidal (recommended default)
- **-16 LUFS:** Apple Music, more dynamic range
- **-11 LUFS:** Louder masters, club/radio
- **-9 LUFS:** Very loud, maximum impact

This is always the last stage in the chain, ensuring consistent output loudness regardless of all preceding processing.
