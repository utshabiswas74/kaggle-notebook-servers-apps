import os
import secrets
from typing import Optional

from fusionflows import state_manager
from fusionflows.filesystem import get_file_extension, is_image, is_video


def convert_int_none(value : int) -> Optional[int]:
	if value == 'none':
		return None
	return value


def convert_str_none(value : str) -> Optional[str]:
	if value == 'none':
		return None
	return value


def suggest_output_path(output_directory_path : str, target_path : str) -> Optional[str]:
	if is_image(target_path) or is_video(target_path):
		target_file_extension = get_file_extension(target_path)
		while True:
			output_file_name = secrets.token_hex(4)
			candidate = os.path.join(output_directory_path, output_file_name + target_file_extension)
			if not os.path.exists(candidate):
				return candidate
	return None
