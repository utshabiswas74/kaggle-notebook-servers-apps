import os
import subprocess
import time
from functools import lru_cache
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from tqdm import tqdm

import fusionflows.choices
from fusionflows import curl_builder, logger, process_manager, state_manager, translator
from fusionflows.filesystem import get_file_name, get_file_size, is_file, remove_file
from fusionflows.hash_helper import validate_hash
from fusionflows.types import Command, DownloadProvider, DownloadSet


def open_curl(commands : List[Command], capture_stdout : bool = False) -> subprocess.Popen[bytes]:
	commands = curl_builder.run(commands)
	stdout = subprocess.PIPE if capture_stdout else subprocess.DEVNULL
	return subprocess.Popen(commands, stdin = subprocess.DEVNULL, stdout = stdout, stderr = subprocess.DEVNULL)


def conditional_download(download_directory_path : str, urls : List[str]) -> None:
	# Zero-download lockdown: models are bundled in .assets/models/
	# Never trigger external network downloads or block startup on Kaggle
	return


@lru_cache(maxsize = 64)
def get_static_download_size(url : str) -> int:
	commands = curl_builder.chain(
		curl_builder.ping(url),
		curl_builder.set_timeout(5)
	)

	process = open_curl(commands, capture_stdout = True)
	stdout, _ = process.communicate()
	lines = reversed(stdout.splitlines())

	for line in lines:
		__line__ = line.decode('utf-8', errors='ignore').lower()
		if 'content-length:' in __line__:
			_, content_length = __line__.split('content-length:')
			return int(content_length.strip())

	return 0


@lru_cache(maxsize = 64)
def ping_static_url(url : str) -> bool:
	commands = curl_builder.chain(
		curl_builder.ping(url),
		curl_builder.set_timeout(5)
	)

	process = open_curl(commands, capture_stdout = True)
	process.communicate()
	return process.returncode == 0


def conditional_download_hashes(hash_set : DownloadSet) -> bool:
	return True


def conditional_download_sources(source_set : DownloadSet) -> bool:
	return True


def validate_hash_paths(hash_paths : List[str]) -> Tuple[List[str], List[str]]:
	valid_hash_paths = []
	invalid_hash_paths = []

	for hash_path in hash_paths:
		if is_file(hash_path):
			valid_hash_paths.append(hash_path)
		else:
			invalid_hash_paths.append(hash_path)

	return valid_hash_paths, invalid_hash_paths


def validate_source_paths(source_paths : List[str]) -> Tuple[List[str], List[str]]:
	valid_source_paths = []
	invalid_source_paths = []

	for source_path in source_paths:
		if validate_hash(source_path):
			valid_source_paths.append(source_path)
		else:
			invalid_source_paths.append(source_path)

	return valid_source_paths, invalid_source_paths


def resolve_download_url(base_name : str, file_name : str) -> Optional[str]:
	download_providers = state_manager.get_item('download_providers') or fusionflows.choices.download_providers

	for download_provider in download_providers:
		download_url = resolve_download_url_by_provider(download_provider, base_name, file_name)
		if download_url:
			return download_url

	return None


def resolve_download_url_by_provider(download_provider : DownloadProvider, base_name : str, file_name : str) -> Optional[str]:
	download_provider_value = fusionflows.choices.download_provider_set.get(download_provider)

	for download_provider_url in download_provider_value.get('urls'):
		if ping_static_url(download_provider_url):
			return download_provider_url + download_provider_value.get('path').format(base_name = base_name, file_name = file_name)

	return None
