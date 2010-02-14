#/bin/bash
#wget --retr-symlinks -nH --cut-dirs=5 --mirror ftp://mirror.cs.vt.edu/pub/ArchLinux/core/os/i686
mirror=$1
mirror=${mirror:-ftp://mirror.cs.vt.edu/pub/ArchLinux/core/os/i686}
lftp -e 'mirror -crL;exit' $mirror
