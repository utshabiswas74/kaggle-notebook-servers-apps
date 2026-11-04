import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Generator, Optional, Tuple

from fusionflows import logger, process_manager, state_manager
from fusionflows.ffprobe import extract_video_fps, extract_video_metadata, probe_audio_entries, probe_video_entries


def get_rife_executable() -> Optional[str]:
	possible_paths = [
		os.path.join(os.path.dirname(__file__), 'flowframes_bin', 'rife-ncnn-vulkan'),
		os.path.join(os.path.dirname(__file__), 'flowframes_bin', 'rife-ncnn-vulkan.exe'),
		shutil.which('rife-ncnn-vulkan'),
		'/usr/local/bin/rife-ncnn-vulkan',
		'/usr/bin/rife-ncnn-vulkan',
		os.path.join(getattr(sys, '_MEIPASS', ''), 'fusionflows', 'flowframes_bin', 'rife-ncnn-vulkan'),
		os.path.join(getattr(sys, '_MEIPASS', ''), 'flowframes_bin', 'rife-ncnn-vulkan'),
		os.path.join(os.path.dirname(sys.executable), 'fusionflows', 'flowframes_bin', 'rife-ncnn-vulkan'),
		os.path.join(os.path.dirname(sys.executable), 'flowframes_bin', 'rife-ncnn-vulkan')
	]
	for path in possible_paths:
		if path and os.path.isfile(path):
			try:
				os.chmod(path, 0o755)
			except Exception:
				pass
			return os.path.abspath(path)
	return None


def get_rife_model_dir() -> Optional[str]:
	candidate_dirs = [
		os.path.join(os.path.dirname(__file__), 'flowframes_bin', 'models', 'rife-v3.1'),
		os.path.join(os.path.dirname(__file__), 'flowframes_bin', 'models', 'rife-v4'),
		os.path.join(os.path.dirname(__file__), 'flowframes_bin', 'models')
	]
	exe_path = get_rife_executable()
	if exe_path:
		candidate_dirs.insert(0, os.path.join(os.path.dirname(exe_path), 'models', 'rife-v3.1'))
	for model_dir in candidate_dirs:
		if model_dir and os.path.isdir(model_dir):
			return os.path.abspath(model_dir)
	return None


def has_audio_stream(video_path: str) -> bool:
	try:
		entries = probe_audio_entries(video_path, ['codec_name'])
		return bool(entries.get('codec_name'))
	except Exception:
		return False


def get_factor_multiplier(factor_str: Optional[str]) -> int:
	if not factor_str or '1' in factor_str:
		return 1
	if '4' in factor_str:
		return 4
	if '8' in factor_str:
		return 8
	return 2


def check_and_fetch_rife_models(model_dir: str) -> bool:
	required = ['flownet.bin', 'contextnet.bin', 'fusionnet.bin', 'flownet.param', 'contextnet.param', 'fusionnet.param']
	for fname in required:
		fpath = os.path.join(model_dir, fname)
		if not os.path.isfile(fpath) or os.path.getsize(fpath) == 0:
			url = f"https://github.com/nihui/rife-ncnn-vulkan/raw/20221029/models/rife-v3.1/{fname}"
			logger.warn(f"[FUSIONFLOWS] Model {fname} missing from {model_dir}. Downloading from {url}...", __name__)
			try:
				import urllib.request
				urllib.request.urlretrieve(url, fpath)
			except Exception as e:
				logger.error(f"[FUSIONFLOWS] Failed to fetch {fname}: {e}", __name__)
				return False
	return True


