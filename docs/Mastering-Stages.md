# Mastering Stages (7-12)

These stages transform the processed audio into release-ready, professionally mastered output. They also have anti-fingerprint value — changing the dynamic profile and spectral balance makes the audio harder to identify as AI-generated.

---

## 7. Multiband Compressor

**Parameter:** `--multiband` (0.0 - 1.0, default: 0.3)

**What it does:** Splits the audio into three frequency bands (low <250Hz, mid 250Hz-4kHz, high >4kHz) and compresses each independently with different attack/release times.

**Why it matters:** AI tracks often have uneven dynamics across frequency bands. A multiband compressor tightens things up and also fundamentally changes the dynamic profile, making detection harder.

**Technical details:**
- 3 bands: low (<250Hz), mid (250Hz-4kHz), high (>4kHz)
- 4th-order Butterworth crossover filters
- Threshold: -20 to -10 dB (scales with intensity)
- Ratio: 2:1 to 4:1 (scales with intensity)
- Per-band attack/release: low=30/200ms, mid=15/150ms, high=5/80ms

**Recommended range:** 0.2 - 0.5. Higher values give more "produced" sound. Above 0.6 starts to sound obviously compressed.

---

## 8. Tape Saturation

**Parameter:** `--tape` (0.0 - 1.0, default: 0.25)

**What it does:** Emulates the behavior of analog tape machines — asymmetric soft saturation, gentle compression, and subtle high-frequency rolloff.

**Why it matters:** More sophisticated than simple harmonic enrichment. Tape has characteristic nonlinear behavior: positive and negative peaks clip differently, and high frequencies are naturally attenuated. This is exactly the kind of analog imperfection that AI audio completely lacks.

**Technical details:**
- Asymmetric saturation: tanh(x * 1.0) for positive, tanh(x * 0.85) for negative
- Drive: 1.0 + intensity * 3.0
- HF rolloff: 1st-order Butterworth low-pass at 15kHz, blended at intensity * 0.2
- Dry/wet blend: intensity * 0.5

**Recommended range:** 0.15 - 0.4. Adds warmth and character. Above 0.5 sounds noticeably "lo-fi."

---

## 9. Glue Compressor

**Parameter:** `--glue` (0.0 - 1.0, default: 0.3)

**What it does:** Gentle stereo bus compression that "glues" the mix together, making all elements feel cohesive — like they were recorded and mixed in the same session.

**Why it matters:** AI tracks often sound like a collection of separate elements rather than a unified mix. A glue compressor is standard practice in professional mastering and gives the track a human-mixed feel.

**Technical details:**
- Linked stereo compression (max envelope across both channels)
- Threshold: -18 to -8 dB (scales with intensity)
- Ratio: 1.5:1 to 3:1 (scales with intensity)
- Attack: 30ms to 10ms (faster at higher intensity)
- Release: 250ms to 150ms (faster at higher intensity)

**Recommended range:** 0.2 - 0.4. Subtle but effective. Above 0.5 starts to pump.

---

## 10. Mid/Side EQ

**Parameter:** `--mseq` (0.0 - 1.0, default: 0.25)

**What it does:** Applies separate EQ processing to the Mid (center) and Side (stereo) channels:
- **Mid:** High-pass at 80Hz (tightens bass center) + presence boost at 2-5kHz
- **Side:** Air boost above 10kHz + high-pass at 200Hz (mono-compatible bass)

**Why it matters:** More surgical than stereo widening. Directly shapes the frequency balance per spatial channel. Standard mastering technique that gives the mix clarity and spatial definition.

**Technical details:**
- Mid HP: 2nd-order Butterworth at 80Hz, blend = intensity * 0.3
- Mid presence: 2nd-order bandpass 2-5kHz, boost = intensity * 0.15
- Side air: 2nd-order high-pass at 10kHz, boost = intensity * 0.3
- Side HP: 2nd-order Butterworth at 200Hz, blend = intensity * 0.5

**Recommended range:** 0.15 - 0.4. Very effective at making tracks sound "mastered." Above 0.5 may thin out the bass.

---

## 11. Soft Clipper

**Parameter:** `--clip` (0.0 - 1.0, default: 0.2)

**What it does:** Drives the signal into a soft clipper that uses a cubic waveshaper for transparent distortion. Provides 1-2 dB of extra loudness without the pumping artifacts of limiting.

**Why it matters:** The standard loudness maximization technique in modern mastering. More transparent than the LUFS limiter alone.

**Technical details:**
- Drive: 1.0 + intensity * 1.5
- Threshold: 0.85 (cubic waveshaper above)
- Waveshaper: threshold + (1 - threshold) * tanh((|x| - threshold) / (1 - threshold))
- Dry/wet blend: intensity * 0.6
- Gain compensation applied

**Recommended range:** 0.1 - 0.3. Above 0.4 introduces audible distortion on transients.

---

## 12. LUFS Normalization

**Parameter:** `--lufs` (-24 to -8, default: -14.0)

**What it does:** Measures integrated loudness using the ITU-R BS.1770 standard (via pyloudnorm), applies gain to reach the target LUFS, then applies true peak limiting at -1 dBTP.

**Why it matters:** Ensures your track meets the loudness requirements of streaming platforms and won't be penalized by loudness normalization algorithms.

**Common targets:**
- **-14 LUFS:** Spotify, YouTube, Tidal (recommended default)
- **-16 LUFS:** Apple Music, more dynamic
- **-11 LUFS:** Louder masters, club/radio
- **-9 LUFS:** Very loud, maximum impact

**Technical details:**
- LUFS measurement: K-weighted, integrated (full track)
- True peak limit: -1 dBTP (~0.891 linear)
- Limiter: tanh-based soft limiting above 90% of threshold

This is always the last stage in the chain, ensuring consistent output loudness regardless of all preceding processing.
