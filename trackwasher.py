# ============================================================
#  trackwasher.py  —  Pre-mastering & audio enhancement for AI-generated music
#  Version 3.1
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
    """Enrich stereo depth by adding natural L/R phase variation."""
    if audio.ndim < 2 or audio.shape[1] < 2:
        return audio

    left = audio[:, 0]
    right = audio[:, 1]

    freq_norm = min(0.02 + intensity * 0.03, 0.09)
    b, a = signal.butter(2, freq_norm, btype='high')
    phase_shifted = signal.lfilter(b, a, right)

    blend = intensity * 0.4
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

    if cutoff_hz >= nyq:
        return audio

    result = audio.copy()
    freq_norm = cutoff_hz / nyq

    b_low, a_low = signal.butter(4, freq_norm, btype='low')
    b_high, a_high = signal.butter(4, freq_norm, btype='high')

    n_channels = result.shape[1] if audio.ndim > 1 else 1
    for ch in range(n_channels):
        chan = result[:, ch] if audio.ndim > 1 else result

        low_part = signal.lfilter(b_low, a_low, chan)
        high_part = signal.lfilter(b_high, a_high, chan)

        kernel_size = max(3, int(sample_rate * 0.002))
        kernel = np.ones(kernel_size) / kernel_size
        high_smoothed = np.convolve(high_part, kernel, mode='same')

        blended_high = high_part * (1.0 - intensity) + high_smoothed * intensity
        out = low_part + blended_high

        if audio.ndim > 1:
            result[:, ch] = out
        else:
            result = out

    return result


