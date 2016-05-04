#!/usr/bin/env python

from setuptools import setup, find_packages
import os

requirements = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).read()
test_requirements = open(os.path.join(os.path.dirname(__file__), 'test_requirements.txt')).read()

setup(
    name='Flask-Breathalyzer',
    version='0.2.2',
    license='BSD',
    url='https://github.com/mindflayer/flask-breathalyzer',
    author='Giorgio Salluzzo',
    author_email='giorgio.salluzzo@gmail.com',
    description='Flask module for submitting timings and exceptions to Datadog',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=('tests',)),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Framework :: Flask',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    test_suite='runtests.runtests',
    platforms='any',
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        'datadog': ('datadog',),
    },
)