def run_ffmpeg_motion_interpolation(
	video_path: str,
	target_fps: float,
	output_path: str
) -> bool:
	temp_fallback = output_path + ".fallback.mp4"
	try:
		cmd = [
			'ffmpeg', '-y',
			'-i', video_path,
			'-vf', f"minterpolate=fps={target_fps}:mi_mode=blend",
			'-c:v', 'libx264',
			'-crf', '18',
			'-preset', 'veryfast',
			'-pix_fmt', 'yuv420p',
			'-c:a', 'copy',
			temp_fallback
		]
		logger.info(f"[FUSIONFLOWS] Executing fast Motion Interpolation to {target_fps} FPS...", __name__)
		res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
		if res.returncode == 0 and os.path.isfile(temp_fallback) and os.path.getsize(temp_fallback) > 0:
			if os.path.exists(output_path):
				os.remove(output_path)
			shutil.move(temp_fallback, output_path)
			return True

		# Retry with audio re-encode in case copy fails
		cmd[-3] = 'aac'
		cmd.insert(-2, '-b:a')
		cmd.insert(-2, '192k')
		res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
		if res.returncode == 0 and os.path.isfile(temp_fallback) and os.path.getsize(temp_fallback) > 0:
			if os.path.exists(output_path):
				os.remove(output_path)
			shutil.move(temp_fallback, output_path)
			return True

		err_msg = res.stderr.decode(errors='ignore') if res.stderr else "Unknown error"
		logger.error(f"[FUSIONFLOWS] Motion Interpolation failed: {err_msg}", __name__)
		return False
	except Exception as e:
		logger.error(f"[FUSIONFLOWS] Motion Interpolation exception: {e}", __name__)
		return False
	finally:
		if os.path.exists(temp_fallback):
			try:
				os.remove(temp_fallback)
			except OSError:
				pass


def interpolate_video(
	video_path: str,
	factor_str: Optional[str] = None,
	output_path: Optional[str] = None
) -> Optional[str]:
	last_result = None
	for result, _ in interpolate_video_with_progress(video_path, factor_str, output_path):
		if result:
			last_result = result
	return last_result


