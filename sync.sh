#!/bin/bash

set -e
mirror=ftp://mirror.cs.vt.edu/pub/ArchLinux
#mirror=ftp://mirrors.kernel.org/archlinux
my_mirror=archdelta.net
my_user=xXxXxXxXxXx
my_pass=xXxXxXxXxXx
PATH="$(pwd):$PATH"

for repo in core extra community;do
    repo_path=$repo/os/i686
    local_repo=/var/repos/$repo_path
    repo_db=$repo.db.tar.gz
    [[ -d $local_repo ]] && mkdir -p $local_repo
    pushd $local_repo
    [[ -f $repo_db ]] && old_stat=$(stat $repo_db)
    wget -N "$mirror/$repo_path/$repo_db"
    [[ $old_stat = $(stat $repo_db) ]] && continue
    pkgs=( $(bsdtar xOf $repo.db.tar.gz|sed -n '/%FILENAME%/{n;p}') )
    for pkg in "${pkgs[@]}";do
        [[ -f $pkg ]] || wget "$mirror/$repo_path/$pkg"
    done
    deltify.py .
    cp $repo.db.tar.gz deltas/$repo.db.tar.gz
    pushd deltas/
    repo-add $repo.db.tar.gz *.delta
    lftp -e "mirror -Rve -P2 . $repo/os/i686;exit;" $my_user:$my_pass@$my_mirror/archdelta.net
    popd
    popd
done
