from setuptools import setup

setup(name='Atomic Database',
      version='2.0',
      packages=['AtomicDatabase'],
      entry_points={
          'gui_scripts': [
              'atomicdb = AtomicDatabase.__main__:run'
          ]
      },
      install_requires=['kivy'],

      package_data={
          # If any package contains *.txt or *.rst files, include them:
          '': ['*.txt', '*.rst'],
      },

      # metadata to display on PyPI
      author="Christopher Dumas",
      author_email="christopherdumas@gmai.com",
      description="A EAV-based, logic-powered, natural language enabled, database.",
      license="MIT",
)
