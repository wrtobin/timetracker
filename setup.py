import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="timetracker",
    version="0.1.0",
    author="User",
    description="A simple but powerful time tracking application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "screeninfo>=0.8.1",
    ],
    entry_points={
        "console_scripts": [
            "timetracker=timetracker:main",
        ],
    },
)
