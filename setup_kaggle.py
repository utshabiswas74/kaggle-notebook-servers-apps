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
    try:
        ver_output = subprocess.check_output(["ffmpeg", "-version"], text=True, stderr=subprocess.DEVNULL)
        if "static" in ver_output.lower() or "johnvansickle" in ver_output.lower() or "version 7" in ver_output.lower() or "version 6" in ver_output.lower():
            print(f"Modern static FFmpeg already configured.")
            return
    except Exception:
        pass

    print("Downloading modern static Linux FFmpeg build...")
    archive_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    archive_name = "ffmpeg-release-amd64-static.tar.xz"

    run_command(f"wget -q -c -nc {archive_url} -O {archive_name}")
    run_command(f"tar -xf {archive_name}")

    extracted_dirs = glob.glob("ffmpeg-*-amd64-static")
    if extracted_dirs:
        ext_dir = extracted_dirs[0]
        ffmpeg_bin = os.path.join(ext_dir, "ffmpeg")
        ffprobe_bin = os.path.join(ext_dir, "ffprobe")

        for dest_dir in ["/usr/local/bin", "/usr/bin"]:
            if os.path.isfile(ffmpeg_bin):
                run_command(f"cp -f {ffmpeg_bin} {dest_dir}/ffmpeg && chmod +x {dest_dir}/ffmpeg", check=False)
            if os.path.isfile(ffprobe_bin):
                run_command(f"cp -f {ffprobe_bin} {dest_dir}/ffprobe && chmod +x {dest_dir}/ffprobe", check=False)

        shutil.rmtree(ext_dir, ignore_errors=True)

    if os.path.isfile(archive_name):
        os.remove(archive_name)

    print("Modern static FFmpeg & FFprobe successfully configured.")


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

    print("Installing clean onnxruntime-gpu for CUDA 12 and numpy 1.26.4...")
    run_command(f"{sys.executable} -m pip install --force-reinstall --no-cache-dir onnxruntime-gpu==1.19.2 numpy==1.26.4")

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


def setup_models_bundle() -> None:
    print("\n--- [5/5] Extracting Bundled Models from GitHub Releases ---")
    repo_root = os.path.dirname(os.path.abspath(__file__))
    assets_models_dir = os.path.join(repo_root, ".assets", "models")
    os.makedirs(assets_models_dir, exist_ok=True)

    test_file = os.path.join(assets_models_dir, "inswapper_128.onnx")
    if os.path.isfile(test_file) and os.path.getsize(test_file) > 100_000_000:
        print(f"Models already extracted in {assets_models_dir}")
        return

    bundle_url = "https://github.com/utshabiswas74/kaggle-notebook-servers-apps/releases/download/v1.0.0/fusionflows-models.zip"
    zip_path = os.path.join(repo_root, "fusionflows-models.zip")

    print("Downloading pre-packaged model bundle from GitHub Releases...")
    run_command(f"wget -q -c {bundle_url} -O {zip_path}")

    print(f"Extracting models to {assets_models_dir}...")
    run_command(f"unzip -q -o {zip_path} -d {assets_models_dir}")

    if os.path.isfile(zip_path):
        os.remove(zip_path)

    # Ensure auxiliary models (hyperswap_1a_256, fan_68_5, xseg_1, bisenet_resnet_34) are present
    base_release_url = "https://github.com/utshabiswas74/kaggle-notebook-servers-apps/releases/download/v1.0.0"
    aux_files = [
        "hyperswap_1a_256.onnx",
        "hyperswap_1a_256.hash",
        "fan_68_5.onnx",
        "fan_68_5.hash",
        "xseg_1.onnx",
        "xseg_1.hash",
        "bisenet_resnet_34.onnx",
        "bisenet_resnet_34.hash"
    ]
    for filename in aux_files:
        dest_path = os.path.join(assets_models_dir, filename)
        if not os.path.isfile(dest_path) or os.path.getsize(dest_path) == 0:
            print(f"Fetching model asset: {filename}...")
            run_command(f"wget -q -c {base_release_url}/{filename} -O {dest_path}", check=False)
            # Reliable fallbacks
            if (not os.path.isfile(dest_path) or os.path.getsize(dest_path) == 0):
                if filename.startswith("hyperswap"):
                    run_command(f"wget -q -c https://github.com/facefusion/facefusion-assets/releases/download/models-3.3.0/{filename} -O {dest_path}", check=False)
                elif filename.startswith("fan_"):
                    run_command(f"wget -q -c https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/{filename} -O {dest_path}", check=False)

    print("All essential neural models are extracted and ready.")


def setup_rife_linux() -> None:
    print("\n--- Configuring FusionFlows RIFE 3.1 Linux Binary ---")
    repo_root = os.path.dirname(os.path.abspath(__file__))
    flowframes_bin_dir = os.path.join(repo_root, "fusionflows", "flowframes_bin")
    os.makedirs(flowframes_bin_dir, exist_ok=True)
    rife_bin = os.path.join(flowframes_bin_dir, "rife-ncnn-vulkan")

    if os.path.isfile(rife_bin) and os.path.getsize(rife_bin) > 5_000_000:
        os.chmod(rife_bin, 0o755)
        print("RIFE Linux binary already present.")
        return

    rife_zip_url = "https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-ubuntu.zip"
    temp_zip = "/tmp/rife-ubuntu.zip"
    run_command(f"wget -q -c {rife_zip_url} -O {temp_zip}")
    run_command(f"unzip -q -j -o {temp_zip} 'rife-ncnn-vulkan-20221029-ubuntu/rife-ncnn-vulkan' -d {flowframes_bin_dir}")
    if os.path.isfile(temp_zip):
        os.remove(temp_zip)
    if os.path.isfile(rife_bin):
        os.chmod(rife_bin, 0o755)
        run_command(f"cp -f {rife_bin} /usr/local/bin/rife-ncnn-vulkan && chmod +x /usr/local/bin/rife-ncnn-vulkan", check=False)
        print("RIFE Linux binary successfully installed and verified.")
    else:
        print("[WARNING] Could not extract rife-ncnn-vulkan binary.", file=sys.stderr)


def main() -> None:
    print("==================================================")
    print(" FusionFlows Kaggle Automated Setup Starting...   ")
    print("==================================================")
    install_ffmpeg()
    setup_onnxruntime_gpu()
    install_requirements()
    setup_cloudflared()
    setup_models_bundle()
    setup_rife_linux()
    print("\n==================================================")
    print(" [DONE] Setup Completed Successfully!            ")
    print(" Run '!python run_kaggle.py' to start the app.    ")
    print("==================================================")


if __name__ == "__main__":
    main()
