#!/usr/bin/env python3

import multiprocessing
import os
import sys

os.environ['OMP_NUM_THREADS'] = '1'

# Configure runtime PATH for bundled binaries (ffmpeg, ffprobe)
bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin'))
if os.path.exists(bin_dir):
	os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')

if getattr(sys, 'frozen', False):
	multiprocessing.freeze_support()
	base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
	exe_dir = os.path.dirname(sys.executable)
	os.environ['PATH'] = base_dir + os.pathsep + exe_dir + os.pathsep + os.environ.get('PATH', '')

# Disable Gradio stub generation in frozen runtime (which requires .py source files)
try:
	import gradio.component_meta
	gradio.component_meta.create_or_modify_pyi = lambda *args, **kwargs: None
except Exception:
	pass

from fusionflows import conda, core

if __name__ == '__main__':
	multiprocessing.freeze_support()
	# Default to GUI run mode if launched without CLI subcommands (e.g. double-clicked)
	if len(sys.argv) == 1:
		sys.argv.append('run')
	conda.setup()
	core.cli()

