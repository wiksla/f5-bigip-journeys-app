
# Migration utility for CBIP to Velos platform. 

## Usage

### Standalone

Available via setuptools as a standalone CLI. 

1. `pip install -r requirements.txt` 
1. `python migrate --help`

### Docker

Example usage of tool can look like this:

1. `docker build -t journeys .`
1. `alias journey="docker run --rm -v $(pwd):/migrate journeys"`
1. `mkdir /tmp/journeys`
1. `cd /tmp/journeys`
1. `cp <ucs_file> .`
1. `journey migrate spdag.ucs`
1. `cd wip`
1. `journey resolve SPDAG`
1. `git checkout . ; git merge SPDAG_change_value_to_default`
1. `journey migrate`

## Contributing

Use `pip install -r test-requirements.txt` first to install dev requirements.

Before opening a merge request, make sure to run the following commands, and ensure that they return without errors.

```
make format
make lint
(TBD) make test
```
