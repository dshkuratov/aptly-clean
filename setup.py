from setuptools import setup, find_packages

setup(
    name='aptly-clean',
    version='0.0.1',
    packages=find_packages(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'python-apt',
    ],
    entry_points="""
        [console_scripts]
        aptly-clean=aptly_clean.__init__:main
    """,
    long_description="""clear "aptly" old package"""
)
