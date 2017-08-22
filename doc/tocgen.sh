#!/bin/bash

function filter-lines()
{
  grep -E "^#{2,4} " "$1" \
    | sed -r -e 's/^## +(.+[^ ]) *$/1. [\1]/' \
             -e 's/^### +(.+[^ ]) *$/    1. [\1]/' \
             -e 's/^#### +(.+[^ ]) *$/        1. [\1]/'
}

function produce-link()
{
  # Next $1 is naked on purpose to get rid of multiple spaces.
  echo ${1,,} | grep -Eo "\[.+\]" | sed -e 's/[()]//g' \
    -e 's/\[/(#/' -e 's/\]/)/' -e 's/ /-/g'
}

function main() {
  local line IFS=$'\n'

  for line in $(filter-lines "$1")
  do
    echo "$line"$(produce-link "$line")
  done
}

if [[ "x" == "x$1" ]]
then
  echo "Usage: $0 file.md"
  exit 1
else
  main "$1"
fi