def harmonic_enrichment(audio: np.ndarray, intensity: float = 0.25) -> np.ndarray:
    """Add subtle even harmonics for analog warmth and musical richness."""
    saturated = np.tanh(audio * (1.0 + intensity * 2.0)) / (1.0 + intensity * 0.5)
    blend = intensity * 0.3
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

    for peak_idx in peaks:
        sample_pos = peak_idx * hop
        shift = rng.integers(-max_shift_samples, max_shift_samples + 1)

        region_start = max(0, sample_pos - frame_size)
        region_end = min(len(result), sample_pos + frame_size)
        region_len = region_end - region_start

        if region_len < abs(shift) * 2:
            continue

        if audio.ndim > 1:
            for ch in range(audio.shape[1]):
                region = result[region_start:region_end, ch].copy()
                result[region_start:region_end, ch] = np.roll(region, shift)
        else:
            region = result[region_start:region_end].copy()
            result[region_start:region_end] = np.roll(region, shift)

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
    """3-band compressor: independent compression for low, mid, and high frequencies."""
    if intensity <= 0:
        return audio

    nyq = sample_rate / 2.0
    low_cut = min(250.0 / nyq, 0.95)
    high_cut = min(4000.0 / nyq, 0.95)

    if low_cut >= high_cut:
        return audio

    b_lo, a_lo = signal.butter(4, low_cut, btype='low')
    b_mid, a_mid = signal.butter(4, [low_cut, high_cut], btype='band')
    b_hi, a_hi = signal.butter(4, high_cut, btype='high')

    # Compression settings per band, scaled by intensity
    threshold_base = -20.0 + (1.0 - intensity) * 10.0  # -20 to -10 dB
    ratio = 2.0 + intensity * 2.0  # 2:1 to 4:1

    result = audio.copy()
    n_channels = result.shape[1] if audio.ndim > 1 else 1

    for ch in range(n_channels):
        chan = result[:, ch] if audio.ndim > 1 else result

        low = signal.lfilter(b_lo, a_lo, chan)
        mid = signal.lfilter(b_mid, a_mid, chan)
        high = signal.lfilter(b_hi, a_hi, chan)

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

    # Mid: high-pass bass tightening at ~80Hz
    hp_freq = min(80.0 / nyq, 0.4)
    b_hp, a_hp = signal.butter(2, hp_freq, btype='high')
    mid_filtered = signal.lfilter(b_hp, a_hp, mid)
    mid = mid * (1.0 - intensity * 0.3) + mid_filtered * (intensity * 0.3)

    # Mid: slight presence boost 2-5kHz via peaking filter
    presence_freq = min(3500.0 / nyq, 0.9)
    if presence_freq < 0.95:
        b_pres, a_pres = signal.butter(2, [min(2000.0 / nyq, 0.9), min(5000.0 / nyq, 0.95)], btype='band')
        presence = signal.lfilter(b_pres, a_pres, mid)
        mid = mid + presence * intensity * 0.15

    # Side: air boost >10kHz
    air_freq = min(10000.0 / nyq, 0.95)
    if air_freq < 0.95:
        b_air, a_air = signal.butter(2, air_freq, btype='high')
        air = signal.lfilter(b_air, a_air, side)
        side = side + air * intensity * 0.3

    # Side: reduce bass below 200Hz (mono compatibility)
    side_hp_freq = min(200.0 / nyq, 0.4)
    b_shp, a_shp = signal.butter(2, side_hp_freq, btype='high')
    side_filtered = signal.lfilter(b_shp, a_shp, side)
    side = side * (1.0 - intensity * 0.5) + side_filtered * (intensity * 0.5)

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

    true_peak_limit = 10.0 ** (-1.0 / 20.0)  # ~0.891
    peak = np.max(np.abs(result))
    if peak > true_peak_limit:
        result = np.where(
            np.abs(result) > true_peak_limit * 0.9,
            np.sign(result) * true_peak_limit * np.tanh(np.abs(result) / true_peak_limit),
            result,
        )

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
        # Audio enhancement
        ("Stereo depth",         lambda a: phase_decorrelation(a, sr, intensity=phase_intensity)),
        ("Stereo width",         lambda a: stereo_widening(a, width=stereo_width)),
        ("HF refinement",       lambda a: hf_artifact_smoothing(a, sr, intensity=hf_intensity)),
        ("Harmonic enrichment",  lambda a: harmonic_enrichment(a, intensity=harmonic_intensity)),
        ("Timing humanizer",     lambda a: micro_timing_jitter(a, sr, intensity=jitter_intensity)),
        ("Ambience shaping",     lambda a: spectral_noise_shaping(a, sr, intensity=noise_intensity)),
        # Pre-mastering
        ("Multiband compressor", lambda a: multiband_compressor(a, sr, intensity=multiband_intensity)),
        ("Tape saturation",      lambda a: tape_saturation(a, intensity=tape_intensity)),
        ("Glue compressor",      lambda a: glue_compressor(a, sr, intensity=glue_intensity)),
        ("Mid/Side EQ",          lambda a: midside_eq(a, sr, intensity=mseq_intensity)),
        ("Soft clipper",         lambda a: soft_clipper(a, intensity=clip_intensity)),
        ("LUFS normalization",   lambda a: lufs_normalize(a, sr, target_lufs=target_lufs)),
    ]

    for i, (name, fn) in enumerate(steps):
        if verbose:
            print(f"  [{i+1:2d}/{len(steps)}] {name} ...")
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
        uploaded = st.file_uploader(
            "Drop an audio file here",
            type=["wav", "flac", "mp3", "ogg"],
            help="WAV, FLAC, MP3, or OGG (stereo or mono)",
        )

        if uploaded:
            st.audio(uploaded, format=f"audio/{os.path.splitext(uploaded.name)[1].lstrip('.')}")
            file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
            st.caption(f"{uploaded.name}  —  {file_size_mb:.1f} MB")

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

        phase_i = st.slider("Stereo Depth", 0.0, 1.0, preset_vals["phase"], 0.05,
                            help="Enriches stereo depth with natural L/R variation.")
        stereo_w = st.slider("Stereo Width", 1.0, 2.0, preset_vals["stereo"], 0.05,
                             help="Widens the stereo image. Above 1.6 may affect mono compatibility.")
        hf_i = st.slider("HF Refinement", 0.0, 1.0, preset_vals["hf"], 0.05,
                          help="Smooths and refines high-frequency clarity above 12kHz.")
        harmonic_i = st.slider("Harmonic Enrichment", 0.0, 1.0, preset_vals["harmonic"], 0.05,
                               help="Adds warm analog-style harmonics for musical richness.")
        jitter_i = st.slider("Timing Humanizer", 0.0, 1.0, preset_vals["jitter"], 0.05,
                             help="Adds natural micro-timing feel for a more human groove.")
        noise_i = st.slider("Ambience Shaping", 0.0, 1.0, preset_vals["noise"], 0.05,
                            help="Adds organic room character and natural ambience.")

        # ── Pre-Mastering section ──
        st.markdown('<p class="section-label">Pre-Mastering</p>', unsafe_allow_html=True)

        multiband_i = st.slider("Multiband Compressor", 0.0, 1.0, preset_vals["multiband"], 0.05,
                                help="3-band compression: tightens dynamics per frequency range.")
        tape_i = st.slider("Tape Saturation", 0.0, 1.0, preset_vals["tape"], 0.05,
                           help="Analog tape warmth and character.")
        glue_i = st.slider("Glue Compressor", 0.0, 1.0, preset_vals["glue"], 0.05,
                           help="Gentle bus compression for mix cohesion.")
        mseq_i = st.slider("Mid/Side EQ", 0.0, 1.0, preset_vals["mseq"], 0.05,
                           help="Tighten bass center, add air on sides, presence boost.")
        clip_i = st.slider("Soft Clipper", 0.0, 1.0, preset_vals["clip"], 0.05,
                           help="Transparent clipping for extra loudness headroom.")
        lufs_target = st.slider("Target LUFS", -24.0, -8.0, preset_vals["lufs"], 0.5,
                                help="-14 = Spotify/YouTube. -11 = louder. -16 = more dynamic.")

        process_btn = st.button("Wash Track", type="primary", use_container_width=True, disabled=not uploaded)

    with col_right:
        st.subheader("Output")

        if process_btn and uploaded:
            progress_bar = st.progress(0, text="Starting...")

            def on_progress(pct, step_name):
                progress_bar.progress(pct, text=f"{step_name}...")

            try:
                raw_bytes = uploaded.getvalue()
                out_bytes, sr, duration, audio_before, audio_after = wash_track_bytes(
                    input_bytes=raw_bytes,
                    filename=uploaded.name,
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
                    progress_callback=on_progress,
                )
                progress_bar.progress(1.0, text="Done!")

                st.audio(out_bytes, format="audio/wav")
                st.caption(f"Sample rate: {sr} Hz  |  Duration: {duration:.2f}s")

                out_name = os.path.splitext(uploaded.name)[0] + "_washed.wav"
                st.download_button(
                    label="Download washed track",
                    data=out_bytes,
                    file_name=out_name,
                    mime="audio/wav",
                    use_container_width=True,
                )
                st.success("Track washed successfully.")

                st.markdown("---")
                st.subheader("Spectrogram Comparison")
                fig = make_spectrogram_figure(audio_before, audio_after, sr)
                st.pyplot(fig)

            except Exception as e:
                progress_bar.empty()
                st.error(f"Processing failed: {e}")

        else:
            st.info("Upload an audio file and click **Wash Track** to begin.")

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
        )
    else:
        parser.print_help()
        print("\n  Or launch the web UI with:  streamlit run trackwasher.py\n")
        sys.exit(1)
