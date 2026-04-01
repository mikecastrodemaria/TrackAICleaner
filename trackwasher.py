# ============================================================
#  trackwasher.py  —  Pre-mastering & audio enhancement for AI-generated music
#  Version 3.3
#
#  INSTALL:
#    pip install numpy scipy soundfile streamlit pyloudnorm matplotlib pydub
#
#  CLI USAGE:
#    python trackwasher.py input.wav output.wav
#    python trackwasher.py input.wav output.wav --preset suno
#    python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.4 --hf 0.6
#
#  STREAMLIT UI:
#    streamlit run trackwasher.py
#
#  PROCESSING CHAIN (12 stages):
#    ── Audio Enhancement ──
#    1.  Phase decorrelation    : enriches stereo depth by adding natural L/R variation
#    2.  Stereo widening        : enhances mid/side separation for a spacious mix
#    3.  HF smoothing           : refines high-frequency clarity above 12kHz
#    4.  Harmonic enrichment    : adds subtle even harmonics for analog warmth
#    5.  Micro-timing humanizer : introduces natural micro-timing feel
#    6.  Ambience shaping       : adds organic room character to the noise floor
#    ── Pre-Mastering ──
#    7.  Multiband compressor   : tightens dynamics per frequency band
#    8.  Tape saturation        : emulates analog tape warmth and character
#    9.  Glue compressor        : gentle bus compression for mix cohesion
#    10. Mid/Side EQ            : surgical spatial frequency shaping
#    11. Soft clipper            : transparent loudness maximizer
#    12. LUFS normalization     : loudness normalization + true peak limiting
# ============================================================

import numpy as np
import soundfile as sf
import scipy.signal as signal
import argparse
import sys
import os
import tempfile


# ────────────────────────────────────────────────────────────
#  PRESETS
# ────────────────────────────────────────────────────────────

PRESETS = {
    "Custom": None,
    "Suno": {
        "phase": 0.7, "stereo": 1.4, "hf": 0.7, "harmonic": 0.3,
        "jitter": 0.4, "noise": 0.3,
        "multiband": 0.5, "tape": 0.4, "glue": 0.4, "mseq": 0.4, "clip": 0.3,
        "lufs": -14.0,
    },
    "Udio": {
        "phase": 0.6, "stereo": 1.3, "hf": 0.8, "harmonic": 0.2,
        "jitter": 0.3, "noise": 0.25,
        "multiband": 0.4, "tape": 0.35, "glue": 0.35, "mseq": 0.3, "clip": 0.25,
        "lufs": -14.0,
    },
    "Generic AI": {
        "phase": 0.6, "stereo": 1.3, "hf": 0.5, "harmonic": 0.25,
        "jitter": 0.3, "noise": 0.2,
        "multiband": 0.3, "tape": 0.25, "glue": 0.3, "mseq": 0.25, "clip": 0.2,
        "lufs": -14.0,
    },
    "Light Touch": {
        "phase": 0.3, "stereo": 1.1, "hf": 0.3, "harmonic": 0.1,
        "jitter": 0.2, "noise": 0.1,
        "multiband": 0.15, "tape": 0.1, "glue": 0.15, "mseq": 0.1, "clip": 0.1,
        "lufs": -14.0,
    },
}

DEFAULTS = {
    "phase": 0.6, "stereo": 1.3, "hf": 0.5, "harmonic": 0.25,
    "jitter": 0.3, "noise": 0.2,
    "multiband": 0.3, "tape": 0.25, "glue": 0.3, "mseq": 0.25, "clip": 0.2,
    "lufs": -14.0,
}


# ────────────────────────────────────────────────────────────
#  INPUT FORMAT HELPERS
# ────────────────────────────────────────────────────────────

