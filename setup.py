import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tracelang-johnswentworth",
    version="0.0.1",
    author="John S Wentworth",
    author_email="jwentworth@g.hmc.edu",
    description="Read, write and manipulate code which reads, writes and manipulates code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johnswentworth/tracelang",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
