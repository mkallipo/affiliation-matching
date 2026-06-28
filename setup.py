import os
import re
from setuptools import setup, find_packages

# Read version from affro/__init__.py
def get_version():
    with open(os.path.join("affro", "__init__.py"), encoding="utf-8") as f:
        content = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="affro",
    version=get_version(),
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "affro": [
            "jsons/*.json.gz",
            "txts/*.txt"
        ],
    },
    install_requires=[], #here you have to list the requirements needed by affro to run for example "
    author="Myrto Kallipoliti",
    description="A tool to resolve organization names to ROR or OpenOrgs IDs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="GPL-3.0-or-later",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        # Other classifiers...
    ],
    url="https://code-repo.d4science.org/mkallipo/affRo"  # Update as needed
)