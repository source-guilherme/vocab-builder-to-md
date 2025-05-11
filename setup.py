from setuptools import setup, find_packages  # type: ignore

setup(
    name="vocab-builder-to-md",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "ttkbootstrap",
        # add other dependencies here
    ],
    entry_points={"gui_scripts": ["vocab-builder-to-md = main:main"]},
    include_package_data=True,
    package_data={"": ["src/icon.ico"]},
    author="Your Name",
    description="Vocabulary Builder Exporter",
)
