from setuptools import setup

setup(
    name='md2notion',
    version='2.0.1',
    description='Utilities for importing Markdown files to Notion.so',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/Cobertos/md2notion/',
    author='Cobertos',
    author_email='me+python@cobertos.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business :: News/Diary',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities'
    ],
    install_requires=[
        'mistletoe>=0.7.2',
        'notion>=0.0.25',
        'requests>=2.22.0',
    ],
    keywords='notion notion.so notion-py markdown md converter',
    packages=['md2notion']
)
