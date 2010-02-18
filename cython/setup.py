from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules=[
    Extension("alpm",
              ["alpm.pyx"],
              libraries=["alpm"])
]

setup(
  name = "alpm",
  cmdclass = {"build_ext": build_ext},
  ext_modules = ext_modules
)
