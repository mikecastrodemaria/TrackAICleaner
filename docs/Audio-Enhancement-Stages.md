# Audio Enhancement Stages (1-6)

These stages enhance the sonic quality of AI-generated music, adding depth, warmth, and natural character to make it sound more professional and polished.

---

## 1. Stereo Depth

**Parameter:** `--phase` (0.0 - 1.0, default: 0.6)

**What it does:** Enriches the stereo field by introducing natural phase variation between the left and right channels, creating a more three-dimensional listening experience.

**Technical details:**
- Applies a 2nd-order Butterworth all-pass filter to the right channel
- Normalized frequency: 0.02 + intensity * 0.03 (capped at 0.09)
- Blend factor: intensity * 0.4
- Left channel remains untouched for stability

**Recommended range:** 0.4 - 0.8. Below 0.4 is subtle. Above 0.8 may introduce audible phasing.

---

## 2. Stereo Width

**Parameter:** `--stereo` (1.0 - 2.0, default: 1.3)

**What it does:** Widens the perceived stereo image using Mid/Side processing, making the mix sound more spacious and immersive — like listening in a larger room.

**Technical details:**
- Decodes to Mid (center) and Side (stereo difference)
- Amplifies the Side signal by the width factor
- Re-encodes to L/R
- Auto-normalizes if clipping occurs

**Recommended range:** 1.1 - 1.6. Values above 1.6 may affect mono compatibility (phone speakers, some Bluetooth devices). Always test mono playback if distributing widely.

---

## 3. HF Refinement

**Parameter:** `--hf` (0.0 - 1.0, default: 0.5)

**What it does:** Smooths and refines the high-frequency content above 12kHz, cleaning up any harshness for a polished, professional top end.

**Technical details:**
- Crossover at 12kHz using 4th-order Butterworth filters
- High band is smoothed with a ~2ms running average kernel
- Low band passes through untouched
- Intensity controls the dry/wet blend of the smoothed high band

**Recommended range:** 0.3 - 0.7. This is one of the most impactful stages for overall polish. Higher values give a silkier top end.

---

## 4. Harmonic Enrichment

**Parameter:** `--harmonic` (0.0 - 1.0, default: 0.25)

**What it does:** Adds subtle even harmonics through soft saturation, bringing analog warmth and musical richness — similar to running audio through vintage tube or transformer-based equipment.

**Technical details:**
- tanh-based soft saturation with controllable drive
- Drive: 1.0 + intensity * 2.0
- Dry/wet blend: intensity * 0.3
- Auto-normalizes

**Recommended range:** 0.15 - 0.35. Adds pleasant warmth. Higher values produce more noticeable coloration — great for lo-fi or vintage aesthetics.

---

## 5. Timing Humanizer

**Parameter:** `--jitter` (0.0 - 1.0, default: 0.3)

**What it does:** Introduces natural micro-timing variations around transients, giving performances a more human, groovy feel — the way real musicians naturally play slightly ahead or behind the beat.

**Technical details:**
- Detects transients via energy envelope peak detection (10ms frames)
- Applies random sub-millisecond shifts to small regions around each transient
- Max shift: +/- 0.5ms scaled by intensity
- Deterministic RNG (seed=42) for reproducible results

**Recommended range:** 0.2 - 0.5. Very effective at adding natural feel. Above 0.5 may be noticeable on tight percussive material.

---

## 6. Ambience Shaping

**Parameter:** `--noise` (0.0 - 1.0, default: 0.2)

**What it does:** Adds organic room character to the audio by introducing subtle, shaped ambient noise — simulating the natural acoustic environment of a real recording space.

**Technical details:**
- Generates pink noise (1/f spectrum) via IIR filtering
- Noise level ranges from -80 dB (very subtle) to -50 dB (noticeable)
- Independent noise per channel for realistic stereo ambience
- Deterministic RNG (seed=123)

**Recommended range:** 0.1 - 0.3. Should be felt rather than heard. Above 0.5 becomes perceptible as ambient noise.
