from typing import Optional

import gradio

import fusionflows
from fusionflows import state_manager, translator
from fusionflows.uis.core import register_ui_component

UI_WORKFLOW_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global UI_WORKFLOW_DROPDOWN

	UI_WORKFLOW_DROPDOWN = gradio.Dropdown(
		label = translator.get('uis.ui_workflow'),
		choices = fusionflows.choices.ui_workflows,
		value = state_manager.get_item('ui_workflow'),
		interactive = True
	)
	register_ui_component('ui_workflow_dropdown', UI_WORKFLOW_DROPDOWN)
