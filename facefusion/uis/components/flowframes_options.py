from typing import Optional

import gradio

import facefusion.choices
from facefusion import state_manager
from facefusion.filesystem import is_video
from facefusion.uis.core import get_ui_components, register_ui_component

FLOWFRAMES_FACTOR_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global FLOWFRAMES_FACTOR_DROPDOWN

	target_path = state_manager.get_item('target_path')
	has_target_video = is_video(target_path) if target_path else False

	if not state_manager.get_item('flowframes_factor'):
		state_manager.set_item('flowframes_factor', '2x')

	FLOWFRAMES_FACTOR_DROPDOWN = gradio.Dropdown(
		label = "Target FPS Multiplier (FusionFlows)",
		choices = facefusion.choices.flowframes_factors,
		value = state_manager.get_item('flowframes_factor') or '2x',
		visible = has_target_video
	)

	register_ui_component('flowframes_factor_dropdown', FLOWFRAMES_FACTOR_DROPDOWN)


def listen() -> None:
	if FLOWFRAMES_FACTOR_DROPDOWN:
		FLOWFRAMES_FACTOR_DROPDOWN.change(update_flowframes_factor, inputs = FLOWFRAMES_FACTOR_DROPDOWN)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(remote_update, outputs = FLOWFRAMES_FACTOR_DROPDOWN)


def remote_update() -> gradio.Dropdown:
	target_path = state_manager.get_item('target_path')
	has_video = is_video(target_path) if target_path else False

	return gradio.Dropdown(visible = has_video)


def update_flowframes_factor(flowframes_factor: str) -> None:
	state_manager.set_item('flowframes_factor', flowframes_factor)
