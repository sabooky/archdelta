#!/bin/bash

set -e
mirror=ftp://mirror.cs.vt.edu/pub/ArchLinux
#mirror=ftp://mirrors.kernel.org/archlinux
my_mirror=archdelta.net
my_user=xXxXxXxXxXx
my_pass=xXxXxXxXxXx
PATH="$(pwd):$PATH"

for repo in core extra community;do
    pushd /var/repos/$repo/os/i686
    list=$(ls -l)
    lftp -e 'mirror -cvrL;exit' "$mirror/$repo/os/i686"
    if ! [[ $list == $(ls -l) ]];then
        deltify.py .
        cp $repo.db.tar.gz deltas/$repo.db.tar.gz
        pushd deltas
        repo-add $repo.db.tar.gz *.delta
        lftp -e "mirror -Rvce . $repo/os/i686;exit;" $my_user:$my_pass@$my_mirror/archdelta.net
        popd
    fi
    popd
done
