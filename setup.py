from setuptools import setup, find_packages
import os

setup(
    name='iris_ransomwarelive',
    version='3.3.1',
    author='DFIR Team',
    description='DFIR-IRIS Ransomware.live Integration Module',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires='>=3.8,<3.14',
    install_requires=[
        'requests>=2.28.0,<3.0.0',
        'iris-module-interface>=1.2.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
