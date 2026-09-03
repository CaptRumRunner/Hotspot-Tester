"""
Core logic shared by the Streamlit dashboard (hotspot_monitor.py) and the
background logger (logger.py). Handles running tests, reading/writing the
CSV log, and generating tips based on the latest results.
"""
import os
import re
import platform
import subprocess
from datetime import datetime

import pandas as pd

try:
    import speedtest
except ImportError:
    speedtest = None

DATA_FILE = "hotspot_log.csv"
COLUMNS = [
    "timestamp",
    "download_mbps",
    "upload_mbps",
    "ping_ms",
    "jitter_ms",
    "packet_loss_pct",
    "connected_devices",
    "notes",
]


def run_ping_test(host="8.8.8.8", count=10):
    """Ping a host and return (avg_latency_ms, jitter_ms, packet_loss_pct, error)."""
    system = platform.system()
    cmd = ["ping", "-n" if system == "Windows" else "-c", str(count), host]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=count * 3 + 10
        )
        output = result.stdout
    except Exception as e:
        return None, None, None, f"ping failed: {e}"

    if system == "Windows":
        times = [float(m) for m in re.findall(r"time[=<]([\d.]+)ms", output)]
        loss_match = re.search(r"\((\d+)% loss\)", output)
    else:
        times = [float(m) for m in re.findall(r"time=([\d.]+) ms", output)]
        loss_match = re.search(r"([\d.]+)% packet loss", output)

    packet_loss = float(loss_match.group(1)) if loss_match else None

    if not times:
        return None, None, packet_loss, "no ping responses parsed"

    avg_latency = sum(times) / len(times)
    jitter = (
        sum(abs(times[i] - times[i - 1]) for i in range(1, len(times))) / (len(times) - 1)
        if len(times) > 1
        else 0.0
    )
    return avg_latency, jitter, packet_loss, None


def run_speed_test():
    """Return (download_mbps, upload_mbps, ping_ms, error)."""
    if speedtest is None:
        return None, None, None, "speedtest-cli not installed"
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        download = s.download() / 1_000_000
        upload = s.upload() / 1_000_000
        ping = s.results.ping
        return download, upload, ping, None
    except Exception as e:
        return None, None, None, f"speedtest failed: {e}"


def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
    return pd.DataFrame(columns=COLUMNS)


def save_result(row: dict):
    df = pd.DataFrame([row])
    header = not os.path.exists(DATA_FILE)
    df.to_csv(DATA_FILE, mode="a", header=header, index=False)


def run_full_test(connected_devices=None, ping_host="8.8.8.8"):
    """Run ping + speed test and return a row dict ready to save."""
    avg_latency, jitter, packet_loss, ping_err = run_ping_test(host=ping_host)
    download, upload, sp_ping, sp_err = run_speed_test()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "download_mbps": round(download, 2) if download else None,
        "upload_mbps": round(upload, 2) if upload else None,
        "ping_ms": round(avg_latency, 1) if avg_latency else (round(sp_ping, 1) if sp_ping else None),
        "jitter_ms": round(jitter, 1) if jitter else None,
        "packet_loss_pct": packet_loss,
        "connected_devices": connected_devices,
        "notes": "; ".join(filter(None, [ping_err, sp_err])),
    }
    return row


def generate_tips(latest: dict):
    """Return (dynamic_tips, general_tips) based on the latest row."""
    dynamic = []
    if latest is not None:
        pl = latest.get("packet_loss_pct")
        jit = latest.get("jitter_ms")
        ping = latest.get("ping_ms")
        dl = latest.get("download_mbps")
        devices = latest.get("connected_devices")

        if pl is not None and pd.notna(pl) and pl > 2:
            dynamic.append(
                "High packet loss detected — try moving your phone closer, "
                "reducing obstructions (walls/metal), or switching hotspot band."
            )
        if jit is not None and pd.notna(jit) and jit > 30:
            dynamic.append(
                "High jitter — other devices on the hotspot may be competing "
                "for bandwidth. Try disconnecting unused devices."
            )
        if ping is not None and pd.notna(ping) and ping > 100:
            dynamic.append(
                "High latency — could be carrier congestion. Try toggling "
                "airplane mode or switching between 5G/LTE on the phone."
            )
        if dl is not None and pd.notna(dl) and dl < 5:
            dynamic.append(
                "Low download speed — check if your data plan is throttled "
                "after a cap, or if too many devices are connected."
            )
        if devices is not None and pd.notna(devices) and devices >= 3:
            dynamic.append(
                f"{int(devices)} devices connected — each additional device "
                "shares the same bandwidth pool."
            )

    if not dynamic:
        dynamic.append("Metrics look healthy right now — no immediate issues detected.")

    general = [
        "Keep the phone's battery above 20% — many phones throttle hotspot "
        "radio to save power when low.",
        "Line-of-sight matters: keep your computer and phone in the same "
        "room without walls/metal in between.",
        "Some carriers deprioritize hotspot data separately from regular "
        "data — check your plan's hotspot allotment.",
        "Restarting the hotspot (toggle off/on) periodically clears up "
        "radio congestion.",
        "5GHz hotspot band is faster but shorter range; 2.4GHz reaches "
        "further but is slower and more congested.",
    ]
    return dynamic, general
