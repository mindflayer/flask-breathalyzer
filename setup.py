#!/usr/bin/env python

from setuptools import setup, find_packages


requirements = [
    'Flask>=0.8',
    'blinker>=1.1',
]
test_requirements = [
    'pytest',
]
datadog_require = [
    'datadog',
]

setup(
    name='Flask-Breathalyzer',
    version='0.1.0',
    license='BSD',
    url='https://github.com/mindflayer/flask-breathalyzer',
    author='Giorgio Salluzzo',
    author_email='giorgio.salluzzo@gmail.com',
    description='Flask module for submitting timings and exceptions to Datadog.',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Framework :: Flask',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    platforms='any',
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        'datadog': datadog_require,
    },
)
