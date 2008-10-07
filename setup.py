#!/usr/bin/env python
import __init__

from distutils.core import setup

if __name__ == '__main__':

    setup(
        name = __init__.__name__,
        version = __init__.__version__,
        license = __init__.__license__,
        description = __init__.__description__,
        author = __init__.__author__,
        packages = ['anybot', 'anybot.im'],
        package_dir = {'anybot': '.'}
        )
        
