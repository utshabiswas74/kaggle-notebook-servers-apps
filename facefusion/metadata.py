from typing import Optional

METADATA =\
{
	'name': 'FusionFlows',
	'description': 'Advanced Face Manipulation & Neural Frame Interpolation Platform',
	'version': '3.9.1',
	'license': 'OpenRAIL-AS',
	'author': 'FusionFlows Team',
	'url': 'https://github.com/utshabiswas74/fusionflows-windows-apps'
}


def get(key : str) -> Optional[str]:
	return METADATA.get(key)
