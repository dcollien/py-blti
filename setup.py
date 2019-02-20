from setuptools import setup

setup(
   name='blti',
   version='0.1.8',
   py_modules=['blti'],
   author='David Collien',
   author_email='me@dcollien.com',
   url='https://github.com/dcollien/py-blti',
   license='MIT',
   description='py-blti: basic LTI authentication for python/django',
   long_description='py-blti: A basic LTI Provider authentication decorator for django, and basic LTI Consumer signing function.',
   platforms=['any'],
   install_requires=['oauth2']
)
