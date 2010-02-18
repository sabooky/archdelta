cdef extern from "alpm.h":
    int alpm_pkg_vercmp(char *,char *)

cdef int c_alpm_pkg_vercmp(char *a, char *b):
    return alpm_pkg_vercmp(a, b)

def vercmp(char *a, char *b):
    return c_alpm_pkg_vercmp(a, b)
