from distutils.core import setup

setup(
    name = 'bucket_throttling',
    packages = ['bucket_throttling'],
    license = 'MIT',
    version = '0.1',
    description = 'Throttling module that uses Token Bucket algorithm.',
    author = 'Artem Vasilev',
    author_email = 'art@force.fm',
    url = 'https://github.com/atten/bucket_throttling',
    download_url = 'https://github.com/atten/bucket_throttling/archive/master.zip',
    keywords = ['throttling','bucket','django'],
    classifiers = [],
    requires=['redis'],
    install_requires=['redis'],
)
