#!/bin/bash
cd $MIGRATE_DIR

if [ "$1" = "--shell" ]; then

  export PS1="\$(journey prompt)\W> "
  journey
  echo ""
  journey first-step
  /bin/bash
  exit
fi

if [ "$1" = "runserver" ]; then
  exec manage.py "$@"
fi

journey $*
