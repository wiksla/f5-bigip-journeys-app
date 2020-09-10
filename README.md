
# Migration utility for CBIP to Velos platform. 

## Usage

### Standalone

Available via setuptools as a standalone CLI. 

1. `pip install -r requirements.txt` 
1. `python migrate --help`

### Docker

Example usage of tool can look like this:

Preparing a temporary folder:
1. `docker build -t journeys .`
1. `mkdir /tmp/journeys`
1. `cd /tmp/journeys`
1. `cp <ucs_file> .`

Run command one by one starting a separate docker container (requires git tool)
1. `alias journey.py="docker run --rm -v /tmp/journeys:/migrate journeys"`
1. `journey.py start spdag.ucs`
1. `journey.py resolve SPDAG`
1. `journey.py cleanup ; journey.py use SPDAG_change_value_to_default`
1. `journey.py migrate`
1. `journey.py generate`

Or use interactive container mode:
1. `docker run -it --rm -v /tmp/journeys:/migrate journeys --shell`
1. `journey.py migrate spdag.ucs`
1. `journey.py resolve SPDAG`
1. `journey.py cleanup ; journey.py use SPDAG_change_value_to_default`
1. `journey.py migrate`
1. `journey.py generate`

## Contributing

Use `pip install -r test-requirements.txt` first to install dev requirements.

Before opening a merge request, make sure to run the following commands, and ensure that they return without errors.

```
make format
make lint
make test
```
