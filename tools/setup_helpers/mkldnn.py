import platform
import glob
import os
import sys

from itertools import chain
from .env import check_env_flag


def gather_paths(env_vars):
    return list(chain(*(os.getenv(v, '').split(':') for v in env_vars)))

IS_LINUX = platform.system() == 'Linux'
IS_CONDA = 'conda' in sys.version or 'Continuum' in sys.version
CONDA_DIR = os.path.join(os.path.dirname(sys.executable), '..')

MKLDNN_HOME = os.getenv('MKLDNN_HOME', '/usr/local/mkl-dnn')

WITH_MKLDNN = False
MKLDNN_LIB_DIR = None
MKLDNN_INCLUDE_DIR = None
MKLDNN_LIBRARY = None
if IS_LINUX and not check_env_flag('NO_MKLDNN'):
    lib_paths = list(filter(bool, [
        os.getenv('MKLDNN_LIB_DIR'),
        os.path.join(MKLDNN_HOME, 'lib'),
        os.path.join(MKLDNN_HOME, 'lib64'),
        '/usr/lib/',
        '/usr/lib64/',
    ] + gather_paths([
        'LIBRARY_PATH',
    ]) + gather_paths([
        'LD_LIBRARY_PATH',
    ])))
    include_paths = list(filter(bool, [
        os.getenv('MKLDNN_INCLUDE_DIR'),
        os.path.join(MKLDNN_HOME, 'include'),
        '/usr/include/',
    ] + gather_paths([
        'CPATH',
        'C_INCLUDE_PATH',
        'CPLUS_INCLUDE_PATH',
    ])))
    if IS_CONDA:
        lib_paths.append(os.path.join(CONDA_DIR, 'lib'))
        include_paths.append(os.path.join(CONDA_DIR, 'include'))
    for path in lib_paths:
        if path is None or not os.path.exists(path):
            continue
        else:
            libraries = sorted(glob.glob(os.path.join(path, 'libmkldnn*')))
            if libraries:
                if not glob.glob(os.path.join(path, 'libmklml_intel*')):
                    print("WARNING: MKL-DNN is not compiled with Intel MKL small library")
                    print("Convolution performance might be suboptimal")
                    print("Refer https://github.com/01org/mkl-dnn for detail info")
                MKLDNN_LIBRARY = libraries[0]
                MKLDNN_LIB_DIR = path
                break
    for path in include_paths:
        if path is None or not os.path.exists(path):
            continue
        else:
            if os.path.exists(os.path.join(path, 'mkldnn.hpp')):
                MKLDNN_INCLUDE_DIR = path
                break

    # Specifying the library directly will overwrite the lib directory
    library = os.getenv('MKLDNN_LIBRARY')
    if library is not None and os.path.exists(library):
        MKLDNN_LIBRARY = library
        MKLDNN_LIB_DIR = os.path.dirname(MKLDNN_LIBRARY)

    if not all([MKLDNN_LIBRARY, MKLDNN_LIB_DIR, MKLDNN_INCLUDE_DIR]):
        MKLDNN_LIBRARY = MKLDNN_LIB_DIR = MKLDNN_INCLUDE_DIR = None
    else:
        real_mkldnn_library = os.path.realpath(MKLDNN_LIBRARY)
        real_mkldnn_lib_dir = os.path.realpath(MKLDNN_LIB_DIR)
        assert os.path.dirname(real_mkldnn_library) == real_mkldnn_lib_dir, (
            'mkldnn library and lib_dir must agree')
        WITH_MKLDNN = True
