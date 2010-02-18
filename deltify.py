#!/usr/bin/python
import sys
import os.path
import subprocess
import tarfile
from glob import glob
from itertools import groupby
from multiprocessing import Pool
from alpm import vercmp


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


def group_pkgs(pkg_list, delta_list):
    keyfunc = lambda x: os.path.basename(x.rsplit('-', 3)[0])
    s_pkg_list = sorted(pkg_list, key=keyfunc)
    name2pkgs = {}
    for k, g in groupby(s_pkg_list, keyfunc):
        name2pkgs.setdefault(k, {})['pkg_list'] = sorted(g, key=CmpToKey(vercmp))

    d_keyfunc = lambda x: os.path.basename(x.rsplit('-', 4)[0])
    s_delta_list = sorted(delta_list, key=d_keyfunc)
    for k, g in groupby(s_delta_list, d_keyfunc):
        name2pkgs.setdefault(k, {})['delta_list'] = sorted(g, key=CmpToKey(vercmp))
    return name2pkgs

def create_delta(old, new, delta):
    delta_fh = open(delta, 'w')
    p1 = subprocess.Popen(["xdelta3", "-q0fs", old, new], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["xz", "-c"], stdin=p1.stdout, stdout=delta_fh)
    ret1 = p1.wait()
    ret2 = p2.wait()
    delta_fh.close()
    return (ret1 + ret2) == 0

def create_deltas(pkg_info, delta_dir, delta_cnt):
    pkg_list = pkg_info.get('pkg_list', [])
    delta_list = pkg_info.get('delta_list', [])
    pkg_list_len = len(pkg_list)
    pkg_offset = delta_cnt
    if pkg_list_len <= delta_cnt + 1:
        pkg_offset = pkg_list_len - 1
    pkg_size = os.path.getsize(pkg_list[-1])
    delta_size = 0
    failed = False
    if pkg_list_len > 1:
        for i in range(pkg_list_len-pkg_offset, pkg_list_len)[::-1]:
            old = pkg_list[i-1]
            new = pkg_list[i]
            old_s = os.path.basename(old).rsplit('-', 3)
            new_s = os.path.basename(new).rsplit('-', 3)
            old_name = old_s[0]
            old_ver = '-'.join(old_s[1:3])
            old_arch= old_s[3].split('.')[0]
            new_name = new_s[0]
            new_ver = '-'.join(new_s[1:3])
            new_arch= new_s[3].split('.')[0]
            delta = '%s-%s_to_%s-%s.delta' % (new_name, old_ver, new_ver, new_arch)
            delta = os.path.join(delta_dir, delta)

            if not delta in delta_list:
                print "creating delta: %s -> %s => %s" % tuple(os.path.basename(x) for x in (old, new, delta))
                if create_delta(old, new, delta):
                    delta_list.append(delta)
                else:
                    print "failed to create delta from %s => %s" % (old, new)
                    failed = True
                    break

            delta_size += os.path.getsize(delta)
            if delta_size > pkg_size * 0.7:
                print "Delta size too big: %s" % delta
                break

    if not failed:
        delete_list = delta_list[:-delta_cnt]
        size = 0
        for delta in delta_list[::-1]:
            size += os.path.getsize(delta)
            if size > pkg_size * 0.7 and delta not in delete_list:
                delete_list.append(delta)

        delete_list += pkg_list[:-1]
        for pkg in delete_list:
            print "deleting %s" % pkg
            #os.unlink(pkg)


def create_deltas_mp(args):
    create_deltas(*args)
        


# variables/parse user input
NUM_DELTAS = 3
dir = sys.argv[1]
delta_dir = os.path.join(dir, 'deltas')
if not os.path.isdir(delta_dir):
    os.mkdir(delta_dir)

# search for pkgs
pkg_list = glob(os.path.join(dir, '*-i686.pkg.tar.gz'))
pkg_list += glob(os.path.join(dir, '*-x86_64.pkg.tar.gz'))
pkg_list += glob(os.path.join(dir, '*-any.pkg.tar.gz'))
delta_list = glob(os.path.join(delta_dir, '*.delta'))
name2pkgs = group_pkgs(pkg_list, delta_list)

# clean up anything not in db
db_list = glob(os.path.join(dir, '*.db.tar.gz'))
valid = set()
for db in db_list:
    valid.update(set(x.rsplit('-', 2)[0] for x in tarfile.open(db).getnames() if '/' not in x))
for name in set(name2pkgs.keys()) - valid:
    for pkg in reduce(lambda x,y: x+y, name2pkgs[name].values()):
        print "deleting: %s" % pkg
        #os.unlink(pkg)
    else:
        del name2pkgs[name]

# create deltas
p = Pool()
p.map(create_deltas_mp, [(pkg_info, delta_dir, NUM_DELTAS) for pkg_info in name2pkgs.values()])
#for name, pkgs in name2pkgs.iteritems():
#    print "processing: %s" % name
#    create_deltas(pkgs, delta_dir, NUM_DELTAS)