def interpolate_video_with_progress(
	video_path: str,
	factor_str: Optional[str] = None,
	output_path: Optional[str] = None
) -> Generator[Tuple[Optional[str], str], None, None]:
	if not os.path.isfile(video_path):
		yield (None, "Input video not found")
		return

	factor = get_factor_multiplier(factor_str or state_manager.get_item('flowframes_factor'))
	if factor <= 1:
		yield (video_path, "Original FPS preserved (1x)")
		return

	if output_path is None:
		dir_name = os.path.dirname(video_path)
		base_name, ext = os.path.splitext(os.path.basename(video_path))
		output_path = os.path.join(dir_name, f"{base_name}_{factor}x{ext}")

	try:
		meta = extract_video_metadata(video_path)
		current_fps = meta.get('fps') or 30.0
		total_input_frames = meta.get('frame_total') or 0
		target_fps = round(current_fps * factor, 2)
	except Exception:
		entries = probe_video_entries(video_path, ['avg_frame_rate', 'r_frame_rate'])
		current_fps = extract_video_fps(entries) or 30.0
		total_input_frames = 0
		target_fps = round(current_fps * factor, 2)

	rife_exe = get_rife_executable()
	model_dir = get_rife_model_dir()

	if not rife_exe or not model_dir or not check_and_fetch_rife_models(model_dir):
		logger.warn("[FUSIONFLOWS] RIFE 3.1 binaries or models unavailable. Using Fast Motion Interpolation...", __name__)
		yield (None, f"Using Motion Interpolation to generate {target_fps} FPS...")
		if run_ffmpeg_motion_interpolation(video_path, target_fps, output_path):
			complete_msg = f"[FUSIONFLOWS] 2x FPS Video Interpolation complete ({current_fps} -> {target_fps} FPS)!"
			logger.info(complete_msg, __name__)
			yield (output_path, complete_msg)
			return
		else:
			yield (video_path, "[FUSIONFLOWS] Interpolation unavailable, keeping original video.")
			return

	init_msg = f"[FUSIONFLOWS] Initializing FusionFlows RIFE 3.1: {current_fps} FPS -> {target_fps} FPS ({factor}x multiplier)"
	logger.info(init_msg, __name__)
	yield (None, f"Initializing FusionFlows RIFE 3.1 ({current_fps} -> {target_fps} FPS)...")

	temp_dir = tempfile.mkdtemp(prefix='fusionflows_')
	temp_assembled = output_path + ".assembling.mp4"

	try:
		# Step 1: Extract Audio (if present)
		audio_file = os.path.join(temp_dir, 'audio.aac')
		audio_extracted = False
		if has_audio_stream(video_path):
			logger.info(f"[FUSIONFLOWS] Extracting audio stream from source video...", __name__)
			res_audio = subprocess.run(
				['ffmpeg', '-y', '-i', video_path, '-vn', '-c:a', 'copy', audio_file],
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL
			)
			if res_audio.returncode != 0 or not os.path.isfile(audio_file) or os.path.getsize(audio_file) == 0:
				res_audio = subprocess.run(
					['ffmpeg', '-y', '-i', video_path, '-vn', '-c:a', 'aac', '-b:a', '192k', audio_file],
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL
				)
			audio_extracted = os.path.isfile(audio_file) and os.path.getsize(audio_file) > 0
			if audio_extracted:
				logger.info(f"[FUSIONFLOWS] Audio stream successfully extracted.", __name__)

		# Step 2: Separate Frames
		frames_pass_0 = os.path.join(temp_dir, 'frames_pass_0')
		os.makedirs(frames_pass_0, exist_ok=True)
		extract_msg = f"[FUSIONFLOWS] Separating video frames into individual images..."
		logger.info(extract_msg, __name__)
		yield (None, "Separating video frames into individual images...")

		res_extract = subprocess.run(
			['ffmpeg', '-y', '-i', video_path, '-qscale:v', '1', '-pix_fmt', 'rgb24', os.path.join(frames_pass_0, '%08d.png')],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)

		if res_extract.returncode != 0:
			err_msg = "[FUSIONFLOWS] Failed to extract frames from video."
			logger.error(err_msg, __name__)
			yield (None, err_msg)
			return

		extracted_files = glob.glob(os.path.join(frames_pass_0, '*.png'))
		input_frame_count = len(extracted_files)
		if input_frame_count == 0:
			err_msg = "[FUSIONFLOWS] No frames were extracted from video."
			logger.error(err_msg, __name__)
			yield (None, err_msg)
			return

		logger.info(f"[FUSIONFLOWS] Successfully separated {input_frame_count} frames.", __name__)
		yield (None, f"Extracted {input_frame_count} frames. Starting RIFE 3.1 neural interpolation...")

		# Step 3: Neural Frame Pairing & Interpolation (RIFE 3.1)
		total_passes = 1 if factor == 2 else (2 if factor == 4 else 3)
		current_in_dir = frames_pass_0
		current_frames = input_frame_count

		for pass_idx in range(1, total_passes + 1):
			current_out_dir = os.path.join(temp_dir, f'frames_pass_{pass_idx}')
			os.makedirs(current_out_dir, exist_ok=True)
			pass_target = (current_frames - 1) * 2 + 1

			pass_start_msg = f"[FUSIONFLOWS] Starting RIFE 3.1 Pass {pass_idx}/{total_passes} ({current_frames} -> {pass_target} frames)..."
			logger.info(pass_start_msg, __name__)
			yield (None, f"**FusionFlows RIFE 3.1:** Pass {pass_idx}/{total_passes} started...")

			cmd_rife = [
				rife_exe,
				'-i', current_in_dir,
				'-o', current_out_dir,
				'-m', model_dir
			]

			env = os.environ.copy()
			extra_ld_paths = [
				os.path.dirname(rife_exe),
				'/usr/lib/x86_64-linux-gnu',
				'/usr/local/lib',
				'/usr/lib64'
			]
			current_ld = env.get('LD_LIBRARY_PATH', '')
			env['LD_LIBRARY_PATH'] = ':'.join(extra_ld_paths) + (':' + current_ld if current_ld else '')

			proc = subprocess.Popen(
				cmd_rife,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.PIPE,
				env=env
			)

			last_logged_pct = -10
			while proc.poll() is None:
				if process_manager.is_stopping():
					proc.terminate()
					yield (None, "Interrupted")
					return

				current_done = len(glob.glob(os.path.join(current_out_dir, '*.png')))
				pct = min(100.0, round(current_done / pass_target * 100, 1)) if pass_target else 0.0
				status_str = f"**FusionFlows RIFE 3.1:** Pass {pass_idx}/{total_passes} | Frame {current_done}/{pass_target} ({pct}%)"

				if int(pct) >= last_logged_pct + 5:
					logger.info(f"[FUSIONFLOWS] {status_str}", __name__)
					last_logged_pct = int(pct)

				yield (None, status_str)
				time.sleep(0.5)

			proc.wait()

			if proc.returncode != 0:
				err_output = ""
				try:
					if proc.stderr:
						err_output = proc.stderr.read().decode(errors='ignore').strip()
				except Exception:
					pass
				err_msg = f"[FUSIONFLOWS] RIFE 3.1 failed on Pass {pass_idx} with exit code {proc.returncode}: {err_output}"
				logger.warn(f"{err_msg}. Triggering automatic High-Quality Motion Interpolation Fallback...", __name__)
				yield (None, f"RIFE error ({proc.returncode}). Using Motion Interpolation to generate {target_fps} FPS...")

				if run_ffmpeg_motion_interpolation(video_path, target_fps, output_path):
					complete_msg = f"[FUSIONFLOWS] 2x FPS Video Interpolation complete ({current_fps} -> {target_fps} FPS)!"
					logger.info(complete_msg, __name__)
					yield (output_path, complete_msg)
					return
				else:
					yield (None, err_msg)
					return

			current_frames = len(glob.glob(os.path.join(current_out_dir, '*.png')))
			logger.info(f"[FUSIONFLOWS] Pass {pass_idx}/{total_passes} complete! {current_frames} frames generated.", __name__)

			# Cleanup previous pass input frames to save disk space
			if pass_idx > 1:
				shutil.rmtree(current_in_dir, ignore_errors=True)
			current_in_dir = current_out_dir

		# Step 4: Re-encode & Mux Audio
		final_frames_dir = current_in_dir
		asm_msg = f"[FUSIONFLOWS] Assembling {current_frames} frames into final video at {target_fps} FPS..."
		logger.info(asm_msg, __name__)
		yield (None, f"Assembling final video at {target_fps} FPS with audio...")

		if audio_extracted:
			cmd_assemble = [
				'ffmpeg', '-y',
				'-framerate', str(target_fps),
				'-i', os.path.join(final_frames_dir, '%08d.png'),
				'-i', audio_file,
				'-map', '0:v',
				'-map', '1:a',
				'-c:v', 'libx264',
				'-crf', '18',
				'-preset', 'fast',
				'-pix_fmt', 'yuv420p',
				'-c:a', 'aac',
				'-b:a', '192k',
				'-shortest',
				temp_assembled
			]
		else:
			cmd_assemble = [
				'ffmpeg', '-y',
				'-framerate', str(target_fps),
				'-i', os.path.join(final_frames_dir, '%08d.png'),
				'-c:v', 'libx264',
				'-crf', '18',
				'-preset', 'fast',
				'-pix_fmt', 'yuv420p',
				temp_assembled
			]

		res_asm = subprocess.run(cmd_assemble, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
		if res_asm.returncode == 0 and os.path.isfile(temp_assembled):
			if os.path.exists(output_path):
				os.remove(output_path)
			shutil.move(temp_assembled, output_path)
			complete_msg = f"[FUSIONFLOWS] FusionFlows RIFE 3.1 interpolation complete: {current_fps} FPS -> {target_fps} FPS ({factor}x)!"
			logger.info(complete_msg, __name__)
			yield (output_path, complete_msg)
			return
		else:
			err_str = res_asm.stderr.decode(errors='ignore') if res_asm.stderr else "Unknown error"
			logger.warn(f"[FUSIONFLOWS] Assembly failed: {err_str}. Trying motion interpolation fallback...", __name__)
			if run_ffmpeg_motion_interpolation(video_path, target_fps, output_path):
				complete_msg = f"[FUSIONFLOWS] 2x FPS Video Interpolation complete ({current_fps} -> {target_fps} FPS)!"
				logger.info(complete_msg, __name__)
				yield (output_path, complete_msg)
				return
			yield (None, f"Error assembling video: {err_str}")
			return

	except Exception as exception:
		logger.error(f"[FUSIONFLOWS] Exception during interpolation: {exception}", __name__)
		yield (None, f"Error: {exception}")

	finally:
		if os.path.exists(temp_dir):
			shutil.rmtree(temp_dir, ignore_errors=True)
		if os.path.exists(temp_assembled):
			try:
				os.remove(temp_assembled)
			except OSError:
				pass
