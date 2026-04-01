# ============================================================
#  trackwasher.py  —  AI Fingerprint Remover for WAV files
#
#  INSTALL:
#    pip install numpy scipy soundfile streamlit
#
#  CLI USAGE:
#    python trackwasher.py input.wav output.wav
#    python trackwasher.py input.wav output.wav --phase 0.8 --stereo 1.4 --hf 0.6 --harmonic 0.3
#
#  STREAMLIT UI:
#    streamlit run trackwasher.py
#
#  PROCESSING CHAIN:
#    1. Phase decorrelation  : breaks L/R symmetry left by neural vocoders
#    2. Stereo widening      : enhances mid/side separation for natural feel
#    3. HF artifact smoothing: targets repetitive spectral patterns >12kHz
#    4. Harmonic enrichment  : adds subtle even harmonics for analog warmth
# ============================================================

import numpy as np
import soundfile as sf
import scipy.signal as signal
import argparse
import sys
import os
import tempfile
import io


# ────────────────────────────────────────────────────────────
#  PROCESSING FUNCTIONS
# ────────────────────────────────────────────────────────────

def phase_decorrelation(audio: np.ndarray, sample_rate: int, intensity: float = 0.6) -> np.ndarray:
    """Break L/R symmetry left by neural vocoders via randomized all-pass phase shifts."""
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
    """Amplify the Side signal to widen perceived stereo image (Mid/Side technique)."""
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
    """Add subtle even harmonics via soft-clip saturation (analog warmth simulation)."""
    saturated = np.tanh(audio * (1.0 + intensity * 2.0)) / (1.0 + intensity * 0.5)
    blend = intensity * 0.3
    result = audio * (1.0 - blend) + saturated * blend

    peak = np.max(np.abs(result))
    if peak > 0.99:
        result = result / peak * 0.99
    return result


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
    verbose: bool = True,
    progress_callback=None,
) -> str:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if verbose:
        print(f"\n  Loading  : {input_path}")

    audio, sr = sf.read(input_path, dtype='float32')

    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
        if verbose:
            print("  Mono detected — duplicated to stereo")

    duration = len(audio) / sr
    if verbose:
        print(f"  Duration : {duration:.2f}s  |  Sample rate: {sr} Hz  |  Channels: {audio.shape[1]}")

    steps = [
        ("Phase decorrelation", lambda a: phase_decorrelation(a, sr, intensity=phase_intensity)),
        ("Stereo widening", lambda a: stereo_widening(a, width=stereo_width)),
        ("HF artifact smoothing", lambda a: hf_artifact_smoothing(a, sr, intensity=hf_intensity)),
        ("Harmonic enrichment", lambda a: harmonic_enrichment(a, intensity=harmonic_intensity)),
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

    return output_path


def wash_track_bytes(
    input_bytes: bytes,
    filename: str,
    phase_intensity: float = 0.6,
    stereo_width: float = 1.3,
    hf_intensity: float = 0.5,
    harmonic_intensity: float = 0.25,
    progress_callback=None,
) -> tuple[bytes, int, float]:
    """Process from bytes, return (output_bytes, sample_rate, duration)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".wav", "_washed.wav")

    try:
        wash_track(
            input_path=tmp_in_path,
            output_path=tmp_out_path,
            phase_intensity=phase_intensity,
            stereo_width=stereo_width,
            hf_intensity=hf_intensity,
            harmonic_intensity=harmonic_intensity,
            verbose=False,
            progress_callback=progress_callback,
        )
        audio, sr = sf.read(tmp_out_path, dtype='float32')
        duration = len(audio) / sr

        with open(tmp_out_path, "rb") as f:
            out_bytes = f.read()

        return out_bytes, sr, duration
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
        page_icon="🎛️",
        layout="wide",
    )

    # --- Custom CSS ---
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #888;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .step-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #e94560;
    }
    .step-card h4 { margin: 0 0 0.3rem 0; color: #e94560; }
    .step-card p  { margin: 0; color: #ccc; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

    # --- Header ---
    st.markdown('<p class="main-title">TrackWasher</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Remove AI fingerprints from your audio tracks</p>', unsafe_allow_html=True)

    # --- Layout: controls left, output right ---
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Upload")
        uploaded = st.file_uploader(
            "Drop a WAV file here",
            type=["wav"],
            help="Stereo or mono WAV (16-bit or 32-bit float)",
        )

        if uploaded:
            st.audio(uploaded, format="audio/wav")
            file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
            st.caption(f"{uploaded.name}  —  {file_size_mb:.1f} MB")

        st.markdown("---")
        st.subheader("Parameters")

        phase_i = st.slider(
            "Phase Decorrelation",
            min_value=0.0, max_value=1.0, value=0.6, step=0.05,
            help="Breaks L/R symmetry left by neural vocoders. Higher = more separation.",
        )
        stereo_w = st.slider(
            "Stereo Widening",
            min_value=1.0, max_value=2.0, value=1.3, step=0.05,
            help="Widens stereo image via Mid/Side. Above 1.6 may cause mono compatibility issues.",
        )
        hf_i = st.slider(
            "HF Artifact Smoothing",
            min_value=0.0, max_value=1.0, value=0.5, step=0.05,
            help="Smooths repetitive spectral patterns >12kHz left by HiFi-GAN / WaveNet.",
        )
        harmonic_i = st.slider(
            "Harmonic Enrichment",
            min_value=0.0, max_value=1.0, value=0.25, step=0.05,
            help="Adds subtle even harmonics for analog warmth. Cosmetic but effective.",
        )

        process_btn = st.button("Wash Track", type="primary", use_container_width=True, disabled=not uploaded)

    with col_right:
        st.subheader("Output")

        if process_btn and uploaded:
            progress_bar = st.progress(0, text="Starting...")

            def on_progress(pct, step_name):
                progress_bar.progress(pct, text=f"{step_name}...")

            try:
                raw_bytes = uploaded.getvalue()
                out_bytes, sr, duration = wash_track_bytes(
                    input_bytes=raw_bytes,
                    filename=uploaded.name,
                    phase_intensity=phase_i,
                    stereo_width=stereo_w,
                    hf_intensity=hf_i,
                    harmonic_intensity=harmonic_i,
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

            except Exception as e:
                progress_bar.empty()
                st.error(f"Processing failed: {e}")

        else:
            st.info("Upload a WAV file and click **Wash Track** to begin.")

        # --- Processing chain explanation ---
        st.markdown("---")
        st.subheader("Processing Chain")

        steps_info = [
            ("1. Phase Decorrelation", "Breaks L/R symmetry left by neural vocoders — makes the stereo field sound natural."),
            ("2. Stereo Widening", "Enhances Mid/Side separation for a more 'live' feel and less 'generated' stereo image."),
            ("3. HF Artifact Smoothing", "Targets repetitive spectral patterns >12kHz left by HiFi-GAN / WaveNet (Suno, Udio)."),
            ("4. Harmonic Enrichment", "Adds subtle even harmonics to simulate analog warmth and organic imperfection."),
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
    """Detect if we're running inside `streamlit run`."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if _is_streamlit():
    launch_streamlit()
elif __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrackWasher — Remove AI fingerprints from WAV files")
    parser.add_argument("input", nargs="?", help="Input WAV file")
    parser.add_argument("output", nargs="?", help="Output WAV file")
    parser.add_argument("--phase", type=float, default=0.6, help="Phase decorrelation intensity (0-1)")
    parser.add_argument("--stereo", type=float, default=1.3, help="Stereo widening factor (1.0-2.0)")
    parser.add_argument("--hf", type=float, default=0.5, help="HF smoothing intensity (0-1)")
    parser.add_argument("--harmonic", type=float, default=0.25, help="Harmonic enrichment intensity (0-1)")

    args = parser.parse_args()

    if args.input and args.output:
        wash_track(
            input_path=args.input,
            output_path=args.output,
            phase_intensity=args.phase,
            stereo_width=args.stereo,
            hf_intensity=args.hf,
            harmonic_intensity=args.harmonic,
        )
    else:
        parser.print_help()
        print("\n  Or launch the web UI with:  streamlit run trackwasher.py\n")
        sys.exit(1)
