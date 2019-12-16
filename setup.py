from setuptools import setup

setup(
    name='md2notion',
    version='0.1.1',
    description='A renderer and uploader for Markdown files to notion',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/Cobertos/md2notion/',
    author='Cobertos',
    author_email='me@cobertos.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
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
        'notion>=0.0.24'
    ],
    keywords='notion notion.so notion-py markdown md converter',
    packages=['md2notion']
)
