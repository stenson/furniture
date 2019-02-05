import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="furniture-typo",
    version="0.0.1",
    author="Rob Stenson",
    author_email="rob.stenson@gmail.com",
    description="Typesetting and layout utilities for drawing and animating in drawBot",
    long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://github.com/stenson/furniture",
    packages=[
        "furniture"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)