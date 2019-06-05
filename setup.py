import setuptools

long_description = """
### Latest documentation available [at the github repo](https://github.com/stenson/furniture)
"""

setuptools.setup(
    name="furniture",
    version="0.2.3",
    author="Rob Stenson",
    author_email="rob.stenson@gmail.com",
    description="Typesetting and layout utilities for drawing and animating in DrawBot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stenson/furniture",
    packages=[
        "furniture"
    ],
    entry_points={
        'console_scripts': [
            'furniture = furniture.renderer:main'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
