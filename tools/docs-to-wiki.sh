#!/bin/bash

DESTINATION_DIR=$1

# Mappings from repo's documents to the repo's wiki
DOC_MAPPING="README.md:Home.md \
    doc/Prerequisites.md:Prerequisites.md \
    doc/AdminGuide.md:Installation.md \
    doc/UserGuide.md:Getting-Started.md \
    doc/Links-And-References.md:Links-And-References.md \
    Changelog.md:Changelog.md"

function usage ()
{
    cat <<EOF
USAGE:

  $0 destination_dir

Transforms the relevant documents in this repository into GitHub's wiki
page documents. The destination_dir parameter tells the script the path
to the output, where either an existing wiki checkout is or to an
arbitrary other location.
EOF
}

function check_args ()
{
    if [ "$#" != "1" ]
    then
        usage
        exit 3
    fi
}

function check_file ()
{
    FILE="$1"

    # file should exist
    if [ ! -e "$FILE" ]
    then
        echo "$FILE not found"
        exit 2
    fi

    # no inline external links allowed
    egrep '\[[^]]+]\(http.?://' $FILE > /dev/null 2>&1
    if [ "$?" == "0" ]
    then
        echo "Inline external link found in ${FILE}. Change the links to the"
        echo "named links."
        exit 1
    fi

    # the title should be in the first row
    head -n 1 $FILE | grep "^# " > /dev/null 2>&1
    if [ "$?" != "0" ]
    then
        echo "The level 1 header should be in the first row for $FILE"
        exit 1
    fi
}

function strip_title ()
{
    FILE="$1"
    DEST_FILE="$2"

    sed '1d' $FILE > "$DEST_FILE"
}

function make_full_links ()
{
    OLD_FILE="$1"
    NEW_FILE="$2"
    URL_PREFIX="https://github.com/dice-project/DICE-Deployment-Service/blob/master"
    URL_RAW_PREFIX="https://github.com/dice-project/DICE-Deployment-Service/raw/master"

    DIRNAME="$(dirname $OLD_FILE)"
    if [ "$DIRNAME" == "." ]
    then
        DIRNAME="/"
    else
        DIRNAME="/${DIRNAME}/"
    fi
    URL_PREFIX="${URL_PREFIX}${DIRNAME}"
    URL_RAW_PREFIX="${URL_RAW_PREFIX}${DIRNAME}"

    cat "$NEW_FILE" | \
        ssed -R 's@(?<!!)\[([^\]]+)\]\((?!#)([^)]+)\)@[\1]('$URL_PREFIX'\2)@' | \
        ssed -R 's@!\[([^\]]+)\]\((?!#)([^)]+)\)@![\1]('$URL_RAW_PREFIX'\2)@' > "$NEW_FILE.tmp"
    mv "$NEW_FILE.tmp" "$NEW_FILE"
}

function map_wiki_links ()
{
    FILE="$1"

    for ML in $DOC_MAPPING
    do
        ML=$(echo $ML | sed 's/:/ /')
        OLD_NAME=$(echo $ML | awk '{print $1}')
        OLD_NAME=$(basename $OLD_NAME)
        NEW_NAME=$(echo $ML | awk '{print $2}' | sed 's/\.md/-wiki/')

        cat "$FILE" | \
            ssed -R 's@\[([^\]]+)\]\([^)]+'$OLD_NAME'\)@[\1]['$NEW_NAME']@' > "$FILE.tmp"
        mv "$FILE.tmp" "$FILE"
    done

}

check_args $@

cd ..

for M in $DOC_MAPPING
do
    M=$(echo $M | sed 's/:/ /')
    OLD_NAME=$(echo $M | awk '{print $1}')
    NEW_NAME=$(echo $M | awk '{print $2}')
    NEW_PATH="$DESTINATION_DIR/$NEW_NAME"

    check_file "$OLD_NAME"
    strip_title "$OLD_NAME" "$NEW_PATH"
    make_full_links "$OLD_NAME" "$NEW_PATH"
    map_wiki_links "$NEW_PATH"
done

