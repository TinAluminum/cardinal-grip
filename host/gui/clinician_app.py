# host/gui/clinician_app.py

import os
import sys
import time
import csv
from datetime import datetime
from statistics import mean

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from fsr_reader import FSRReader  # noqa: E402


def main():
    st.set_page_config(page_title="Cardinal Grip – Clinician GUI", layout="wide")
    st.title("Cardinal Grip – Clinician Dashboard")

    port = st.sidebar.text_input("Serial port", "/dev/cu.usbserial-0001")
    baud = st.sidebar.number_input("Baud rate", value=115200, step=1200)
    session_duration = st.sidebar.number_input(
        "Session duration (seconds)", value=30, min_value=5, max_value=300
    )
    target_min = st.sidebar.slider("Target band (min)", 0, 4095, 1200)
    target_max = st.sidebar.slider("Target band (max)", 0, 4095, 2000)

    data_dir = os.path.join(os.path.dirname(ROOT), "data", "logs")
    os.makedirs(data_dir, exist_ok=True)

    if "session_data" not in st.session_state:
        st.session_state.session_data = []

    col1, col2 = st.columns(2)
    status_placeholder = col1.empty()
    summary_placeholder = col2.empty()
    chart_placeholder = st.empty()

    if st.button("Run session"):
        st.session_state.session_data = []

        try:
            reader = FSRReader(port=port, baud=baud)
            status_placeholder.success(f"Connected to {port} at {baud} baud.")
        except Exception as e:
            status_placeholder.error(f"Failed to open {port}: {e}")
            return

        start_time = time.time()
        end_time = start_time + session_duration

        with st.spinner("Recording session..."):
            while time.time() < end_time:
                val = reader.read()
                t = time.time() - start_time
                if val is not None:
                    st.session_state.session_data.append((t, val))
                    chart_placeholder.line_chart(
                        [v for _, v in st.session_state.session_data[-200:]]
                    )
                time.sleep(0.02)

        reader.close()
        status_placeholder.success("Session completed ✅")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(data_dir, f"session_{ts}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "force_adc"])
            for t, v in st.session_state.session_data:
                writer.writerow([t, v])

        values = [v for _, v in st.session_state.session_data]
        if values:
            max_force = max(values)
            avg_force = mean(values)
            in_band = [v for v in values if target_min <= v <= target_max]
            pct_in_band = 100 * len(in_band) / len(values)

            summary_placeholder.markdown(
                f"""
                **Session Summary**

                * Samples: `{len(values)}`
                * Max force: `{max_force}` ADC units  
                * Mean force: `{int(avg_force)}` ADC units  
                * Time in target band ({target_min}–{target_max}): `{pct_in_band:.1f}%`  
                * Saved to: `{csv_path}`
                """
            )
        else:
            summary_placeholder.warning("No valid data captured.")


if __name__ == "__main__":
    main()
