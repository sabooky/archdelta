#!/usr/bin/python
import sys
import os.path
import subprocess
import re
from glob import glob
from itertools import groupby
from multiprocessing import Pool


re_ver = re.compile(r'\d+(?=\D)|[a-zA-Z]+(?=[^a-zA-Z])')


def CmpToKey(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) == -1
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) == 1
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) != 1  
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) != -1
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K


def vercmp(a, b):
    a_base = os.path.basename(a)
    b_base = os.path.basename(b)
    ret = subprocess.call(['vercmp', a_base, b_base], stdout=subprocess.PIPE)
    if ret == 255:
        ret = -1
    return ret

def group_pkgs(pkg_list):
    keyfunc = lambda x: os.path.basename(x.rsplit('-', 3)[0])
    verkey = lambda x: [c.isdigit() and int(c) or c for c in re_ver.findall(x)]
    s_pkg_list = sorted(pkg_list, key=keyfunc)
    name2pkgs = {}
    for k, g in groupby(s_pkg_list, keyfunc):
        #name2pkgs[k] = sorted(g, key=CmpToKey(vercmp))
        name2pkgs[k] = sorted(g, key=verkey)
        #if sorted(g, key=CmpToKey(vercmp)) != sorted(g, key=verkey):
        #    print "you fucked up"
    return name2pkgs

def create_delta(old, new, path=None, delete_old=False, delta_fname = None):
    if not delta_fname:
        old_s = os.path.basename(old).rsplit('-', 3)
        new_s = os.path.basename(new).rsplit('-', 3)
        old_name = old_s[0]
        old_ver = '-'.join(old_s[1:3])
        old_arch= old_s[3].split('.')[0]
        new_name = new_s[0]
        new_ver = '-'.join(new_s[1:3])
        new_arch= new_s[3].split('.')[0]
        if old_name != new_name or old_arch != new_arch:
            return False
        delta_fname = '%s-%s_to_%s-%s.delta' % (new_name, old_ver, new_ver, new_arch)
    if path:
        delta_fname = os.path.join(path, delta_fname)
    if os.path.exists(delta_fname):
        return delta_fname
    delta_fh = open(delta_fname, 'w')
    p1 = subprocess.Popen(["xdelta3", "-q0fs", old, new], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["xz", "-c"], stdin=p1.stdout, stdout=delta_fh)
    p2.wait()
    delta_fh.close()
    return delta_fname

def create_deltas(pkg_list, limit=2):
    if limit:
        pkg_list = pkg_list[-(limit+1):]
    print pkg_list
    current_size = os.path.getsize(pkg_list[-1])
    delta_size = 0
    for i in range(1, len(pkg_list))[::-1]:
        delta_fname = create_delta(pkg_list[i-1], pkg_list[i])
        if delta_fname:
            delta_size += os.path.getsize(delta_fname)
            if delta_size > current_size * 0.7:
                print "Delta too big, deleteing %s" % delta_fname
                os.unlink(delta_fname)
                break
        else:
            print "failed to create delta from %s => %s" % (pkg_list[i-1],pkg_list[i])
        

dir = sys.argv[1]
pkg_list = glob(os.path.join(dir, '*.pkg.tar.gz'))
pkg_list += glob('/var/cache/pacman/pkg/*.pkg.tar.gz')
#pkg_list = glob(dir + 'kernel26-2*i686.pkg.tar.gz')
#pkg_list = []
#pkg_list += glob('/var/cache/pacman/pkg/kernel26-2*i686.pkg.tar.gz')
name2pkgs = group_pkgs(pkg_list)
#p = Pool()
#p.map(create_deltas, name2pkgs.values())
#for name, pkgs in name2pkgs.iteritems():
#    print "processing: %s" % name
#    create_deltas(pkgs)
