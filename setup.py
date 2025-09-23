from setuptools import setup, find_packages


setup(
    name="django-docketsearch",
    version="1.0.2",
    author="Nate Vogel",
    author_email="nvogel@clsphila.org",
    description="CLI and web API for searching Pennsylvania public UJS records",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        ujs=ujs_search.bin.cli:ujs
    """,
)
