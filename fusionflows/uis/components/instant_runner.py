import os
from pathlib import Path
import secrets
from time import sleep
from typing import Generator, Optional, Tuple

import gradio

from fusionflows import process_manager, state_manager, translator
from fusionflows.args import collect_step_args
from fusionflows.core import process_step
from fusionflows.filesystem import get_file_extension, get_file_name, is_directory, is_image, is_video
from fusionflows.jobs import job_helper, job_manager, job_runner, job_store
from fusionflows.temp_helper import clear_temp_directory
from fusionflows.types import UiWorkflow
from fusionflows.uis.core import get_ui_component

INSTANT_RUNNER_WRAPPER : Optional[gradio.Column] = None
INSTANT_RUNNER_START_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_STATUS : Optional[gradio.Markdown] = None


def suggest_unique_output_path(output_directory_path : str, target_path : str) -> str:
	ext = get_file_extension(target_path) or ('.mp4' if is_video(target_path) else '.png')
	while True:
		random_hex = secrets.token_hex(4)
		candidate = os.path.join(output_directory_path, f"{random_hex}{ext}")
		if not os.path.exists(candidate):
			return candidate


def render() -> None:
	global INSTANT_RUNNER_WRAPPER
	global INSTANT_RUNNER_START_BUTTON
	global INSTANT_RUNNER_STOP_BUTTON
	global INSTANT_RUNNER_CLEAR_BUTTON
	global INSTANT_RUNNER_STATUS

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_instant_runner = state_manager.get_item('ui_workflow') == 'instant_runner'

		with gradio.Column(visible = is_instant_runner) as INSTANT_RUNNER_WRAPPER:
			with gradio.Row():
				INSTANT_RUNNER_START_BUTTON = gradio.Button(
					value = translator.get('uis.start_button'),
					variant = 'primary',
					size = 'sm'
				)
				INSTANT_RUNNER_STOP_BUTTON = gradio.Button(
					value = translator.get('uis.stop_button'),
					variant = 'primary',
					size = 'sm',
					visible = False
				)
				INSTANT_RUNNER_CLEAR_BUTTON = gradio.Button(
					value = translator.get('uis.clear_button'),
					size = 'sm'
				)
			INSTANT_RUNNER_STATUS = gradio.Markdown(
				value = "",
				visible = False
			)


def listen() -> None:
	output_image = get_ui_component('output_image')
	output_video = get_ui_component('output_video')
	ui_workflow_dropdown = get_ui_component('ui_workflow_dropdown')

	if output_image and output_video:
		INSTANT_RUNNER_START_BUTTON.click(run, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, output_image, output_video, INSTANT_RUNNER_STATUS ])
		INSTANT_RUNNER_STOP_BUTTON.click(stop, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, output_image, output_video, INSTANT_RUNNER_STATUS ])
		INSTANT_RUNNER_CLEAR_BUTTON.click(clear, outputs = [ output_image, output_video, INSTANT_RUNNER_STATUS ])
	if ui_workflow_dropdown:
		ui_workflow_dropdown.change(remote_update, inputs = ui_workflow_dropdown, outputs = INSTANT_RUNNER_WRAPPER)


def remote_update(ui_workflow : UiWorkflow) -> gradio.Column:
	is_instant_runner = ui_workflow == 'instant_runner'
	return gradio.Column(visible = is_instant_runner)


def start() -> Tuple[gradio.Button, gradio.Button, gradio.Markdown]:
	target_paths = state_manager.get_item('target_paths') or []
	if not target_paths and state_manager.get_item('target_path'):
		target_paths = [ state_manager.get_item('target_path') ]

	total = len(target_paths)
	msg = f"⏳ Starting queue ({total} item{'s' if total != 1 else ''})..." if total else "⏳ Starting..."
	return gradio.Button(visible = False), gradio.Button(visible = True), gradio.Markdown(value = msg, visible = True)