def load_audio(path: str) -> tuple[np.ndarray, int]:
    """Load audio from WAV, FLAC, OGG, or MP3. Returns (float32 ndarray, sample_rate)."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".mp3":
        from pydub import AudioSegment
        seg = AudioSegment.from_mp3(path)
        sr = seg.frame_rate
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2 ** (seg.sample_width * 8 - 1))
        if seg.channels == 2:
            samples = samples.reshape(-1, 2)
        return samples, sr

    audio, sr = sf.read(path, dtype='float32')
    return audio, sr


# ────────────────────────────────────────────────────────────
#  AUDIO ENHANCEMENT
# ────────────────────────────────────────────────────────────

def phase_decorrelation(audio: np.ndarray, sample_rate: int, intensity: float = 0.6) -> np.ndarray:
    """Enrich stereo depth by adding natural L/R phase variation (bass-preserving)."""
    if audio.ndim < 2 or audio.shape[1] < 2:
        return audio

    left = audio[:, 0]
    right = audio[:, 1]

    # Use allpass filter instead of high-pass to shift phase without removing bass
    freq_norm = min(0.02 + intensity * 0.03, 0.09)
    b_ap, a_ap = signal.butter(2, freq_norm, btype='low')
    # Convert lowpass to allpass: allpass = 2*lowpass - original
    lowpassed = signal.lfilter(b_ap, a_ap, right)
    phase_shifted = 2.0 * lowpassed - right

    blend = intensity * 0.25  # reduced from 0.4 to be more subtle
    right_out = right * (1.0 - blend) + phase_shifted * blend

    result = audio.copy()
    result[:, 1] = right_out
    return result


def stereo_widening(audio: np.ndarray, width: float = 1.3) -> np.ndarray:
    """Widen perceived stereo image for a spacious, immersive mix (Mid/Side)."""
    if audio.ndim < 2 or audio.shape[1] < 2:
        return audio

    left = audio[:, 0]
    right = audio[:, 1]

    mid = (left + right) * 0.5
    side = (left - right) * 0.5
    side_widened = side * width

    result = audio.copy()
    result[:, 0] = mid + side_widened
    result[:, 1] = mid - side_widened

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def hf_artifact_smoothing(audio: np.ndarray, sample_rate: int, intensity: float = 0.5) -> np.ndarray:
    """Refine high-frequency clarity by smoothing harsh spectral artifacts above 12kHz."""
    cutoff_hz = 12000
    nyq = sample_rate / 2.0

    if cutoff_hz >= nyq or intensity <= 0:
        return audio

    result = audio.copy()
    freq_norm = cutoff_hz / nyq

    # Use single lowpass and derive HF by subtraction (complementary, phase-coherent)
    b_low, a_low = signal.butter(2, freq_norm, btype='low')

    n_channels = result.shape[1] if audio.ndim > 1 else 1
    for ch in range(n_channels):
        chan = result[:, ch] if audio.ndim > 1 else result

        low_part = signal.lfilter(b_low, a_low, chan)
        high_part = chan - low_part  # complementary: no phase mismatch

        # Gentle smoothing on HF only
        kernel_size = max(3, int(sample_rate * 0.001))
        kernel = np.ones(kernel_size) / kernel_size
        high_smoothed = np.convolve(high_part, kernel, mode='same')

        # Blend smoothed HF back (attenuate harshness, don't boost)
        blended_high = high_part * (1.0 - intensity * 0.5) + high_smoothed * (intensity * 0.5)
        out = low_part + blended_high

        if audio.ndim > 1:
            result[:, ch] = out
        else:
            result = out

    return result


def harmonic_enrichment(audio: np.ndarray, intensity: float = 0.25) -> np.ndarray:
    """Add subtle even harmonics for analog warmth and musical richness."""
    if intensity <= 0:
        return audio

    # Asymmetric soft clipping generates even harmonics (warm, tube-like)
    # instead of tanh which generates harsh odd harmonics
    drive = 1.0 + intensity * 1.5
    driven = audio * drive
    # Asymmetric waveshaper: positive side clips softer than negative
    pos = driven - (driven ** 3) / 3.0  # cubic soft clip (even+odd but gentler)
    neg = np.tanh(driven * 0.8)         # softer saturation on negative
    saturated = np.where(driven >= 0, pos, neg)
    saturated = np.clip(saturated, -1.0, 1.0)
    saturated = saturated / drive  # compensate gain

    blend = intensity * 0.2  # reduced from 0.3 — subtler
    result = audio * (1.0 - blend) + saturated * blend

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def micro_timing_jitter(audio: np.ndarray, sample_rate: int, intensity: float = 0.3) -> np.ndarray:
    """Add natural micro-timing feel around transients for a more human, groovy performance."""
    if intensity <= 0:
        return audio

    result = audio.copy()

    if audio.ndim > 1:
        mono = np.mean(audio, axis=1)
    else:
        mono = audio.copy()

    frame_size = int(sample_rate * 0.01)
    hop = frame_size // 2
    energy = np.array([
        np.sum(mono[i:i + frame_size] ** 2)
        for i in range(0, len(mono) - frame_size, hop)
    ])

    if len(energy) < 3:
        return audio

    threshold = np.mean(energy) + np.std(energy) * 1.5
    peaks, _ = signal.find_peaks(energy, height=threshold, distance=int(0.05 * sample_rate / hop))

    max_shift_samples = int(sample_rate * 0.0005 * intensity)
    if max_shift_samples < 1:
        return audio

    rng = np.random.default_rng(42)
    fade_len = max(16, frame_size // 4)

    for peak_idx in peaks:
        sample_pos = peak_idx * hop
        shift = rng.integers(-max_shift_samples, max_shift_samples + 1)
        if shift == 0:
            continue

        region_start = max(0, sample_pos - frame_size)
        region_end = min(len(result), sample_pos + frame_size)
        region_len = region_end - region_start

        if region_len < abs(shift) * 2 + fade_len * 2:
            continue

        n_ch = audio.shape[1] if audio.ndim > 1 else 1
        for ch in range(n_ch):
            if audio.ndim > 1:
                region = result[region_start:region_end, ch].copy()
            else:
                region = result[region_start:region_end].copy()

            # Shift via linear interpolation (no wrapping)
            indices = np.arange(len(region), dtype=np.float64) - shift
            indices = np.clip(indices, 0, len(region) - 1)
            shifted = np.interp(np.arange(len(region)), indices, region)

            # Crossfade at region boundaries to avoid discontinuities
            fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
            fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
            shifted[:fade_len] = region[:fade_len] * (1.0 - fade_in) + shifted[:fade_len] * fade_in
            shifted[-fade_len:] = region[-fade_len:] * (1.0 - fade_out) + shifted[-fade_len:] * fade_out

            if audio.ndim > 1:
                result[region_start:region_end, ch] = shifted
            else:
                result[region_start:region_end] = shifted

    return result


def spectral_noise_shaping(audio: np.ndarray, sample_rate: int, intensity: float = 0.2) -> np.ndarray:
    """Add organic room ambience and character to the noise floor for a more natural sound."""
    if intensity <= 0:
        return audio

    n_samples = len(audio)
    n_channels = audio.shape[1] if audio.ndim > 1 else 1

    rng = np.random.default_rng(123)
    result = audio.copy()

    for ch in range(n_channels):
        white = rng.standard_normal(n_samples).astype(np.float32)

        b_pink = np.array([0.049922035, -0.095993537, 0.050612699, -0.004709510])
        a_pink = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
        pink = signal.lfilter(b_pink, a_pink, white)

        pink_peak = np.max(np.abs(pink))
        if pink_peak > 0:
            pink = pink / pink_peak

        noise_db = -80.0 + intensity * 30.0
        noise_level = 10.0 ** (noise_db / 20.0)
        pink_scaled = pink * noise_level

        if audio.ndim > 1:
            result[:, ch] = result[:, ch] + pink_scaled
        else:
            result = result + pink_scaled

    return result


# ────────────────────────────────────────────────────────────
#  PRE-MASTERING
# ────────────────────────────────────────────────────────────

def _compress_signal(x: np.ndarray, threshold_db: float, ratio: float,
                     attack_ms: float, release_ms: float, sample_rate: int) -> np.ndarray:
    """Apply dynamic range compression to a 1D signal."""
    threshold = 10.0 ** (threshold_db / 20.0)
    attack_coeff = np.exp(-1.0 / (sample_rate * attack_ms / 1000.0))
    release_coeff = np.exp(-1.0 / (sample_rate * release_ms / 1000.0))

    envelope = np.zeros_like(x)
    env = 0.0
    for i in range(len(x)):
        level = abs(x[i])
        if level > env:
            env = attack_coeff * env + (1.0 - attack_coeff) * level
        else:
            env = release_coeff * env + (1.0 - release_coeff) * level
        envelope[i] = env

    gain = np.ones_like(x)
    mask = envelope > threshold
    if np.any(mask):
        over_db = 20.0 * np.log10(np.clip(envelope[mask] / threshold, 1e-10, None))
        gain_reduction_db = over_db * (1.0 - 1.0 / ratio)
        gain[mask] = 10.0 ** (-gain_reduction_db / 20.0)

    return x * gain


def multiband_compressor(audio: np.ndarray, sample_rate: int, intensity: float = 0.3) -> np.ndarray:
    """3-band compressor: phase-coherent band splitting with independent compression."""
    if intensity <= 0:
        return audio

    nyq = sample_rate / 2.0
    low_cut = min(250.0 / nyq, 0.95)
    high_cut = min(4000.0 / nyq, 0.95)

    if low_cut >= high_cut:
        return audio

    # Phase-coherent splitting: use lowpass and derive other bands by subtraction
    b_lo, a_lo = signal.butter(2, low_cut, btype='low')
    b_lohi, a_lohi = signal.butter(2, high_cut, btype='low')

    # Compression settings per band, scaled by intensity
    threshold_base = -18.0 + (1.0 - intensity) * 10.0  # -18 to -8 dB
    ratio = 1.5 + intensity * 1.5  # 1.5:1 to 3:1 (gentler)

    result = audio.copy()
    n_channels = result.shape[1] if audio.ndim > 1 else 1

    for ch in range(n_channels):
        chan = result[:, ch] if audio.ndim > 1 else result

        # Phase-coherent band splitting
        low = signal.lfilter(b_lo, a_lo, chan)
        below_high = signal.lfilter(b_lohi, a_lohi, chan)
        mid = below_high - low        # mid = lowpass@4k - lowpass@250
        high = chan - below_high       # high = original - lowpass@4k

        # Different attack/release per band
        low_c = _compress_signal(low, threshold_base - 2, ratio, 30.0, 200.0, sample_rate)
        mid_c = _compress_signal(mid, threshold_base, ratio * 0.8, 15.0, 150.0, sample_rate)
        high_c = _compress_signal(high, threshold_base + 2, ratio * 0.6, 5.0, 80.0, sample_rate)

        out = low_c + mid_c + high_c

        if audio.ndim > 1:
            result[:, ch] = out
        else:
            result = out

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def tape_saturation(audio: np.ndarray, intensity: float = 0.25) -> np.ndarray:
    """Emulate analog tape: asymmetric soft saturation + subtle HF rolloff + compression."""
    if intensity <= 0:
        return audio

    drive = 1.0 + intensity * 3.0

    # Asymmetric saturation (tape characteristic: positive peaks clip differently)
    driven = audio * drive
    pos = np.tanh(driven * 1.0)
    neg = np.tanh(driven * 0.85)  # slight asymmetry
    saturated = np.where(driven >= 0, pos, neg)
    saturated = saturated / drive  # compensate gain

    # Blend dry/wet
    blend = intensity * 0.5
    result = audio * (1.0 - blend) + saturated * blend

    # Subtle HF rolloff (tape naturally rolls off highs)
    nyq = 48000.0 / 2.0  # approximate
    rolloff_freq = min(0.9, 15000.0 / nyq)
    if rolloff_freq < 0.95:
        b_roll, a_roll = signal.butter(1, rolloff_freq, btype='low')
        rolloff_blend = intensity * 0.2
        if audio.ndim > 1:
            for ch in range(audio.shape[1]):
                filtered = signal.lfilter(b_roll, a_roll, result[:, ch])
                result[:, ch] = result[:, ch] * (1.0 - rolloff_blend) + filtered * rolloff_blend
        else:
            filtered = signal.lfilter(b_roll, a_roll, result)
            result = result * (1.0 - rolloff_blend) + filtered * rolloff_blend

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def glue_compressor(audio: np.ndarray, sample_rate: int, intensity: float = 0.3) -> np.ndarray:
    """Gentle stereo bus compression for mix cohesion (VCA-style glue)."""
    if intensity <= 0:
        return audio

    threshold_db = -18.0 + (1.0 - intensity) * 10.0  # -18 to -8 dB
    ratio = 1.5 + intensity * 1.5  # 1.5:1 to 3:1
    attack_ms = 30.0 - intensity * 20.0  # 30ms to 10ms
    release_ms = 250.0 - intensity * 100.0  # 250ms to 150ms

    result = audio.copy()

    if audio.ndim > 1:
        # Linked stereo compression: use max envelope across channels
        mono_env = np.max(np.abs(audio), axis=1)
        gain = np.ones_like(mono_env)

        threshold = 10.0 ** (threshold_db / 20.0)
        attack_coeff = np.exp(-1.0 / (sample_rate * attack_ms / 1000.0))
        release_coeff = np.exp(-1.0 / (sample_rate * release_ms / 1000.0))

        env = 0.0
        envelope = np.zeros_like(mono_env)
        for i in range(len(mono_env)):
            level = mono_env[i]
            if level > env:
                env = attack_coeff * env + (1.0 - attack_coeff) * level
            else:
                env = release_coeff * env + (1.0 - release_coeff) * level
            envelope[i] = env

        mask = envelope > threshold
        if np.any(mask):
            over_db = 20.0 * np.log10(np.clip(envelope[mask] / threshold, 1e-10, None))
            gain_reduction_db = over_db * (1.0 - 1.0 / ratio)
            gain[mask] = 10.0 ** (-gain_reduction_db / 20.0)

        for ch in range(audio.shape[1]):
            result[:, ch] = audio[:, ch] * gain
    else:
        result = _compress_signal(audio, threshold_db, ratio, attack_ms, release_ms, sample_rate)

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def midside_eq(audio: np.ndarray, sample_rate: int, intensity: float = 0.25) -> np.ndarray:
    """Mid/Side EQ: tighten bass in center, add air on sides."""
    if intensity <= 0 or audio.ndim < 2 or audio.shape[1] < 2:
        return audio

    left = audio[:, 0]
    right = audio[:, 1]
    mid = (left + right) * 0.5
    side = (left - right) * 0.5

    nyq = sample_rate / 2.0

    # Mid: gentle bass tightening at ~40Hz (sub-bass only, not bass fundamentals)
    hp_freq = min(40.0 / nyq, 0.4)
    b_hp, a_hp = signal.butter(1, hp_freq, btype='high')
    mid_filtered = signal.lfilter(b_hp, a_hp, mid)
    mid = mid * (1.0 - intensity * 0.15) + mid_filtered * (intensity * 0.15)

    # Mid: subtle presence boost 3-5kHz (narrower, less aggressive)
    lo_pres = min(3000.0 / nyq, 0.9)
    hi_pres = min(5000.0 / nyq, 0.95)
    if lo_pres < 0.9 and hi_pres < 0.95:
        b_pres, a_pres = signal.butter(2, [lo_pres, hi_pres], btype='band')
        presence = signal.lfilter(b_pres, a_pres, mid)
        mid = mid + presence * intensity * 0.08  # reduced from 0.15

    # Side: gentle air boost >12kHz (narrower, subtler)
    air_freq = min(12000.0 / nyq, 0.95)
    if air_freq < 0.95:
        b_air, a_air = signal.butter(2, air_freq, btype='high')
        air = signal.lfilter(b_air, a_air, side)
        side = side + air * intensity * 0.15  # reduced from 0.3

    # Side: reduce bass below 120Hz for mono compatibility (gentler)
    side_hp_freq = min(120.0 / nyq, 0.4)
    b_shp, a_shp = signal.butter(1, side_hp_freq, btype='high')
    side_filtered = signal.lfilter(b_shp, a_shp, side)
    side = side * (1.0 - intensity * 0.25) + side_filtered * (intensity * 0.25)

    result = audio.copy()
    result[:, 0] = mid + side
    result[:, 1] = mid - side

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def soft_clipper(audio: np.ndarray, intensity: float = 0.2) -> np.ndarray:
    """Transparent soft clipping for final loudness maximization (+1-2 dB)."""
    if intensity <= 0:
        return audio

    # Drive into the clipper
    drive = 1.0 + intensity * 1.5  # 1.0 to 2.5
    driven = audio * drive

    # Soft clip using a cubic waveshaper (more transparent than tanh)
    threshold = 0.85
    result = np.where(
        np.abs(driven) <= threshold,
        driven,
        np.sign(driven) * (threshold + (1.0 - threshold) * np.tanh(
            (np.abs(driven) - threshold) / (1.0 - threshold)
        ))
    )

    # Compensate gain
    result = result / drive

    # Blend
    blend = intensity * 0.6
    result = audio * (1.0 - blend) + result * blend

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def lufs_normalize(audio: np.ndarray, sample_rate: int, target_lufs: float = -14.0) -> np.ndarray:
    """Normalize to target LUFS with true peak limiting at -1 dBTP."""
    import pyloudnorm as pyln

    meter = pyln.Meter(sample_rate)
    current_lufs = meter.integrated_loudness(audio)

    if np.isinf(current_lufs) or np.isnan(current_lufs):
        return audio

    gain_db = target_lufs - current_lufs
    gain_linear = 10.0 ** (gain_db / 20.0)
    result = audio * gain_linear

    true_peak_limit = 10.0 ** (-1.0 / 20.0)  # -1 dBTP ~ 0.891
    peak = np.max(np.abs(result))
    if peak > true_peak_limit:
        # Soft-knee limiting for samples approaching the ceiling
        knee_start = true_peak_limit * 0.85
        above_knee = np.abs(result) > knee_start
        if np.any(above_knee):
            x = np.abs(result[above_knee])
            # Smooth compression curve from knee_start to true_peak_limit
            compressed = knee_start + (true_peak_limit - knee_start) * np.tanh(
                (x - knee_start) / (true_peak_limit - knee_start)
            )
            result[above_knee] = np.sign(result[above_knee]) * compressed

    # Hard safety clip — never exceed [-1.0, 1.0]
    result = np.clip(result, -1.0, 1.0)

    return result


# ────────────────────────────────────────────────────────────
#  SPECTROGRAM HELPER
# ────────────────────────────────────────────────────────────

def make_spectrogram_figure(audio_before: np.ndarray, audio_after: np.ndarray, sample_rate: int):
    """Create a side-by-side spectrogram comparison figure."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("Agg")

    if audio_before.ndim > 1:
        mono_before = np.mean(audio_before, axis=1)
    else:
        mono_before = audio_before
    if audio_after.ndim > 1:
        mono_after = np.mean(audio_after, axis=1)
    else:
        mono_after = audio_after

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4), dpi=100)
    fig.patch.set_facecolor("#0e1117")

    for ax, data, title in [(ax1, mono_before, "Before"), (ax2, mono_after, "After")]:
        ax.set_facecolor("#0e1117")
        ax.specgram(data, NFFT=2048, Fs=sample_rate, noverlap=1024, cmap="magma", vmin=-100, vmax=0)
        ax.set_title(title, color="white", fontsize=13, fontweight="bold")
        ax.set_xlabel("Time (s)", color="#aaa", fontsize=10)
        ax.set_ylabel("Frequency (Hz)", color="#aaa", fontsize=10)
        ax.tick_params(colors="#888")
        ax.set_ylim(0, min(sample_rate / 2, 20000))

    fig.tight_layout(pad=2.0)
    return fig


