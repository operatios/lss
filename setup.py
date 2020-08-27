from setuptools import setup, find_packages

with open('README.md') as file:
    long_description = file.read()

setup(
    name='lss',
    version='1.0.0',
    author='operatios',
    description='Cross-platform ls command',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/operatios/lss',
    packages=find_packages(),
    entry_points={
          'console_scripts': ['lss = lss.__main__:main']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8'
    ]
)
