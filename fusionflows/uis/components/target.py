from typing import List, Optional, Tuple, Union

import gradio

from fusionflows import state_manager, translator
from fusionflows.face_store import clear_faces
from fusionflows.filesystem import is_image, is_video
from fusionflows.uis.core import register_ui_component
from fusionflows.uis.types import ComponentOptions, File

TARGET_FILE : Optional[gradio.File] = None
TARGET_IMAGE : Optional[gradio.Image] = None
TARGET_VIDEO : Optional[gradio.Video] = None


def render() -> None:
	global TARGET_FILE
	global TARGET_IMAGE
	global TARGET_VIDEO

	target_paths = state_manager.get_item('target_paths') or []
	if not target_paths and state_manager.get_item('target_path'):
		target_paths = [ state_manager.get_item('target_path') ]

	first_target = target_paths[0] if target_paths else None
	is_target_image = is_image(first_target) if first_target else False
	is_target_video = is_video(first_target) if first_target else False

	TARGET_FILE = gradio.File(
		label = translator.get('uis.target_file'),
		file_count = 'multiple',
		value = target_paths if target_paths else None
	)
	target_image_options : ComponentOptions =\
	{
		'show_label': False,
		'visible': False
	}
	target_video_options : ComponentOptions =\
	{
		'show_label': False,
		'visible': False
	}
	if is_target_image and first_target:
		target_image_options['value'] = first_target
		target_image_options['visible'] = True
	if is_target_video and first_target:
		target_video_options['value'] = first_target
		target_video_options['visible'] = True

	TARGET_IMAGE = gradio.Image(**target_image_options)
	TARGET_VIDEO = gradio.Video(**target_video_options)

	register_ui_component('target_image', TARGET_IMAGE)
	register_ui_component('target_video', TARGET_VIDEO)


def listen() -> None:
	TARGET_FILE.change(update, inputs = TARGET_FILE, outputs = [ TARGET_IMAGE, TARGET_VIDEO ])


def update(files : Union[File, List[File], None]) -> Tuple[gradio.Image, gradio.Video]:
	clear_faces()

	if not files:
		state_manager.clear_item('target_path')
		state_manager.clear_item('target_paths')
		return gradio.Image(value = None, visible = False), gradio.Video(value = None, visible = False)

	if not isinstance(files, list):
		files = [ files ]

	file_names = []
	for f in files:
		if hasattr(f, 'name') and f.name:
			file_names.append(f.name)
		elif isinstance(f, dict) and f.get('path'):
			file_names.append(f.get('path'))
		elif isinstance(f, str) and f:
			file_names.append(f)

	valid_paths = [ p for p in file_names if is_image(p) or is_video(p) ]

	if not valid_paths:
		state_manager.clear_item('target_path')
		state_manager.clear_item('target_paths')
		return gradio.Image(value = None, visible = False), gradio.Video(value = None, visible = False)

	state_manager.set_item('target_paths', valid_paths)
	state_manager.set_item('target_path', valid_paths[0])

	first_path = valid_paths[0]
	if is_image(first_path):
		return gradio.Image(value = first_path, visible = True), gradio.Video(value = None, visible = False)
	if is_video(first_path):
		return gradio.Image(value = None, visible = False), gradio.Video(value = first_path, visible = True)

	return gradio.Image(value = None, visible = False), gradio.Video(value = None, visible = False)
