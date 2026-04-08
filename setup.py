from setuptools import setup, find_packages

setup(
    name="scfvtools",
    version="0.1",
    packages=find_packages(),
    scripts=["scripts/run_scfvtools_scoring.py"],
    package_data={"scfvtools": ["example_data/*"]},
    include_package_data=True,
)
