#!/usr/bin/env python3
"""
run_kaggle.py - Unified Cloudflare Tunnel & FusionFlows Runner for Kaggle
"""
import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.request

DEFAULT_TOKEN = "eyJhIjoiNDhmZmY2NGYwNmI2ZGJkZjY3MmI2M2FjYjhhNmI0MjgiLCJ0IjoiMzM1OWM2MjgtNWNmNi00ODZhLWI2YWEtMWQ2ZDNiN2Y0NTFkIiwicyI6Ik9EZzNOelkwWkRJdFlqRTJaUzAwT0dZeUxUazJNak10TVRRd05tRXhPV0l3Wm1JNCJ9"


def start_tunnel(token: str, cf_bin: str) -> subprocess.Popen:
    print("[1/2] Preparing Cloudflare Tunnel...")
    # Kill any stale background tunnels
    os.system("pkill -f cloudflared 2>/dev/null || true")
    time.sleep(1)

    print(f"[TUNNEL] Starting tunnel daemon with token: {token[:12]}...{token[-8:]}")
    proc = subprocess.Popen(
        [cf_bin, "tunnel", "run", "--token", token],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None
    )
    time.sleep(2)

    if proc.poll() is not None:
        print("[WARNING] Tunnel process exited prematurely. Check your token.", file=sys.stderr)
    else:
        print("[SUCCESS] Cloudflare tunnel active in background! Pointing to https://wangp.piepretech.com")
    return proc


def run_app(port: int = 7860) -> None:
    print(f"\n[2/2] Launching FusionFlows on GPU (port {port})...")
    app_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fusionflows.py")

    cmd = [
        sys.executable,
        app_py,
        "run",
        "--execution-providers", "cuda"
    ]

    print(f"[EXEC] {' '.join(cmd)}\n")
    sys.stdout.flush()

    # Run the application in foreground
    app_proc = subprocess.Popen(cmd)
    try:
        app_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping FusionFlows...")
        app_proc.terminate()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FusionFlows with Cloudflare Tunnel on Kaggle")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Cloudflare Tunnel Token")
    parser.add_argument("--port", type=int, default=7860, help="Local application port (default: 7860)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    cf_bin = os.path.join(base_dir, "cloudflared-linux-amd64")

    if not os.path.isfile(cf_bin):
        print("[INFO] cloudflared-linux-amd64 not found. Downloading...")
        cf_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        urllib.request.urlretrieve(cf_url, cf_bin)
        os.chmod(cf_bin, 0o755)

    tunnel_proc = start_tunnel(args.token, cf_bin)

    try:
        run_app(port=args.port)
    finally:
        print("\n[CLEANUP] Terminating Cloudflare tunnel...")
        try:
            if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                os.killpg(os.getpgid(tunnel_proc.pid), signal.SIGTERM)
            else:
                tunnel_proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()
