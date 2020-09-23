
# Migration utility for CBIP to Velos platform. 

----

## Contents:
- [Descrpition](../master/README.md#migration-utility-for-cbip-to-velos-platform)
- [Prerequisites](../master/README.md#prerequisites)
- [App deployment](../master/README.md#deployment)
- [Usage](../master/README.md#usage)
   - [Preparation]()
   - [Migrate]()
   - [Deploy]()
   - [Validate]()
- [Contribution](../master/README.md#contributing)

----

## Prerequisites
## Deployment
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
1. `journey.py use SPDAG_change_value_to_default`
1. `journey.py migrate`
1. `journey.py generate`

Or use interactive container mode:
1. `docker run -it --rm -v /tmp/journeys:/migrate journeys --shell`
1. `journey.py migrate spdag.ucs`
1. `journey.py resolve SPDAG`
1. `journey.py use SPDAG_change_value_to_default`
1. `journey.py migrate`
1. `journey.py generate`

## Contributing

### Bug reporting

Let us know if something went wrong. By doing reporting issues, you supports development of this project and gets a chance of having it fixed soon. 
Please use bug template available [here]()

### Feature requests

Ideas for enhancements are welcome [here]()

### Code contribution 

If you wish to contribute please contact with: p.purc@f5.com to get CLA document. The below section explains why.  

#### F5 Networks Contributor License Agreement

Before you start contributing to any project sponsored by F5 Networks, Inc. (F5) on GitHub, you will need to sign a Contributor License Agreement (CLA).

If you are signing as an individual, we recommend that you talk to your employer (if applicable) before signing the CLA since some employment agreements may have restrictions on your contributions to other projects.
Otherwise by submitting a CLA you represent that you are legally entitled to grant the licenses recited therein.

If your employer has rights to intellectual property that you create, such as your contributions, you represent that you have received permission to make contributions on behalf of that employer, that your employer has waived such rights for your contributions, or that your employer has executed a separate CLA with F5.

If you are signing on behalf of a company, you represent that you are legally entitled to grant the license recited therein.
You represent further that each employee of the entity that submits contributions is authorized to submit such contributions on behalf of the entity pursuant to the CLA.

#### Pull requests

You can contribute by opening us a Pull Request. 
To prepare your dev environment run `pip install -r test-requirements.txt` with python 3.8.5 as interpreter in your env. 
Before opening a pull request, make sure to run the following commands, and ensure that they return without errors.
 
```
make format
make lint
make test
```

Please make sure the new code is covered by unit tests.
