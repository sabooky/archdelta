#!/usr/bin/python

import tarfile
import re
import os.path
import sys
from lxml import etree
from urlparse import urlparse, urljoin


pkg_re = re.compile(r'%(.*)%\n(.*)', re.M)

def repo2ml(repo_db, mirrors):
    repo_db = tarfile.open(fileobj=repo_db)
    descs = [repo_db.extractfile(x) for x in repo_db if x.name.endswith('/desc')]
    
    pkgs = [dict(pkg_re.findall(f.read())) for f in descs]
    metalink = etree.Element('metalink', version="3.0", xmlns="http://www.metalinker.org/")
    files_elm = etree.SubElement(metalink, 'files')
    for pkg in pkgs:
        file_elm = etree.SubElement(files_elm, 'file', name=pkg['FILENAME'])
        etree.SubElement(file_elm, 'size').text = pkg['CSIZE']
        verification_elm = etree.SubElement(file_elm, 'verification')
        hash_elm = etree.SubElement(verification_elm, 'hash', type='md5').text = pkg['MD5SUM']
        resources_elm = etree.SubElement(file_elm, 'resources')
        for mirror in mirrors:
            etree.SubElement(resources_elm, 'url', type=urlparse(mirror)[0]).text = os.path.join(mirror, pkg['FILENAME'])
    
    return etree.tostring(metalink, pretty_print=True)


if __name__ == "__main__":
    mirrors = [ 
        'ftp://mirror.cs.vt.edu/pub/ArchLinux/',
        'ftp://mirrors.kernel.org/archlinux/',
    ]
    print repo2ml(open(sys.argv[1]), mirrors)
