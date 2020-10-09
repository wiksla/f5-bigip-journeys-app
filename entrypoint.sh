#!/bin/bash
cd $MIGRATE_DIR

if [ "$1" = "--shell" ]; then

  export PS1="\$(journey.py prompt)\W> "
  $SHELL
  exit
fi

if [ "$1" = "runserver" ]; then
  exec manage.py "$@"
fi

journey.py $*
