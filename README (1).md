# Hotspot Signal & Bandwidth Monitor

A local Streamlit app that measures your phone hotspot's real performance —
download/upload speed, ping, jitter, and packet loss — and gives tips for
improving it.

**Must run locally.** It tests whatever network your computer is currently
using, so it needs to run on the machine connected to your hotspot (not
deployed to Streamlit Community Cloud, which would test Streamlit's servers
instead of your hotspot).

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Dashboard (manual/on-demand testing)

```bash
streamlit run hotspot_monitor.py
```

Opens at `localhost:8501`. Click "Run Test Now" while connected to your
hotspot. Optionally enter how many devices are currently connected to the
hotspot — this gets logged alongside each test so you can correlate slowdowns
with device count.

### Background logger (continuous testing)

Run in a separate terminal to log results on a schedule, even when the
dashboard isn't open:

```bash
python logger.py --interval 15
```

Both scripts read/write the same `hotspot_log.csv`, so the dashboard will
show logger results too — just refresh the page.

## What it measures

| Metric | What it tells you |
|---|---|
| Download / Upload (Mbps) | Real throughput via speedtest-cli |
| Ping (ms) | Round-trip latency to 8.8.8.8 |
| Jitter (ms) | Latency variability — high jitter hurts calls/streaming even if speed looks fine |
| Packet loss (%) | Dropped packets — a common cause of "flaky" connections |

Signal strength (carrier bars) isn't included — that data lives on the
phone's radio firmware and isn't exposed to a computer over the hotspot
connection.
