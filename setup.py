import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pgesmd_self_access",
    version="0.0.5",
    author="J.P. Hutchins",
    author_email="jphutchins@gmail.com",
    description="PG&E Share My Data API for Self Access users",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JPHutchins/pgesmd_self_access",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pytz", "requests",],
    python_requires=">=3.8",
)
