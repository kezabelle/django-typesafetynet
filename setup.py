#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['-vvv', '-x', '--durations=10']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

HERE = os.path.abspath(os.path.dirname(__file__))


def make_readme(root_path):
    FILES = ('README.rst', 'LICENSE', 'CHANGELOG', 'CONTRIBUTORS')
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()


LONG_DESCRIPTION = "\r\n\r\n----\r\n\r\n".join(make_readme(HERE))


try:
    from inspect import signature
    INSTALL_REQUIRES = (
        'Django>=1.4',
        'wrapt>=1.10.4',
    )
except ImportError:  # Need to add additional dependency
    INSTALL_REQUIRES = (
        'Django>=1.4',
        'wrapt>=1.10.4',
        'funcsigs>=0.4',
    )


setup(
    name='django-typesafetynet',
    version='0.1.3',
    py_modules=(
        'typesafetynet',
    ),
    packages=(),
    install_requires=INSTALL_REQUIRES,
    tests_require=(
        'pytest>=2.6.4',
        'pytest-cov>=1.8.1',
        'pytest-django>=2.8.0',
        'tox>=1.9.0',
    ),
    cmdclass = {'test': PyTest},
    author='Keryn Knight',
    author_email='python-package@kerynknight.com',
    description="typecasting arguments in Django views via Django Forms",
    long_description=LONG_DESCRIPTION,
    include_package_data=True,
    zip_safe=False,
    license="BSD License",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
