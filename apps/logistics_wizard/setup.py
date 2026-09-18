from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="logistics_wizard",
    version="0.0.1",
    description="Import-Export Workflow Widget and AfterShip API integration",
    author="Khanh",
    author_email="khanh@logistics.local",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