def run() -> Generator[Tuple[gradio.Button, gradio.Button, gradio.Image, gradio.Video, gradio.Markdown], None, None]:
	target_paths = state_manager.get_item('target_paths') or []
	if not target_paths and state_manager.get_item('target_path'):
		target_paths = [ state_manager.get_item('target_path') ]

	if not target_paths:
		yield (
			gradio.Button(visible = True),
			gradio.Button(visible = False),
			gradio.Image(value = None),
			gradio.Video(value = None),
			gradio.Markdown(value = "⚠️ Please select a target image or video first.", visible = True)
		)
		return

	step_args = collect_step_args()
	base_output = step_args.get('output_path')
	if not base_output:
		base_output = str(Path.home().joinpath('Downloads'))
	base_output_dir = str(base_output) if is_directory(str(base_output)) else os.path.dirname(str(base_output))

	total_items = len(target_paths)
	processed_count = 0
	last_output_image = None
	last_output_video = None

	for index, current_target in enumerate(target_paths):
		if process_manager.is_stopping():
			break

		file_name = os.path.basename(current_target)
		status_msg = f"⏳ **Queue [{index + 1}/{total_items}]:** Processing `{file_name}`..."
		yield (
			gradio.Button(visible = False),
			gradio.Button(visible = True),
			gradio.Image(value = last_output_image, visible = bool(last_output_image)),
			gradio.Video(value = last_output_video, visible = bool(last_output_video)),
			gradio.Markdown(value = status_msg, visible = True)
		)

		state_manager.set_item('target_path', current_target)
		current_output = suggest_unique_output_path(base_output_dir, current_target)
		current_step_args = step_args.copy()
		current_step_args['target_path'] = current_target
		current_step_args['output_path'] = current_output

		if job_manager.init_jobs(state_manager.get_item('jobs_path')):
			job_id = job_helper.suggest_job_id('ui')
			for key in job_store.get_job_keys():
				state_manager.sync_item(key)

			if job_manager.create_job(job_id) and job_manager.add_step(job_id, current_step_args) and job_manager.submit_job(job_id):
				success = job_runner.run_job(job_id, process_step)
				if success and os.path.exists(current_output):
					processed_count += 1
					if is_image(current_output):
						last_output_image = current_output
						last_output_video = None
					elif is_video(current_output):
						factor = state_manager.get_item('flowframes_factor') or '2x'
						if factor and factor != '1x':
							from fusionflows.flowframes_runner import interpolate_video_with_progress
							for interp_out, progress_status in interpolate_video_with_progress(current_output, factor, current_output):
								if process_manager.is_stopping():
									break
								interp_msg = f"**FusionFlows [{index + 1}/{total_items}]:** {progress_status}"
								yield (
									gradio.Button(visible = False),
									gradio.Button(visible = True),
									gradio.Image(value = last_output_image, visible = bool(last_output_image)),
									gradio.Video(value = last_output_video, visible = bool(last_output_video)),
									gradio.Markdown(value = interp_msg, visible = True)
								)
								if interp_out and os.path.exists(interp_out):
									current_output = interp_out
						last_output_video = current_output
						last_output_image = None

		if is_video(current_target):
			clear_temp_directory(current_target)

	state_manager.set_item('output_path', base_output)

	if process_manager.is_stopping():
		final_msg = f"⏹️ **Queue Stopped.** Completed {processed_count} of {total_items} items."
	else:
		final_msg = f"✅ **Queue Complete!** Processed {processed_count} of {total_items} items into `{base_output_dir}`"

	yield (
		gradio.Button(visible = True),
		gradio.Button(visible = False),
		gradio.Image(value = last_output_image, visible = bool(last_output_image)),
		gradio.Video(value = last_output_video, visible = bool(last_output_video)),
		gradio.Markdown(value = final_msg, visible = True)
	)


def stop() -> Tuple[gradio.Button, gradio.Button, gradio.Image, gradio.Video, gradio.Markdown]:
	process_manager.stop()
	return (
		gradio.Button(visible = True),
		gradio.Button(visible = False),
		gradio.Image(value = None),
		gradio.Video(value = None),
		gradio.Markdown(value = "⏹️ Stopping queue...", visible = True)
	)


def clear() -> Tuple[gradio.Image, gradio.Video, gradio.Markdown]:
	while process_manager.is_processing():
		sleep(0.5)
	if state_manager.get_item('target_path'):
		clear_temp_directory(state_manager.get_item('target_path'))
	state_manager.clear_item('target_paths')
	state_manager.clear_item('target_path')
	return gradio.Image(value = None), gradio.Video(value = None), gradio.Markdown(value = "", visible = False)
