import pkg_resources

from .cache import Cache


__version__ = pkg_resources.get_distribution('mds-agency-validator').version


cache = Cache()
