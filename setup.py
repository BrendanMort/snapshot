from setuptools import setup

setup(
    name='snapshot',
    version='0.1',
    author="BrendanMort",
    author_email="brendan.mortensen@gmail.com",
    description="snapshot is a tool to manage AWS EC2 snapshots",
    license="",
    packages=['shotty'],
    url="https://github.com/BrendanMort/snapshot",
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points= '''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',
)
