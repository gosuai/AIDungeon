import setuptools

setuptools.setup(
    name="gosu-aidungeon-client",
    version="0.0.1",
    author="GOSU.AI",
    author_email="dev@gosu.ai",
    description="Client for AiDungeon server",
    url="https://github.com/gosuai/aidungeon",
    packages=['aidungeon'],
    package_data={'': ['*.yaml', '*.txt']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'pyyaml',
        'profanityfilter',
        'tracery',
        'aiohttp',
    ],
)