# ────────────────────────────────────────────────────────────
#  MAIN PIPELINE
# ────────────────────────────────────────────────────────────

def wash_track(
    input_path: str,
    output_path: str,
    phase_intensity: float = 0.6,
    stereo_width: float = 1.3,
    hf_intensity: float = 0.5,
    harmonic_intensity: float = 0.25,
    jitter_intensity: float = 0.3,
    noise_intensity: float = 0.2,
    multiband_intensity: float = 0.3,
    tape_intensity: float = 0.25,
    glue_intensity: float = 0.3,
    mseq_intensity: float = 0.25,
    clip_intensity: float = 0.2,
    target_lufs: float = -14.0,
    enabled_stages: dict[str, bool] | None = None,
    verbose: bool = True,
    progress_callback=None,
    return_before_after: bool = False,
) -> str | tuple[str, np.ndarray, np.ndarray, int]:

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if verbose:
        print(f"\n  Loading  : {input_path}")

    audio, sr = load_audio(input_path)

    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
        if verbose:
            print("  Mono detected — duplicated to stereo")

    duration = len(audio) / sr
    if verbose:
        print(f"  Duration : {duration:.2f}s  |  Sample rate: {sr} Hz  |  Channels: {audio.shape[1]}")

    audio_before = audio.copy() if return_before_after else None

    steps = [
        # (key, display_name, processing_function)
        # Audio enhancement
        ("phase",     "Stereo depth",         lambda a: phase_decorrelation(a, sr, intensity=phase_intensity)),
        ("stereo",    "Stereo width",         lambda a: stereo_widening(a, width=stereo_width)),
        ("hf",        "HF refinement",        lambda a: hf_artifact_smoothing(a, sr, intensity=hf_intensity)),
        ("harmonic",  "Harmonic enrichment",  lambda a: harmonic_enrichment(a, intensity=harmonic_intensity)),
        ("jitter",    "Timing humanizer",     lambda a: micro_timing_jitter(a, sr, intensity=jitter_intensity)),
        ("noise",     "Ambience shaping",     lambda a: spectral_noise_shaping(a, sr, intensity=noise_intensity)),
        # Pre-mastering
        ("multiband", "Multiband compressor", lambda a: multiband_compressor(a, sr, intensity=multiband_intensity)),
        ("tape",      "Tape saturation",      lambda a: tape_saturation(a, intensity=tape_intensity)),
        ("glue",      "Glue compressor",      lambda a: glue_compressor(a, sr, intensity=glue_intensity)),
        ("mseq",      "Mid/Side EQ",          lambda a: midside_eq(a, sr, intensity=mseq_intensity)),
        ("clip",      "Soft clipper",         lambda a: soft_clipper(a, intensity=clip_intensity)),
        ("lufs",      "LUFS normalization",   lambda a: lufs_normalize(a, sr, target_lufs=target_lufs)),
    ]

    for i, (key, name, fn) in enumerate(steps):
        skipped = enabled_stages is not None and not enabled_stages.get(key, True)
        if verbose:
            tag = " [OFF]" if skipped else ""
            print(f"  [{i+1:2d}/{len(steps)}] {name}{tag} ...")
        if not skipped:
            audio = fn(audio)
        if progress_callback:
            progress_callback((i + 1) / len(steps), name)

    sf.write(output_path, audio, sr, subtype='PCM_16')

    if verbose:
        print(f"\n  Done -> {output_path}\n")

    if return_before_after:
        return output_path, audio_before, audio, sr
    return output_path


