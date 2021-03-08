from distutils.core import setup

VERSION = '0.1'

setup(name='xy_stage_control',
      version=VERSION,
      description='Setup for Controlling the LATRt XY Gantry',
      author='Katie Harrington',
      author_email='kmharrington90@gmail.com',
      package_dir={'xy_wing':'xy_stage', 
                    'xy_agent':'xy_agent'},
      packages=['xy_wing', 'xy_agent'],
     )

