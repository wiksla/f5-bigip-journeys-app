#!/bin/bash
cd $MIGRATE_DIR

if [ "$1" = "--shell" ]; then

  export PS1="\$(journey prompt)\W> "
  journey --help
  /bin/bash
  exit
fi

function server_usage()
{
  cat << HEREDOC
  Usage: $(basename $0) runserver [--debug] [--no-ssl]

    Spawn a web gui server for the journeys application.

    Unless --no-ssl is specified, the server will use https with 
    a self-signed certificate on port 443.


  Optional arguments:
    -d, --debug          enable django debug mode
    -h, --help           show this help message and exit
    --no-ssl             run the server without ssl on port 80

HEREDOC
}  

if [ "$1" = "runserver" ]; then
  export DJANGO_SETTINGS_MODULE=journeys.backend.settings
  ssl=true
  for i in "${@:2}"; do
    case $i in 
      --no-ssl)
        ssl=false
      ;;
      -d|--debug)
        export DJANGO_DEBUG=true
      ;;
      -h|--help)
        server_usage
        exit
      ;;
      *)
        echo "Try '$(basename $0) runserver --help'"
        echo ""
        echo "Error: no such option: $i"
      ;;
    esac
  done
  echo "Starting journeys app..."
  if [ "$ssl" = true ]; then
    CERT_PATH="/etc/ssl/server_certs/server.crt"
    KEY_PATH="/etc/ssl/server_certs/server.key"
    mkdir /etc/ssl/server_certs
    openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out ${CERT_PATH} -keyout ${KEY_PATH} \
              -subj "/O=F5 Networks/OU=Journeys/CN=Journeys"
    echo "Certificate:"
    echo $(cat ${CERT_PATH})
    exec gunicorn --certfile=${CERT_PATH} --keyfile=${KEY_PATH} --bind 0.0.0.0:443 journeys.backend.wsgi
  else
    exec gunicorn --bind 0.0.0.0:80 journeys.backend.wsgi
  fi
fi

journey $*
