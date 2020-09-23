
# Migration utility for Classic BIG-IP system to VELOS platform. 

----
## Contents:
- [Descrpition](#description)
- [Prerequisites](#prerequisites)
- [App deployment](#deployment)
- [Usage](#usage)
   - [Example](#example)
   - [Migrate](#migrate)
   - [Deploy](#deploy)
   - [Validate](#validate)
- [Contribution](#contributing)

----
## Description
The tool allows migrating from 11.5.0 to 14.1.2 software versions running on the source system. 
Journey App supports flagging feature parity gaps with exemplary solutions implemented for:

+ Compatibility level
+ Double Tagging
+ Hardware Class of Service
+ Management dhcp
+ Service Provider DAG
+ sPVA [1]
+ Trunk
+ Virtual Wire
+ VLAN groups
+ Wildcard allow-list

**Journey App does not support** following feature parity gaps, which:

+ can cause migration failure:
    + PEM [2]
    + CGNAT

+ reside outside a ucs file to be migrated, eg. in a host ucs (not in a guest ucs):
    + Crypto/Compression Guest Isolation (affects vCMP guests only)
    + Traffic Rate Limiting (affects vCMP guests only)

+ do not cause any failure:

    + Secure Vault
    + sPVA features [3]
    + Wildcard SYN cookie protection [4]


#### Footnotes
[1]. *Device addr-list allow-list feature detection is implemented as a part of sPVA.*

[2]. *Affects only bare metal deployments. PEM migration is blocked on VELOS natively by the BIG-IP.*

[3]. *SPVA features, such as DDoS HW Vectors (Device and VS), Device/VS Block List, Device Vector Bad Actor (Greylist), 
Device Flood vector will be handled by the software instead of hardware support.*

[4]. *Wildcard VS SYN cookie protection will be handled by the software instead of hardware support.*

----
## Prerequisites
1. Steps before running Journey App or manually creating and loading UCS.

    Before you run Journey App, you need to set a device master key password on both Source and Destination Systems.
    There are two ways of doing this:

    1. Copying Source System master key with f5mku and re-keying master key on the Destination System:

       >Important: Whenever possible, use the documented tmsh commands for master and unit key manipulation. 
       >Only use the f5mku command with assistance from F5 Support when no tmsh commands exist to perform 
       > the task you want.
        
       - Obtain the master key from the Source System by entering the following commands:
         ```
         f5mku -K
         ```     
         and copy the output. The command output appears similar to the following example:
         ```
         oruIVCHfmVBnwGaSR/+MAA==
         ```
       - Install the master-key that you copied in the previous step to the Destination System using the 
         following syntax:
         ``` 
         f5mku -r <key_value>
         ```
      
    1.  Setting master-key password before saving the source UCS file
        - Set the device master key password on the Source System by entering the following commands 
          (**remember this password** because you'll need to use the same password on the destination device)
          ``` 
          tmsh modify sys crypto master-key prompt-for-password
          tmsh save sys config
          ```
       
        - Set the master key password on the Destination System by entering the following commands, 
          using the password remembered in the previous step::
          ```
          tmsh modify sys crypto master-key prompt-for-password
          tmsh save sys config
           ```

   For more details, refer to:
      - [Platform-migrate option overview: K82540512](https://support.f5.com/csp/article/K82540512#p1)
      - [Installing UCS files containing encrypted passwords or passphrases: K9420](https://support.f5.com/csp/article/K9420)

1. Destination System:
    1. Destination VELOS VM tenant deployed and configured on the chassis partition
    1. VLANs, trunks and interfaces configured and assigned to othe VM Tenant (on System Controller level)
    1. All modules from the Source System provisioned on the destination host (with the exception for PEM and CGNAT)

----
## Deployment

### Journeys App as a standalone tool

Available via setuptools as a standalone CLI. 

1. `pip install -r requirements.txt` 
1. `python migrate --help`

### Running Journeys app as a docker container: summary

Example usage of tool can look like this:

Preparing a temporary folder:
1. `docker build -t journeys .`
1. `mkdir /tmp/journeys`
1. `cd /tmp/journeys`
1. `cp <ucs_file> .`

Run commands one by one starting a separate docker container (requires git tool)
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

----
## Usage

### Example
1. Install Docker on a host system
    ```
    https://www.docker.com/get-started
    ```
1. Fetch the image from repository (when run as a docker container).
    ```
   docker pull f5devcentral/journeys:latest
    ```
1. Prepare working directory.
   ```
   mkdir /tmp/journey
   cd /tmp/journey
   ```
1. Prepare tool environment.

    1. Interactive (Bash) mode
        1. On Linux-based hosts:
             ```
             docker run --rm -it -v $(pwd):/migrate f5devcentral/journeys:latest --shell
             ```
        1. On Windows:
             ```
             docker run --rm -it -v %cd%:/migrate f5devcentral/journeys:latest --shell 
             ```
    1. Non Interactive mode
        1. On Linux-based hosts:
             ```
             alias journey.py="docker run --rm -v $(pwd):/migrate f5devcentral/journeys:latest"
             ```
        1. On Windows:
             ```
             doskey journey.py=docker run --rm -v %cd%:/migrate f5devcentral/journeys:latest
             ```
1. Prepare source UCS file
   1. manually, by saving the UCS on a Source System:
       ```
       tmsh save sys ucs <ucs_name> passphrase <passphrase>
       ```
       and copying it (eg: scp, USB) to the working directory: /tmp/journey on a host system    
   1. automatically, by using Journey App:
       1. download the ucs file from a live source BIG-IP system:
            ```
            journey.py download-ucs --host <bigip host> --username <bigip username> --password <bigip password> --ucs-passphrase <passphrase> --output <ucs file>
            ```
   >IMPORTANT for security reasons:
   >The account used should be a READ-ONLY and should have permission only to generate and fetch the ucs.
   >Generated UCS should be encrypted with passphrase.**
1. Run the tool.
   ```
   journey.py start <ucs file> --ucs-passphrase <passphrase>
   ```
   After the command is run, the tool searches for conflicts in a given source configuration.
1. Resolving conflicts.
   If at least one conflict has been detected, the tool will print the whole list.
   1. One-by-one
   ``` 
   journey.py resolve <conflict_tag>
   ```
   1. Resolve all conflicts and apply recommended changes
   ```
   journey.py resolve-all
   ```
   After the command is run, the tool will generate git branches with proposed conflict mitigations. 
   Detailed instructions about resolving conflicts are printed by the tool.
1. Generate the output UCS file.

   Once all conflicts are resolved, following command will generate the output UCS file.
   ```
   journey.py generate --output <output_ucs_name> --ucs-passphrase <passphrase>
   ```
1. Load the output UCS to a Destination System
   ```
   load sys ucs <output_ucs_name> passphrase <passphrase> platform-migrate no-license keep-current-management-ip
   ```

### Migrate
### Deploy
### Validate

----
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
