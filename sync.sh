#!/bin/bash

set -e
#mirror=ftp://mirror.cs.vt.edu/pub/ArchLinux
#mirror=ftp://mirrors.kernel.org/archlinux
my_mirror=archdelta.net
my_user=xXxXxXxXxXx
my_pass=xXxXxXxXxXx
PATH="$(pwd):$PATH"

gen_metalink() {
    local repo_db=$1
    local repo=${2:-$(basename ${repo_db%.db.tar.gz})}
    echo -n '
<metalink version="3.0" xmlns="http://www.metalinker.org/">
    <files>'
    # add files
    bsdtar xOf $repo_db '*/desc' |
    awk '/%FILENAME%/{fn=$2} /%MD5SUM%/{ md=$2 } /%CSIZE%/{ sz=$2 }
         fn&&md&&sz{ print fn" "md" "sz;fn="";md="";sz="" }' RS= |
    while read name md5sum size;do
        echo -n "
        <file name='$name'>
           <size>$size</size>
           <verification>
               <hash type='md5'>$md5sum</hash>
           </verification>
           <resources>"
        for mirror in "${mirrors[@]}";do
            echo -n "
                <url type='${mirror%%:*}'>$(eval echo $mirror)/$name</url>"
        done
        echo -n "
            </resources>
        </file>"
    done
    echo "
    </files>
</metalink>"
}

mirrors=( $(reflector -h 1 -r|awk '/^[^#]/&&$0=$3') )

for repo in core extra community;do
    repo_path=$repo/os/i686
    local_repo=/var/repos/$repo_path
    repo_db=$repo.db.tar.gz
    mirror=$(eval echo $mirrors)
    [[ ! $mirror ]] && { echo "no mirrors"; exit 1; }
    [[ ! -d $local_repo ]] && mkdir -p $local_repo
    # get db file
    pushd $local_repo
    [[ -f $repo_db ]] && old_stat=$(stat $repo_db)
    wget -N "$mirror/$repo_db"
    # check for changes
    [[ $old_stat = $(stat $repo_db) ]] && continue
    # dl packages
    aria2c -M <(gen_metalink $repo_db)
    # create deltas
    deltify.py .
    # create delta db
    cp $repo.db.tar.gz deltas/$repo.db.tar.gz
    pushd deltas/
    repo-add $repo.db.tar.gz *.delta
    # push changes to our mirror
    lftp -e "mirror -Rve -P2 . $repo/os/i686;exit;" $my_user:$my_pass@$my_mirror/archdelta.net
    popd
    popd
    break
done
