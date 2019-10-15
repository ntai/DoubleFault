import setuptools, sys, os

with open("README.md", "r") as fh:
  long_description = fh.read()

# The wce triage is designed to work with Ubuntu 18.04LTS and after
# that comes with Python 3.6. 
python_version = sys.version_info
need_python_version = (3, 6)

if python_version < need_python_version:
  raise RuntimeError("doublefault_bot requires Python version %d.%d or higher"
                     % need_python_version)

sys.path.append(os.getcwd())
from doublefault.version import *

setuptools.setup(
  name="DoubleFault",
  version=BOT_VERSION,
  author="Naoyuki Tai",
  author_email="naoyukitai@gmail.com",
  description="Double Fault - Discord bot for Boston Mystics",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/ntai/doublefault",
  packages=[
    'doublefault'
  ],
  include_package_data=True,
  install_requires=[
    'discord.py>1.2',
  ],
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
  ],
)

