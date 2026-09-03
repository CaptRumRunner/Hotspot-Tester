"""
Background hotspot logger.

Runs continuously in a terminal, testing your hotspot connection on an
interval and appending results to the same CSV the Streamlit dashboard
(hotspot_monitor.py) reads from. Useful for catching problems that happen
when you're not actively watching the dashboard (e.g. "bandwidth tanks
every day around 6pm").

Usage:
    python logger.py                  # test every 15 minutes (default)
    python logger.py --interval 5     # test every 5 minutes
    python logger.py --devices 2      # log a fixed connected-device count

Stop with Ctrl+C.
"""
import argparse
import time
from datetime import datetime

from hotspot_core import run_full_test, save_result


def main():
    parser = argparse.ArgumentParser(description="Continuous hotspot logger")
    parser.add_argument("--interval", type=int, default=15, help="Minutes between tests (default: 15)")
    parser.add_argument("--devices", type=int, default=None, help="Fixed connected-device count to log")
    args = parser.parse_args()

    print(f"Starting hotspot logger — testing every {args.interval} minute(s). Ctrl+C to stop.")
    while True:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] Running test...")
        row = run_full_test(connected_devices=args.devices)
        save_result(row)
        summary = (
            f"  download={row['download_mbps']} Mbps  upload={row['upload_mbps']} Mbps  "
            f"ping={row['ping_ms']} ms  jitter={row['jitter_ms']} ms  "
            f"loss={row['packet_loss_pct']}%"
        )
        print(summary)
        if row["notes"]:
            print(f"  notes: {row['notes']}")
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
