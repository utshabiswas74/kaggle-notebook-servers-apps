import random
from typing import Optional

import gradio

from fusionflows import metadata, translator

METADATA_BUTTON : Optional[gradio.Button] = None
ACTION_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global METADATA_BUTTON
	global ACTION_BUTTON

	action = random.choice(
	[
		{
			'label': 'GITHUB',
			'url': 'https://github.com/utshabiswas74/fusionflows-windows-apps'
		},
		{
			'label': 'RELEASES',
			'url': 'https://github.com/utshabiswas74/fusionflows-windows-apps/releases'
		},
		{
			'label': 'ISSUES',
			'url': 'https://github.com/utshabiswas74/fusionflows-windows-apps/issues'
		}
	])

	METADATA_BUTTON = gradio.Button(
		value = metadata.get('name') + ' ' + metadata.get('version'),
		variant = 'primary',
		link = metadata.get('url')
	)
	ACTION_BUTTON = gradio.Button(
		value = action.get('label'),
		link = action.get('url'),
		size = 'sm'
	)
