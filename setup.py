from setuptools import setup, find_packages

setup(
    name='depthai_blazepose',
    version='0.1.0',
    packages=find_packages(include=['data_collection',
                                    'depthai_blazepose',
                                    'depthai_blazepose.utils']),
    install_requires=[
        'opencv-python >= 4.5.1.48',
        'open3d',
        'depthai >= 2.10',
        'pandas',
    ],
    # entry_points={
    #     'console_scripts': []
    # }
)