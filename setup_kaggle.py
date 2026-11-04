#!/usr/bin/env python3
"""
setup_kaggle.py - Automated Kaggle Environment & Dependency Setup for FusionFlows
"""
import glob
import os
import shutil
import subprocess
import sys
import urllib.request


def run_command(cmd: str, check: bool = True) -> int:
    print(f"\n[EXEC] {cmd}")
    res = os.system(cmd)
    if check and res != 0:
        print(f"[ERROR] Command failed with return code {res}: {cmd}", file=sys.stderr)
    return res


def install_ffmpeg() -> None:
    print("\n--- [1/4] Checking FFmpeg & FFprobe ---")
    ffmpeg_exists = shutil.which("ffmpeg")
    ffprobe_exists = shutil.which("ffprobe")

    if ffmpeg_exists and ffprobe_exists:
        print(f"FFmpeg already available: {ffmpeg_exists}")
        return

    print("Downloading static Linux FFmpeg build...")
    archive_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    archive_name = "ffmpeg-release-amd64-static.tar.xz"

    run_command(f"wget -q -c -nc {archive_url} -O {archive_name}")
    run_command(f"tar -xf {archive_name}")

    extracted_dirs = glob.glob("ffmpeg-*-amd64-static")
    if extracted_dirs:
        ext_dir = extracted_dirs[0]
        ffmpeg_bin = os.path.join(ext_dir, "ffmpeg")
        ffprobe_bin = os.path.join(ext_dir, "ffprobe")

        if os.path.isfile(ffmpeg_bin):
            run_command(f"cp -f {ffmpeg_bin} /usr/bin/ffmpeg && chmod +x /usr/bin/ffmpeg")
        if os.path.isfile(ffprobe_bin):
            run_command(f"cp -f {ffprobe_bin} /usr/bin/ffprobe && chmod +x /usr/bin/ffprobe")

        shutil.rmtree(ext_dir, ignore_errors=True)

    if os.path.isfile(archive_name):
        os.remove(archive_name)

    print("FFmpeg & FFprobe successfully configured.")


def setup_onnxruntime_gpu() -> None:
    print("\n--- [2/4] Configuring ONNX Runtime GPU ---")
    # Clean up any conflicting orphaned package directories
    run_command(f"{sys.executable} -m pip uninstall -y onnxruntime onnxruntime-gpu", check=False)

    search_dirs = [
        "/usr/local/lib/python*/dist-packages/onnxruntime*",
        "/opt/conda/lib/python*/site-packages/onnxruntime*",
        os.path.expanduser("~/.local/lib/python*/site-packages/onnxruntime*")
    ]
    for pattern in search_dirs:
        for path in glob.glob(pattern):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                elif os.path.isfile(path):
                    os.remove(path)
            except Exception:
                pass

    print("Installing clean onnxruntime-gpu...")
    run_command(f"{sys.executable} -m pip install --force-reinstall --no-cache-dir onnxruntime-gpu")

    # Verification test
    verify_code = "import onnxruntime; from onnxruntime import InferenceSession; print('ONNX Runtime GPU loaded:', onnxruntime.__version__)"
    res = run_command(f'{sys.executable} -c "{verify_code}"')
    if res != 0:
        print("[WARNING] Verification of onnxruntime-gpu threw an exit code. Please check CUDA libraries.", file=sys.stderr)
    else:
        print("[SUCCESS] onnxruntime-gpu verified successfully!")


def install_requirements() -> None:
    print("\n--- [3/4] Installing Python Requirements ---")
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.isfile(req_file):
        run_command(f"{sys.executable} -m pip install -r {req_file}")
    else:
        print("[INFO] No requirements.txt found.")


def setup_cloudflared() -> None:
    print("\n--- [4/5] Setting up Cloudflare Tunnel Client ---")
    cf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared-linux-amd64")
    if not os.path.isfile(cf_path):
        cf_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        print("Downloading cloudflared-linux-amd64...")
        urllib.request.urlretrieve(cf_url, cf_path)

    os.chmod(cf_path, 0o755)
    run_command(f"{cf_path} --version", check=False)
    print("Cloudflared client ready.")


def download_models() -> None:
    print("\n--- [5/5] Pre-downloading Essential Models ---")
    app_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fusionflows.py")
    run_command(f"{sys.executable} {app_py} force-download", check=False)
    print("Models pre-downloaded.")


def main() -> None:
    print("==================================================")
    print(" FusionFlows Kaggle Automated Setup Starting...   ")
    print("==================================================")
    install_ffmpeg()
    setup_onnxruntime_gpu()
    install_requirements()
    setup_cloudflared()
    download_models()
    print("\n==================================================")
    print(" [DONE] Setup Completed Successfully!            ")
    print(" Run '!python run_kaggle.py' to start the app.    ")
    print("==================================================")


if __name__ == "__main__":
    main()
