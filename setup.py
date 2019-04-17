from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess

class CustomInstallCommand(install):
    """Custom install setup to help run shell commands (outside shell) before installation"""
    def run(self):
        install.run(self)
        subprocess.run(["python3", "-m", "spacy", "download", "en"])

setup(cmdclass={'install': CustomInstallCommand},
      name='Atomic Database',
      version='2.0',
      packages=find_packages(),
      entry_points={
          'gui_scripts': [
              'atomicdb = AtomicDatabase.__main__:run'
          ]
      },
      install_requires=[
          'imgui[full]',
          'spacy',
          'en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.1.0/en_core_web_sm-2.1.0.tar.gz'],

      package_data={
          # If any package contains *.txt or *.rst files, include them:
          '': ['*.txt', '*.rst'],
      },

      # metadata to display on PyPI
      url="https://github.com/christopherdumas/atomicdatabase/tree/v2.0",
      author="Christopher Dumas",
      author_email="christopherdumas@gmail.com",
      description="A EAV-based, logic-powered, natural language enabled, deductive database.",
      license="MIT",
)