def wash_track_bytes(
    input_bytes: bytes,
    filename: str,
    phase_intensity: float = 0.6,
    stereo_width: float = 1.3,
    hf_intensity: float = 0.5,
    harmonic_intensity: float = 0.25,
    jitter_intensity: float = 0.3,
    noise_intensity: float = 0.2,
    multiband_intensity: float = 0.3,
    tape_intensity: float = 0.25,
    glue_intensity: float = 0.3,
    mseq_intensity: float = 0.25,
    clip_intensity: float = 0.2,
    target_lufs: float = -14.0,
    enabled_stages: dict[str, bool] | None = None,
    progress_callback=None,
) -> tuple[bytes, int, float, np.ndarray, np.ndarray]:
    """Process from bytes, return (output_bytes, sample_rate, duration, audio_before, audio_after)."""
    ext = os.path.splitext(filename)[1].lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path + "_washed.wav"

    try:
        result = wash_track(
            input_path=tmp_in_path,
            output_path=tmp_out_path,
            phase_intensity=phase_intensity,
            stereo_width=stereo_width,
            hf_intensity=hf_intensity,
            harmonic_intensity=harmonic_intensity,
            jitter_intensity=jitter_intensity,
            noise_intensity=noise_intensity,
            multiband_intensity=multiband_intensity,
            tape_intensity=tape_intensity,
            glue_intensity=glue_intensity,
            mseq_intensity=mseq_intensity,
            clip_intensity=clip_intensity,
            target_lufs=target_lufs,
            enabled_stages=enabled_stages,
            verbose=False,
            progress_callback=progress_callback,
            return_before_after=True,
        )
        _, audio_before, audio_after, sr = result
        duration = len(audio_after) / sr

        with open(tmp_out_path, "rb") as f:
            out_bytes = f.read()

        return out_bytes, sr, duration, audio_before, audio_after
    finally:
        for p in (tmp_in_path, tmp_out_path):
            if os.path.exists(p):
                os.unlink(p)


