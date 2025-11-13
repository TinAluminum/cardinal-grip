# gui/patient_app.py

import os
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from websocket import create_connection, WebSocketConnectionClosedException

st.set_page_config(page_title="Cardinal Grip – Patient GUI", layout="wide")

st.title("Cardinal Grip – Patient Training")

st.markdown(
    "This page shows **live finger pressures** from the ESP32 grip ball and "
    "records a rehab session for later clinician review."
)

# --- Sidebar controls ---------------------------------------------------------

default_uri = "ws://192.168.4.1/ws"  # change if your ESP32 IP/route is different
ws_uri = st.sidebar.text_input("ESP32 WebSocket URL", default_uri)

threshold = st.sidebar.number_input(
    "Training threshold (ADC units, 0–4095)", min_value=0, max_value=4095, value=2000
)

session_duration = st.sidebar.number_input(
    "Max session duration (seconds)", min_value=5, max_value=600, value=120
)

col_start, col_stop = st.sidebar.columns(2)

if "running" not in st.session_state:
    st.session_state.running = False

if col_start.button("Start session"):
    st.session_state.running = True
if col_stop.button("Stop session"):
    st.session_state.running = False

# --- Placeholders for dynamic UI ---------------------------------------------

status_box = st.empty()
plot_box = st.empty()
info_box = st.empty()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


def run_session():
    """Connect to ESP32 WebSocket and stream a single rehab session."""

    try:
        ws = create_connection(ws_uri, timeout=5)
    except Exception as e:
        status_box.error(f"Failed to connect to {ws_uri}: {e}")
        st.session_state.running = False
        return

    status_box.success(f"Connected to {ws_uri}")
    data_rows = []
    start_time = time.time()
    presses_over_threshold = 0

    try:
        while st.session_state.running:
            # Stop if session exceeds max duration
            t = time.time() - start_time
            if t > session_duration:
                status_box.warning("Max session duration reached – stopping.")
                break

            try:
                msg = ws.recv()  # blocking read
            except WebSocketConnectionClosedException:
                status_box.error("WebSocket connection closed by ESP32.")
                break
            except Exception as e:
                status_box.error(f"WebSocket error: {e}")
                break

            msg = msg.strip()
            if not msg:
                continue

            # Expect e.g. "1500,2147,2473,2659"
            try:
                vals = [int(x) for x in msg.split(",")]
            except ValueError:
                # Skip malformed line
                status_box.warning(f"Received malformed message: {msg}")
                continue

            timestamp = t
            row = [timestamp] + vals
            data_rows.append(row)

            # Convert to DataFrame for plotting
            n_fingers = len(vals)
            col_names = ["time"] + [f"F{i+1}" for i in range(n_fingers)]
            df = pd.DataFrame(data_rows, columns=col_names)

            # Count "press" if any finger crosses threshold
            if any(v >= threshold for v in vals):
                presses_over_threshold += 1

            # Build plot
            fig = go.Figure()
            for i in range(n_fingers):
                col = f"F{i+1}"
                fig.add_trace(
                    go.Scatter(
                        x=df["time"],
                        y=df[col],
                        mode="lines",
                        name=col,
                    )
                )

            # Threshold line
            fig.add_hline(
                y=threshold, line_dash="dash", line_color="red", annotation_text="Threshold"
            )

            fig.update_layout(
                xaxis_title="Time (s)",
                yaxis_title="Raw ADC (0–4095)",
                height=450,
                margin=dict(l=40, r=20, t=40, b=40),
            )

            plot_box.plotly_chart(fig, use_container_width=True)

            # Status text
            latest = ", ".join(str(v) for v in vals)
            info_box.markdown(
                f"""
                **Elapsed:** {timestamp:5.1f} s  
                **Latest ADCs:** {latest}  
                **Press events ≥ threshold:** {presses_over_threshold}
                """
            )

            # Small sleep to avoid hammering Streamlit
            time.sleep(0.05)

            # Let Streamlit see button changes
            if not st.session_state.running:
                break

    finally:
        try:
            ws.close()
        except Exception:
            pass

    # Save session if we collected data
    if data_rows:
        col_names = ["time"] + [f"F{i+1}" for i in range(len(data_rows[0]) - 1)]
        df = pd.DataFrame(data_rows, columns=col_names)
        filename = datetime.now().strftime("data/session_%Y%m%d_%H%M%S.csv")
        df.to_csv(filename, index=False)
        status_box.success(f"Session saved to **{filename}**")
    else:
        status_box.warning("No data collected; nothing saved.")

    # Reset running flag
    st.session_state.running = False


if st.session_state.running:
    run_session()
else:
    status_box.info("Press **Start session** in the sidebar to begin streaming data.")
