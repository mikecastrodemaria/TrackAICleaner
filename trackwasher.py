# ============================================================
#  trackwasher.py  —  AI Fingerprint Remover for audio files
#
#  INSTALL:
#    pip install numpy scipy soundfile streamlit pyloudnorm matplotlib pydub
#
#  CLI USAGE:
#    python trackwasher.py input.wav output.wav
#    python trackwasher.py input.wav output.wav --preset suno
#    python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.4 --hf 0.6 --harmonic 0.3 --jitter 0.4 --noise 0.3 --lufs -14
#
#  STREAMLIT UI:
#    streamlit run trackwasher.py
#
#  PROCESSING CHAIN:
#    1. Phase decorrelation   : breaks L/R symmetry left by neural vocoders
#    2. Stereo widening       : enhances mid/side separation for natural feel
#    3. HF artifact smoothing : targets repetitive spectral patterns >12kHz
#    4. Harmonic enrichment   : adds subtle even harmonics for analog warmth
#    5. Micro-timing jitter   : breaks perfect grid placement of AI generators
#    6. Spectral noise shaping: masks unnaturally clean AI noise floor
#    7. LUFS normalization    : normalizes loudness to broadcast/streaming standard
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
        "jitter": 0.4, "noise": 0.3, "lufs": -14.0,
    },
    "Udio": {
        "phase": 0.6, "stereo": 1.3, "hf": 0.8, "harmonic": 0.2,
        "jitter": 0.3, "noise": 0.25, "lufs": -14.0,
    },
    "Generic AI": {
        "phase": 0.6, "stereo": 1.3, "hf": 0.5, "harmonic": 0.25,
        "jitter": 0.3, "noise": 0.2, "lufs": -14.0,
    },
    "Light Touch": {
        "phase": 0.3, "stereo": 1.1, "hf": 0.3, "harmonic": 0.1,
        "jitter": 0.2, "noise": 0.1, "lufs": -14.0,
    },
}

