"""
Hotspot Signal & Bandwidth Monitor

Run this locally (on the machine connected to your phone's hotspot) with:
    streamlit run hotspot_monitor.py

It measures real download/upload speed, ping, jitter, and packet loss over
your actual hotspot connection, logs results to hotspot_log.csv, and
surfaces tips based on what it finds.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from hotspot_core import (
    generate_tips,
    load_history,
    run_full_test,
    speedtest,
)

st.set_page_config(page_title="Hotspot Monitor", page_icon="📶", layout="wide")

st.title("📶 Hotspot Signal & Bandwidth Monitor")
st.caption(
    "Run this while connected to your phone's hotspot to see real download/upload "
    "speed, latency, jitter, and packet loss over time."
)

if speedtest is None:
    st.error("`speedtest-cli` isn't installed. Run: `pip install speedtest-cli`")

history = load_history()

col_run, col_devices = st.columns([2, 1])
with col_devices:
    connected_devices = st.number_input(
        "Devices currently connected to hotspot", min_value=0, max_value=20, value=1, step=1
    )
with col_run:
    run_clicked = st.button("🔄 Run Test Now", type="primary", use_container_width=True)

if run_clicked:
    with st.spinner("Running ping + speed test (can take 15-30s)..."):
        row = run_full_test(connected_devices=connected_devices)
    from hotspot_core import save_result

    save_result(row)
    if row["notes"]:
        st.warning(f"Test completed with issues: {row['notes']}")
    else:
        st.success("Test complete.")
    history = load_history()

if not history.empty:
    latest = history.iloc[-1].to_dict()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Download", f"{latest['download_mbps']:.1f} Mbps" if pd.notna(latest["download_mbps"]) else "—")
    m2.metric("Upload", f"{latest['upload_mbps']:.1f} Mbps" if pd.notna(latest["upload_mbps"]) else "—")
    m3.metric("Ping", f"{latest['ping_ms']:.0f} ms" if pd.notna(latest["ping_ms"]) else "—")
    m4.metric("Jitter", f"{latest['jitter_ms']:.1f} ms" if pd.notna(latest["jitter_ms"]) else "—")
    m5.metric(
        "Packet Loss",
        f"{latest['packet_loss_pct']:.1f}%" if pd.notna(latest["packet_loss_pct"]) else "—",
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Speed", "Latency & Jitter", "Packet Loss"])
    with tab1:
        fig = px.line(
            history, x="timestamp", y=["download_mbps", "upload_mbps"], markers=True,
            labels={"value": "Mbps", "timestamp": "Time", "variable": "Metric"},
        )
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig2 = px.line(
            history, x="timestamp", y=["ping_ms", "jitter_ms"], markers=True,
            labels={"value": "ms", "timestamp": "Time", "variable": "Metric"},
        )
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        fig3 = px.bar(
            history, x="timestamp", y="packet_loss_pct",
            labels={"packet_loss_pct": "% loss", "timestamp": "Time"},
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    st.subheader("💡 Tips")
    dynamic_tips, general_tips = generate_tips(latest)
    for t in dynamic_tips:
        st.warning(t)
    with st.expander("General hotspot optimization tips"):
        for t in general_tips:
            st.markdown(f"- {t}")

    st.divider()

    st.subheader("📋 History")
    st.dataframe(history.sort_values("timestamp", ascending=False), use_container_width=True)
    csv_bytes = history.to_csv(index=False).encode("utf-8")
    st.download_button("Download full history as CSV", csv_bytes, "hotspot_log.csv", "text/csv")
else:
    st.info("No data yet — click 'Run Test Now' above to log your first measurement.")

st.sidebar.header("About")
st.sidebar.markdown(
    "This app tests the connection **your computer is currently using**. "
    "Make sure you're connected to your phone's hotspot before running a test.\n\n"
    "For continuous background logging (so you don't have to keep this tab open), "
    "run `logger.py` in a separate terminal — it writes to the same CSV this "
    "dashboard reads from."
)
