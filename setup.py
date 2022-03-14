from gettext import install
from setuptools import find_packages, setup

setup(
    name='MyMovieGraph',
    version='0.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)