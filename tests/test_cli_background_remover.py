import subprocess
import sys

import pytest

import fusionflows.choices
from fusionflows import ffmpeg, ffmpeg_builder, process_manager
from fusionflows.download import conditional_download
from fusionflows.jobs.job_manager import clear_jobs, init_jobs
from fusionflows.types import WorkflowStrategy
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/fusionflows/fusionflows-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/fusionflows/fusionflows-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


@pytest.mark.parametrize('workflow_strategy', fusionflows.choices.workflow_strategies)
def test_remove_background_to_image(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'fusionflows.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--workflow-strategy', workflow_strategy, '--processors', 'background_remover', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_file('test-remove-background-to-image.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-remove-background-to-image.jpg') is True


@pytest.mark.parametrize('workflow_strategy', fusionflows.choices.workflow_strategies)
def test_remove_background_to_video(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'fusionflows.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--workflow-strategy', workflow_strategy, '--processors', 'background_remover', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_file('test-remove-background-to-video.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-remove-background-to-video.mp4') is True
