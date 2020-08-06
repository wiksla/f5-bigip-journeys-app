#!/bin/bash
cd $MIGRATE_DIR

if [ "$1" = "--shell" ]; then

  export PS1="\$(journey.py prompt)\W> "
  $SHELL
  exit
fi

journey.py $*
