import os
import sys

try:
    import gradio.component_meta
    gradio.component_meta.create_or_modify_pyi = lambda *args, **kwargs: None
except Exception:
    pass
