
Migration utility:
1. VCMP (Guest) -> Velos (Tenant) 



Available via setuptools as a standalone CLI. 

1. make virtualenv 
2. pip install -e . 
3.
bash_completion: 

In ~/.bashrc


eval "$(_MIGRATE_COMPLETE=source migrate)"



Usage:

migrate --help



Dockerized (in future).

1. docker build -t artifactory.pdsea.f5net.com/cxt-calypso-docker/migration:latest .
2. docker run -it artifactory.pdsea.f5net.com/cxt-calypso-docker/migration:latest