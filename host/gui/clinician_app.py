# gui/clinician_app.py

import glob

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cardinal Grip – Clinician GUI", layout="wide")

st.title("Cardinal Grip – Clinician Review Dashboard")

st.markdown(
    "Select a recorded rehab session to review finger forces over time, "
    "peak values, and variability."
)

files = sorted(glob.glob("data/session_*.csv"))

if not files:
    st.warning("No session files found in the `data/` folder yet.")
    st.stop()

file = st.selectbox("Session file", files, index=len(files) - 1)

df = pd.read_csv(file)

st.subheader("Summary statistics")

st.write(df.describe())

# Long-form DataFrame for plotting
value_cols = [c for c in df.columns if c != "time"]
long_df = df.melt(id_vars="time", value_vars=value_cols, var_name="Finger", value_name="ADC")

st.subheader("Finger forces over time")

fig = px.line(long_df, x="time", y="ADC", color="Finger")
fig.update_layout(
    xaxis_title="Time (s)",
    yaxis_title="Raw ADC (0–4095)",
    height=500,
    margin=dict(l=40, r=20, t=40, b=40),
)
st.plotly_chart(fig, use_container_width=True)
