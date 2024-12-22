"""Python setup.py for wyoming-azure-speech package."""

import os
from pathlib import Path

from setuptools import find_packages, setup

REPO_URL = "https://github.com/shmuelzon/wyoming-azure-speech"
VERSION = os.environ["VERSION"]


def read(path: str) -> str:
    """Read file contents."""
    with (Path(__file__).parent / path).open(encoding="utf8") as open_file:
        return open_file.read().strip()


def read_requirements(path: str) -> list[str]:
    """Read requirements file."""
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="wyoming-azure-speech",
    version=VERSION,
    description="Wyoming Server for Azure AI Speech",
    url=REPO_URL,
    download_url=REPO_URL + "/tarball/" + VERSION,
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Shmuelzon",
    packages=find_packages(include=["wyoming_azure_speech*"]),
    install_requires=read_requirements("requirements.txt"),
    extras_require={"test": read_requirements("dev-requirements.txt")},
    python_requires=">=3.9",
    license="MIT",
    entry_points={
        "console_scripts": ["wyoming-azure-speech = wyoming_azure_speech.__main__:run"],
    },
)
