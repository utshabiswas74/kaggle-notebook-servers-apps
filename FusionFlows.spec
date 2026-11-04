# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

packages_to_collect_data = [
    'anyio', 'certifi', 'click', 'fastapi', 'ffmpy', 'filelock', 'gradio',
    'gradio_client', 'gradio_rangeslider', 'groovy', 'h11', 'httpcore', 'httpx',
    'huggingface_hub', 'idna', 'mdurl', 'ml_dtypes', 'numpy', 'onnx',
    'onnxruntime', 'orjson', 'packaging', 'pandas', 'pydantic', 'pydantic_core',
    'pytz', 'rich', 'safehttpx', 'scipy', 'starlette', 'tomlkit', 'tqdm',
    'typer', 'tzdata', 'uvicorn', 'websockets', 'cv2'
]

package_datas = []
for p in packages_to_collect_data:
    try:
        package_datas += collect_data_files(p)
    except Exception:
        pass

onnxruntime_binaries = collect_dynamic_libs('onnxruntime')
cv2_modules = collect_submodules('cv2')
onnx_modules = collect_submodules('onnx')
tqdm_modules = collect_submodules('tqdm')
groovy_modules = collect_submodules('groovy')

# Collect hidden submodules
fusionflows_modules = collect_submodules('fusionflows')
gradio_modules = collect_submodules('gradio')
gradio_client_modules = collect_submodules('gradio_client')
gradio_rangeslider_modules = collect_submodules('gradio_rangeslider')
safehttpx_modules = collect_submodules('safehttpx')
uvicorn_modules = collect_submodules('uvicorn')
fastapi_modules = collect_submodules('fastapi')
scipy_modules = collect_submodules('scipy')

hidden_imports = list(set(
    fusionflows_modules +
    gradio_modules +
    gradio_client_modules +
    gradio_rangeslider_modules +
    safehttpx_modules +
    uvicorn_modules +
    fastapi_modules +
    scipy_modules +
    cv2_modules +
    onnx_modules +
    tqdm_modules +
    groovy_modules +
    [
        'onnx',
        'onnxruntime',
        'onnxruntime.capi._pybind_state',
        'cv2',
        'cv2.typing',
        'scipy.special.cython_special',
        'scipy.spatial.transform._rotation',
        'jinja2',
        'multiprocessing',
        'groovy',
    ]
))

# Application data files
app_datas = [
    ('fusionflows.ini', '.'),
    ('fusionflows.ico', '.'),
    ('fusionflows.ini', '.'),
    ('fusionflows.ico', '.'),
    ('fusionflows', 'fusionflows'),
]

# Binaries to embed (FFmpeg & FFprobe)
app_binaries = [
    ('bin/ffmpeg.exe', '.'),
    ('bin/ffprobe.exe', '.'),
] + onnxruntime_binaries

all_datas = package_datas + app_datas

a = Analysis(
    ['fusionflows.py'],
    pathex=['.'],
    binaries=app_binaries,
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[
        'torch',
        'torchvision',
        'tensorflow',
        'tensorrt',
        'onnxruntime-gpu',
        'onnxruntime-directml',
        'onnxruntime-openvino',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FusionFlows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='fusionflows.ico',
)
