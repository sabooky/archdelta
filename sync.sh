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
    awk '/%NAME%/{n=$2} /%FILENAME%/{fn=$2} /%MD5SUM%/{md=$2} /%CSIZE%/{sz=$2}
         n&&fn&&md&&sz{ print n" "fn" "md" "sz;n="";fn="";md="";sz="" }' RS= |
    while read name fname md5sum size;do
        # skip excludes
        echo "$exclude" | egrep -q "\b$name\b" && continue
        echo -n "
        <file name='$fname'>
           <size>$size</size>
           <verification>
               <hash type='md5'>$md5sum</hash>
           </verification>
           <resources>"
        for mirror in "${mirrors[@]}";do
            echo -n "
                <url type='${mirror%%:*}'>$(eval echo $mirror)/$fname</url>"
        done
        echo -n "
            </resources>
        </file>"
    done
    echo "
    </files>
</metalink>"
}

mirrors=( $(reflector -h 2 -l 10 -r|awk '/^[^#]/&&$0=$3') )
repos="core extra community"
#repos="community"
exclude="vimpager"

for repo in $repos;do
    repo_path=$repo/os/i686
    local_repo=/var/repos/$repo_path
    repo_db=$repo.db.tar.gz
    mirror=$(eval echo $mirrors)
    [[ ! $mirror ]] && { echo "no mirrors"; exit 1; }
    [[ ! -d $local_repo ]] && mkdir -p $local_repo
    # get db file
    pushd $local_repo
    [[ -f $repo_db ]] && old_stat=$(stat -L -c '%Y %s %n' *)
    wget -N "$mirror/$repo_db"
    # dl packages
    aria2c --auto-file-renaming=false -M <(gen_metalink $repo_db)
    # check for changes
    [[ $old_stat = $(stat -L -c '%Y %s %n' *) ]] && continue
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
done