DEFAULTS = {
    "phase": 0.6, "stereo": 1.3, "hf": 0.5, "harmonic": 0.25,
    "jitter": 0.3, "noise": 0.2, "lufs": -14.0,
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

    # soundfile handles WAV, FLAC, OGG
    audio, sr = sf.read(path, dtype='float32')
    return audio, sr


# ────────────────────────────────────────────────────────────
#  PROCESSING FUNCTIONS
# ────────────────────────────────────────────────────────────

def phase_decorrelation(audio: np.ndarray, sample_rate: int, intensity: float = 0.6) -> np.ndarray:
    """Break L/R symmetry left by neural vocoders via all-pass phase shifts."""
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
    """Amplify the Side signal to widen perceived stereo image (Mid/Side)."""
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
    """Smooth repetitive spectral comb patterns >12kHz left by mel-spectrogram inversion."""
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
    """Add subtle even harmonics via soft-clip saturation (analog warmth)."""
    saturated = np.tanh(audio * (1.0 + intensity * 2.0)) / (1.0 + intensity * 0.5)
    blend = intensity * 0.3
    result = audio * (1.0 - blend) + saturated * blend

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


def micro_timing_jitter(audio: np.ndarray, sample_rate: int, intensity: float = 0.3) -> np.ndarray:
    """Apply sub-ms random timing shifts around transients to break AI grid perfection."""
    if intensity <= 0:
        return audio

    result = audio.copy()

    # Work on mono mix for transient detection
    if audio.ndim > 1:
        mono = np.mean(audio, axis=1)
    else:
        mono = audio.copy()

    # Compute energy envelope
    frame_size = int(sample_rate * 0.01)  # 10ms frames
    hop = frame_size // 2
    energy = np.array([
        np.sum(mono[i:i + frame_size] ** 2)
        for i in range(0, len(mono) - frame_size, hop)
    ])

    if len(energy) < 3:
        return audio

    # Find transient peaks
    threshold = np.mean(energy) + np.std(energy) * 1.5
    peaks, _ = signal.find_peaks(energy, height=threshold, distance=int(0.05 * sample_rate / hop))

    # Max jitter: ±0.5ms scaled by intensity
    max_shift_samples = int(sample_rate * 0.0005 * intensity)
    if max_shift_samples < 1:
        return audio

    rng = np.random.default_rng(42)

    for peak_idx in peaks:
        sample_pos = peak_idx * hop
        shift = rng.integers(-max_shift_samples, max_shift_samples + 1)

        # Define a small region around the transient to shift
        region_start = max(0, sample_pos - frame_size)
        region_end = min(len(result), sample_pos + frame_size)
        region_len = region_end - region_start

        if region_len < abs(shift) * 2:
            continue

        # Circular shift the region for each channel
        if audio.ndim > 1:
            for ch in range(audio.shape[1]):
                region = result[region_start:region_end, ch].copy()
                result[region_start:region_end, ch] = np.roll(region, shift)
        else:
            region = result[region_start:region_end].copy()
            result[region_start:region_end] = np.roll(region, shift)

    return result


def spectral_noise_shaping(audio: np.ndarray, sample_rate: int, intensity: float = 0.2) -> np.ndarray:
    """Inject low-level pink noise to mask the unnaturally clean AI noise floor."""
    if intensity <= 0:
        return audio

    n_samples = len(audio)
    n_channels = audio.shape[1] if audio.ndim > 1 else 1

    rng = np.random.default_rng(123)

    result = audio.copy()

    for ch in range(n_channels):
        # Generate pink noise via Voss-McCartney algorithm (simplified)
        white = rng.standard_normal(n_samples).astype(np.float32)

        # Shape white noise to pink (1/f) via IIR filter
        # Paul Kellet's filter coefficients for pink noise
        b_pink = np.array([0.049922035, -0.095993537, 0.050612699, -0.004709510])
        a_pink = np.array([1.0, -2.494956002, 2.017265875, -0.522189400])
        pink = signal.lfilter(b_pink, a_pink, white)

        # Normalize pink noise
        pink_peak = np.max(np.abs(pink))
        if pink_peak > 0:
            pink = pink / pink_peak

        # Scale: intensity 1.0 = -60 dB, intensity 0.0 = silence
        # Range: -80 dB (very subtle) to -50 dB (noticeable)
        noise_db = -80.0 + intensity * 30.0
        noise_level = 10.0 ** (noise_db / 20.0)
        pink_scaled = pink * noise_level

        if audio.ndim > 1:
            result[:, ch] = result[:, ch] + pink_scaled
        else:
            result = result + pink_scaled

    return result


def lufs_normalize(audio: np.ndarray, sample_rate: int, target_lufs: float = -14.0) -> np.ndarray:
    """Normalize to target LUFS with true peak limiting at -1 dBTP."""
    import pyloudnorm as pyln

    meter = pyln.Meter(sample_rate)

    # Measure current loudness
    current_lufs = meter.integrated_loudness(audio)

    if np.isinf(current_lufs) or np.isnan(current_lufs):
        return audio

    # Apply gain to reach target
    gain_db = target_lufs - current_lufs
    gain_linear = 10.0 ** (gain_db / 20.0)
    result = audio * gain_linear

    # True peak limiter at -1 dBTP
    true_peak_limit = 10.0 ** (-1.0 / 20.0)  # ~0.891
    peak = np.max(np.abs(result))
    if peak > true_peak_limit:
        # Soft limiting via tanh compression on peaks above threshold
        mask = np.abs(result) > true_peak_limit * 0.9
        if np.any(mask):
            # Compress the signal above threshold
            ratio = true_peak_limit / peak
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

    # Use mono for display
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

    # Force stereo
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
        if verbose:
            print("  Mono detected — duplicated to stereo")

    duration = len(audio) / sr
    if verbose:
        print(f"  Duration : {duration:.2f}s  |  Sample rate: {sr} Hz  |  Channels: {audio.shape[1]}")

    audio_before = audio.copy() if return_before_after else None

    steps = [
        ("Phase decorrelation", lambda a: phase_decorrelation(a, sr, intensity=phase_intensity)),
        ("Stereo widening", lambda a: stereo_widening(a, width=stereo_width)),
        ("HF artifact smoothing", lambda a: hf_artifact_smoothing(a, sr, intensity=hf_intensity)),
        ("Harmonic enrichment", lambda a: harmonic_enrichment(a, intensity=harmonic_intensity)),
        ("Micro-timing jitter", lambda a: micro_timing_jitter(a, sr, intensity=jitter_intensity)),
        ("Spectral noise shaping", lambda a: spectral_noise_shaping(a, sr, intensity=noise_intensity)),
        ("LUFS normalization", lambda a: lufs_normalize(a, sr, target_lufs=target_lufs)),
    ]

    for i, (name, fn) in enumerate(steps):
        if verbose:
            print(f"  [{i+1}/{len(steps)}] {name} ...")
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-title">TrackWasher</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Remove AI fingerprints from your audio tracks</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Left column: upload + controls ──
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

        # ── Preset selector ──
        st.subheader("Preset")
        preset_name = st.selectbox(
            "Generator preset",
            list(PRESETS.keys()),
            index=0,
            help="Select a preset tuned for a specific AI generator, or use Custom for manual control.",
        )

        preset_vals = PRESETS[preset_name] if PRESETS[preset_name] else DEFAULTS

        st.markdown("---")
        st.subheader("Parameters")

        phase_i = st.slider(
            "Phase Decorrelation", 0.0, 1.0, preset_vals["phase"], 0.05,
            help="Breaks L/R symmetry. Higher = more separation.",
        )
        stereo_w = st.slider(
            "Stereo Widening", 1.0, 2.0, preset_vals["stereo"], 0.05,
            help="Widens stereo image. Above 1.6 may cause mono issues.",
        )
        hf_i = st.slider(
            "HF Artifact Smoothing", 0.0, 1.0, preset_vals["hf"], 0.05,
            help="Smooths repetitive patterns >12kHz.",
        )
        harmonic_i = st.slider(
            "Harmonic Enrichment", 0.0, 1.0, preset_vals["harmonic"], 0.05,
            help="Adds analog warmth via soft saturation.",
        )
        jitter_i = st.slider(
            "Micro-Timing Jitter", 0.0, 1.0, preset_vals["jitter"], 0.05,
            help="Breaks perfect AI grid timing around transients.",
        )
        noise_i = st.slider(
            "Spectral Noise Shaping", 0.0, 1.0, preset_vals["noise"], 0.05,
            help="Adds subtle pink noise to mask clean AI noise floor.",
        )
        lufs_target = st.slider(
            "Target LUFS", -24.0, -8.0, preset_vals["lufs"], 0.5,
            help="Loudness normalization target. -14 = Spotify/YouTube standard.",
        )

        process_btn = st.button("Wash Track", type="primary", use_container_width=True, disabled=not uploaded)

    # ── Right column: output ──
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

                # ── Spectrogram comparison ──
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
            ("1. Phase Decorrelation", "Breaks L/R symmetry left by neural vocoders."),
            ("2. Stereo Widening", "Mid/Side expansion for a more organic stereo image."),
            ("3. HF Artifact Smoothing", "Targets spectral combs >12kHz (HiFi-GAN/WaveNet)."),
            ("4. Harmonic Enrichment", "Soft saturation adds analog warmth."),
            ("5. Micro-Timing Jitter", "Breaks perfect grid timing around transients."),
            ("6. Spectral Noise Shaping", "Pink noise masks the clean AI noise floor."),
            ("7. LUFS Normalization", "Loudness normalization + true peak limiting."),
        ]
        for title, desc in steps_info:
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
    parser = argparse.ArgumentParser(description="TrackWasher — Remove AI fingerprints from audio files")
    parser.add_argument("input", nargs="?", help="Input audio file (WAV, FLAC, MP3, OGG)")
    parser.add_argument("output", nargs="?", help="Output WAV file")
    parser.add_argument("--phase", type=float, default=None, help="Phase decorrelation intensity (0-1)")
    parser.add_argument("--stereo", type=float, default=None, help="Stereo widening factor (1.0-2.0)")
    parser.add_argument("--hf", type=float, default=None, help="HF smoothing intensity (0-1)")
    parser.add_argument("--harmonic", type=float, default=None, help="Harmonic enrichment intensity (0-1)")
    parser.add_argument("--jitter", type=float, default=None, help="Micro-timing jitter intensity (0-1)")
    parser.add_argument("--noise", type=float, default=None, help="Spectral noise shaping intensity (0-1)")
    parser.add_argument("--lufs", type=float, default=None, help="Target LUFS level (e.g. -14)")
    parser.add_argument("--preset", type=str, default=None, choices=["suno", "udio", "generic", "light"],
                        help="Apply a generator preset")

    args = parser.parse_args()

    if args.input and args.output:
        # Resolve preset + overrides
        if args.preset:
            preset_map = {"suno": "Suno", "udio": "Udio", "generic": "Generic AI", "light": "Light Touch"}
            vals = PRESETS[preset_map[args.preset]].copy()
        else:
            vals = DEFAULTS.copy()

        # CLI overrides take priority
        if args.phase is not None:    vals["phase"] = args.phase
        if args.stereo is not None:   vals["stereo"] = args.stereo
        if args.hf is not None:       vals["hf"] = args.hf
        if args.harmonic is not None: vals["harmonic"] = args.harmonic
        if args.jitter is not None:   vals["jitter"] = args.jitter
        if args.noise is not None:    vals["noise"] = args.noise
        if args.lufs is not None:     vals["lufs"] = args.lufs

        wash_track(
            input_path=args.input,
            output_path=args.output,
            phase_intensity=vals["phase"],
            stereo_width=vals["stereo"],
            hf_intensity=vals["hf"],
            harmonic_intensity=vals["harmonic"],
            jitter_intensity=vals["jitter"],
            noise_intensity=vals["noise"],
            target_lufs=vals["lufs"],
        )
    else:
        parser.print_help()
        print("\n  Or launch the web UI with:  streamlit run trackwasher.py\n")
        sys.exit(1)
