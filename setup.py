from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

version = "0.0.2"

TEST_REQUIREMENTS = [
    'TurboGears2',
    'WebTest==1.4.3',
    'repoze.who',
    'nose',
    'coverage',
    'mock',
    'pastedeploy',
    'formencode',
    'anypubsub'
]

setup(name='tgext.socketio',
      version=version,
      description="SocketIO support for TurboGears through gevent-socketio",
      long_description=README,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='turbogears2.extension, socketio, gevent',
      author='Alessandro Molina',
      author_email='alessandro.molina@axant.it',
      url='http://github.com/amol-/tgext.socketio',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['tgext'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'gevent<1.2.0',
          'gevent-socketio'
      ],
      test_suite='nose.collector',
      tests_require=TEST_REQUIREMENTS,
      extras_require={
        'testing': TEST_REQUIREMENTS,
      },
      entry_points={
        'paste.server_runner': [
            'socketio = tgext.socketio.server:socketio_server_runner'
        ]
      }
)
