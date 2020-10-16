#!/bin/bash
cd $MIGRATE_DIR

if [ "$1" = "--shell" ]; then

  export PS1="\$(journey.py prompt)\W> "
  journey.py
  echo ""
  journey.py first-step
  $SHELL
  exit
fi

if [ "$1" = "runserver" ]; then
  exec manage.py "$@"
fi

journey.py $*