# ────────────────────────────────────────────────────────────
#  STREAMLIT UI
# ────────────────────────────────────────────────────────────

def launch_streamlit():
    import streamlit as st

    st.set_page_config(
        page_title="TrackWasher",
        page_icon="\U0001f39b\ufe0f",
        layout="wide",
    )

    st.markdown("""
    <style>
    .main-title { font-size: 2.4rem; font-weight: 700; margin-bottom: 0; }
    .subtitle   { font-size: 1.1rem; color: #888; margin-top: 0; margin-bottom: 1.5rem; }
    .step-card  { background: #1a1a2e; border-radius: 10px; padding: 1rem;
                  margin-bottom: 0.5rem; border-left: 4px solid #e94560; }
    .step-card h4 { margin: 0 0 0.3rem 0; color: #e94560; }
    .step-card p  { margin: 0; color: #ccc; font-size: 0.9rem; }
    .section-label { font-size: 0.85rem; color: #e94560; font-weight: 600;
                     text-transform: uppercase; letter-spacing: 0.05em; margin: 0.8rem 0 0.3rem 0; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-title">TrackWasher</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Pre-mastering & audio enhancement for AI-generated music</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Upload")
        uploaded_files = st.file_uploader(
            "Drop audio file(s) here",
            type=["wav", "flac", "mp3", "ogg"],
            help="WAV, FLAC, MP3, or OGG (stereo or mono). Select multiple files for batch processing.",
            accept_multiple_files=True,
        )

        if uploaded_files:
            for uf in uploaded_files:
                file_size_mb = len(uf.getvalue()) / (1024 * 1024)
                st.caption(f"{uf.name}  —  {file_size_mb:.1f} MB")
        uploaded = uploaded_files[0] if len(uploaded_files) == 1 else None

        st.markdown("---")

        st.subheader("Preset")
        preset_name = st.selectbox(
            "Generator preset",
            list(PRESETS.keys()),
            index=0,
            help="Optimized settings for music from specific AI platforms, or use Custom.",
        )
        preset_vals = PRESETS[preset_name] if PRESETS[preset_name] else DEFAULTS

        st.markdown("---")
        st.subheader("Parameters")

        # ── Audio Enhancement section ──
        st.markdown('<p class="section-label">Audio Enhancement</p>', unsafe_allow_html=True)

        c1, c2 = st.columns([0.07, 0.93])
        en_phase = c1.checkbox("", value=True, key="en_phase", help="Enable/disable this stage")
        phase_i = c2.slider("Stereo Depth", 0.0, 1.0, preset_vals["phase"], 0.05,
                            help="Enriches stereo depth with natural L/R variation.", disabled=not en_phase)

        c1, c2 = st.columns([0.07, 0.93])
        en_stereo = c1.checkbox("", value=True, key="en_stereo", help="Enable/disable this stage")
        stereo_w = c2.slider("Stereo Width", 1.0, 2.0, preset_vals["stereo"], 0.05,
                             help="Widens the stereo image. Above 1.6 may affect mono compatibility.", disabled=not en_stereo)

        c1, c2 = st.columns([0.07, 0.93])
        en_hf = c1.checkbox("", value=True, key="en_hf", help="Enable/disable this stage")
        hf_i = c2.slider("HF Refinement", 0.0, 1.0, preset_vals["hf"], 0.05,
                          help="Smooths and refines high-frequency clarity above 12kHz.", disabled=not en_hf)

        c1, c2 = st.columns([0.07, 0.93])
        en_harmonic = c1.checkbox("", value=True, key="en_harmonic", help="Enable/disable this stage")
        harmonic_i = c2.slider("Harmonic Enrichment", 0.0, 1.0, preset_vals["harmonic"], 0.05,
                               help="Adds warm analog-style harmonics for musical richness.", disabled=not en_harmonic)

        c1, c2 = st.columns([0.07, 0.93])
        en_jitter = c1.checkbox("", value=True, key="en_jitter", help="Enable/disable this stage")
        jitter_i = c2.slider("Timing Humanizer", 0.0, 1.0, preset_vals["jitter"], 0.05,
                             help="Adds natural micro-timing feel for a more human groove.", disabled=not en_jitter)

        c1, c2 = st.columns([0.07, 0.93])
        en_noise = c1.checkbox("", value=True, key="en_noise", help="Enable/disable this stage")
        noise_i = c2.slider("Ambience Shaping", 0.0, 1.0, preset_vals["noise"], 0.05,
                            help="Adds organic room character and natural ambience.", disabled=not en_noise)

        # ── Pre-Mastering section ──
        st.markdown('<p class="section-label">Pre-Mastering</p>', unsafe_allow_html=True)

        c1, c2 = st.columns([0.07, 0.93])
        en_multiband = c1.checkbox("", value=True, key="en_multiband", help="Enable/disable this stage")
        multiband_i = c2.slider("Multiband Compressor", 0.0, 1.0, preset_vals["multiband"], 0.05,
                                help="3-band compression: tightens dynamics per frequency range.", disabled=not en_multiband)

        c1, c2 = st.columns([0.07, 0.93])
        en_tape = c1.checkbox("", value=True, key="en_tape", help="Enable/disable this stage")
        tape_i = c2.slider("Tape Saturation", 0.0, 1.0, preset_vals["tape"], 0.05,
                           help="Analog tape warmth and character.", disabled=not en_tape)

        c1, c2 = st.columns([0.07, 0.93])
        en_glue = c1.checkbox("", value=True, key="en_glue", help="Enable/disable this stage")
        glue_i = c2.slider("Glue Compressor", 0.0, 1.0, preset_vals["glue"], 0.05,
                           help="Gentle bus compression for mix cohesion.", disabled=not en_glue)

        c1, c2 = st.columns([0.07, 0.93])
        en_mseq = c1.checkbox("", value=True, key="en_mseq", help="Enable/disable this stage")
        mseq_i = c2.slider("Mid/Side EQ", 0.0, 1.0, preset_vals["mseq"], 0.05,
                           help="Tighten bass center, add air on sides, presence boost.", disabled=not en_mseq)

        c1, c2 = st.columns([0.07, 0.93])
        en_clip = c1.checkbox("", value=True, key="en_clip", help="Enable/disable this stage")
        clip_i = c2.slider("Soft Clipper", 0.0, 1.0, preset_vals["clip"], 0.05,
                           help="Transparent clipping for extra loudness headroom.", disabled=not en_clip)

        c1, c2 = st.columns([0.07, 0.93])
        en_lufs = c1.checkbox("", value=True, key="en_lufs", help="Enable/disable this stage")
        lufs_target = c2.slider("Target LUFS", -24.0, -8.0, preset_vals["lufs"], 0.5,
                                help="-14 = Spotify/YouTube. -11 = louder. -16 = more dynamic.", disabled=not en_lufs)

        enabled_stages = {
            "phase": en_phase, "stereo": en_stereo, "hf": en_hf,
            "harmonic": en_harmonic, "jitter": en_jitter, "noise": en_noise,
            "multiband": en_multiband, "tape": en_tape, "glue": en_glue,
            "mseq": en_mseq, "clip": en_clip, "lufs": en_lufs,
        }

        has_files = len(uploaded_files) > 0
        is_batch = len(uploaded_files) > 1
        btn_label = f"Wash {len(uploaded_files)} Tracks" if is_batch else "Wash Track"
        process_btn = st.button(btn_label, type="primary", use_container_width=True, disabled=not has_files)

    with col_right:
        st.subheader("Output")

        if process_btn and has_files:
            import zipfile, io as _io

            all_results = []
            total_files = len(uploaded_files)

            for file_idx, uf in enumerate(uploaded_files):
                if is_batch:
                    st.markdown(f"**[{file_idx+1}/{total_files}] {uf.name}**")

                progress_bar = st.progress(0, text=f"Processing {uf.name}...")

                def on_progress(pct, step_name, _idx=file_idx):
                    progress_bar.progress(pct, text=f"{step_name}...")

                try:
                    raw_bytes = uf.getvalue()
                    out_bytes, sr, duration, audio_before, audio_after = wash_track_bytes(
                        input_bytes=raw_bytes,
                        filename=uf.name,
                        phase_intensity=phase_i,
                        stereo_width=stereo_w,
                        hf_intensity=hf_i,
                        harmonic_intensity=harmonic_i,
                        jitter_intensity=jitter_i,
                        noise_intensity=noise_i,
                        multiband_intensity=multiband_i,
                        tape_intensity=tape_i,
                        glue_intensity=glue_i,
                        mseq_intensity=mseq_i,
                        clip_intensity=clip_i,
                        target_lufs=lufs_target,
                        enabled_stages=enabled_stages,
                        progress_callback=on_progress,
                    )
                    progress_bar.progress(1.0, text="Done!")

                    out_name = os.path.splitext(uf.name)[0] + "_washed.wav"
                    all_results.append((out_name, out_bytes, sr, duration, audio_before, audio_after))

                    st.audio(out_bytes, format="audio/wav")
                    st.caption(f"Sample rate: {sr} Hz  |  Duration: {duration:.2f}s")
                    st.download_button(
                        label=f"Download {out_name}",
                        data=out_bytes,
                        file_name=out_name,
                        mime="audio/wav",
                        use_container_width=True,
                        key=f"dl_{file_idx}",
                    )

                    if not is_batch:
                        st.markdown("---")
                        st.subheader("Spectrogram Comparison")
                        fig = make_spectrogram_figure(audio_before, audio_after, sr)
                        st.pyplot(fig)

                except Exception as e:
                    progress_bar.empty()
                    st.error(f"Processing failed for {uf.name}: {e}")

                if is_batch and file_idx < total_files - 1:
                    st.markdown("---")

            # Batch ZIP download
            if is_batch and len(all_results) > 1:
                st.markdown("---")
                zip_buf = _io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for name, data, *_ in all_results:
                        zf.writestr(name, data)
                zip_buf.seek(0)
                st.download_button(
                    label=f"Download all ({len(all_results)} tracks) as ZIP",
                    data=zip_buf.getvalue(),
                    file_name="trackwasher_batch.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="dl_zip",
                )

            if all_results:
                st.success(f"{len(all_results)} track(s) washed successfully.")

        else:
            st.info("Upload audio file(s) and click **Wash Track** to begin.")

        st.markdown("---")
        st.subheader("Processing Chain")

        steps_info = [
            ("Audio Enhancement", [
                ("1. Stereo Depth", "Enriches stereo field with natural L/R variation."),
                ("2. Stereo Width", "Mid/Side expansion for a spacious, immersive mix."),
                ("3. HF Refinement", "Smooths and refines high-frequency clarity."),
                ("4. Harmonic Enrichment", "Adds warm analog-style harmonics."),
                ("5. Timing Humanizer", "Introduces natural micro-timing feel."),
                ("6. Ambience Shaping", "Adds organic room character and depth."),
            ]),
            ("Pre-Mastering", [
                ("7. Multiband Compressor", "3-band dynamics control (low/mid/high)."),
                ("8. Tape Saturation", "Analog tape warmth and character."),
                ("9. Glue Compressor", "Bus compression for mix cohesion."),
                ("10. Mid/Side EQ", "Bass tightening + air boost + presence."),
                ("11. Soft Clipper", "Transparent loudness maximization."),
                ("12. LUFS Normalization", "Loudness normalization + true peak limiting."),
            ]),
        ]
        for section, items in steps_info:
            st.markdown(f'<p class="section-label">{section}</p>', unsafe_allow_html=True)
            for title, desc in items:
                st.markdown(
                    f'<div class="step-card"><h4>{title}</h4><p>{desc}</p></div>',
                    unsafe_allow_html=True,
                )


# ────────────────────────────────────────────────────────────
#  ENTRY POINT
# ────────────────────────────────────────────────────────────

def _is_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if _is_streamlit():
    launch_streamlit()
elif __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrackWasher — Pre-mastering & audio enhancement for AI-generated music")
    parser.add_argument("input", nargs="?", help="Input audio file (WAV, FLAC, MP3, OGG)")
    parser.add_argument("output", nargs="?", help="Output WAV file")
    parser.add_argument("--phase", type=float, default=None, help="Phase decorrelation (0-1)")
    parser.add_argument("--stereo", type=float, default=None, help="Stereo widening (1.0-2.0)")
    parser.add_argument("--hf", type=float, default=None, help="HF smoothing (0-1)")
    parser.add_argument("--harmonic", type=float, default=None, help="Harmonic enrichment (0-1)")
    parser.add_argument("--jitter", type=float, default=None, help="Micro-timing jitter (0-1)")
    parser.add_argument("--noise", type=float, default=None, help="Spectral noise shaping (0-1)")
    parser.add_argument("--multiband", type=float, default=None, help="Multiband compressor (0-1)")
    parser.add_argument("--tape", type=float, default=None, help="Tape saturation (0-1)")
    parser.add_argument("--glue", type=float, default=None, help="Glue compressor (0-1)")
    parser.add_argument("--mseq", type=float, default=None, help="Mid/Side EQ (0-1)")
    parser.add_argument("--clip", type=float, default=None, help="Soft clipper (0-1)")
    parser.add_argument("--lufs", type=float, default=None, help="Target LUFS (e.g. -14)")
    parser.add_argument("--preset", type=str, default=None, choices=["suno", "udio", "generic", "light"],
                        help="Apply a generator preset")
    parser.add_argument("--disable", nargs="+", default=[],
                        choices=["phase", "stereo", "hf", "harmonic", "jitter", "noise",
                                 "multiband", "tape", "glue", "mseq", "clip", "lufs"],
                        help="Disable specific processing stages")

    args = parser.parse_args()

    if args.input and args.output:
        if args.preset:
            preset_map = {"suno": "Suno", "udio": "Udio", "generic": "Generic AI", "light": "Light Touch"}
            vals = PRESETS[preset_map[args.preset]].copy()
        else:
            vals = DEFAULTS.copy()

        for key in ["phase", "stereo", "hf", "harmonic", "jitter", "noise",
                     "multiband", "tape", "glue", "mseq", "clip", "lufs"]:
            cli_val = getattr(args, key, None)
            if cli_val is not None:
                vals[key] = cli_val

        cli_enabled = None
        if args.disable:
            all_keys = ["phase", "stereo", "hf", "harmonic", "jitter", "noise",
                        "multiband", "tape", "glue", "mseq", "clip", "lufs"]
            cli_enabled = {k: (k not in args.disable) for k in all_keys}

        wash_track(
            input_path=args.input,
            output_path=args.output,
            phase_intensity=vals["phase"],
            stereo_width=vals["stereo"],
            hf_intensity=vals["hf"],
            harmonic_intensity=vals["harmonic"],
            jitter_intensity=vals["jitter"],
            noise_intensity=vals["noise"],
            multiband_intensity=vals["multiband"],
            tape_intensity=vals["tape"],
            glue_intensity=vals["glue"],
            mseq_intensity=vals["mseq"],
            clip_intensity=vals["clip"],
            target_lufs=vals["lufs"],
            enabled_stages=cli_enabled,
        )
    else:
        parser.print_help()
        print("\n  Or launch the web UI with:  streamlit run trackwasher.py\n")
        sys.exit(1)
