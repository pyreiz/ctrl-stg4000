from distutils.core import setup

setup(
    name='stg',
    version='0.0.1',
    description='Control multichannelsystems STG 4002/4/8.',
    long_description='Toolbox to control  multichannelsystems STG 4002/4/8 via MCS.USB.DLL',
    author='Robert Guggenberger',
    author_email='robert.guggenberger@uni-tuebingen.de',
    url='https://github.com/pyreiz/app-stg4000.git',
    download_url='https://github.com/pyreiz/app-stg4000.git',
    license='MIT',
    packages=['stg'],
    entry_points = {
        'console_scripts': ['stg4000-pulsegui=stg.gui.main:main'],
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries',
        ]
)
