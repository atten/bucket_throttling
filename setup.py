from setuptools import setup, find_packages
from bucket_throttling.version import __version__

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='bucket_throttling',
    packages=find_packages(),
    license='MIT',
    version=__version__,
    description='Throttling module that uses Token Bucket algorithm.',
    author='Artem Vasilev',
    author_email='art@force.fm',
    url='https://github.com/atten/bucket_throttling',
    download_url='https://github.com/atten/bucket_throttling/archive/master.zip',
    keywords=['throttling', 'bucket', 'django'],
    classifiers=[],
    requires=['redis'],
    install_requires=['redis'],
    long_description=long_description,
)
