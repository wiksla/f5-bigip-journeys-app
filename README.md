# BIG-IP Journeys app - BIG-IP migration utility to new F5 platforms and architectures

----
## Contents:
- [Description](#description)
- [Prerequisites](#big-ip-prerequisites)
- [Requirements](#requirements)
- [Usage](#usage)
- [Contributing](#contributing)

----
## Description
F5 BIG-IP Journeys app assists with migrating a configuration from any BIG-IP between versions 11.5.0 and 14.1.3 onto the VELOS platform, which as of now runs on BIG-IP version 14.1.3. It allows:
+ flagging source configuration feature parity gaps and fixing them with custom or F5 recommended solutions,
+ automated deployment of the updated configuration to VELOS VM tenant and post-deployment validation.

List of possibly unsupported configuration features for the VELOS platform that the journeys app is able to catch:
+ **CGNAT** - VELOS platform currently does not support [Carrier Grade NAT](https://techdocs.f5.com/en-us/bigip-15-0-0/big-ip-cgnat-implementations.html) configuration.
+ **ClassOfService** - the CoS feature is not supported on VELOS.
+ **CompatibilityLevel** - determines the level of platform hardware capability for for device DoS/DDoS prevention. VELOS currently supports only level 0 and 1 (the latter if software DoS processing mode is enabled). Details on the feature can be found [here](https://techdocs.f5.com/en-us/bigip-15-1-0/big-ip-system-dos-protection-and-protocol-firewall-implementations/detecting-and-preventing-system-dos-and-ddos-attacks.html).
+ **DoubleTagging** - indicates support for the IEEE 802.1QinQ standard, informally known as Double Tagging or Q-in-Q, which VELOS does not have as of now. More info on the feature can be found [here](https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/vlans-vlan-groups-and-vxlan.html).
+ **MGMT-DHCP** - on VELOS mgmt-dhcp configuration is handled mostly on chassis-level.
+ **PEM** - while keeping the PEM configuration in the conf files wouldn't cause load errors per se (it will be discarded when loading the UCS), as of now PEM is not functionally supported by VELOS. The tool removes the PEM parts from the configuration altogether to avoid confusion.
+ **SPDAG** - [source/destination DAG](https://techdocs.f5.com/en-us/bigip-15-1-0/big-ip-service-provider-generic-message-administration/generic-message-example/generic-message-example/about-dag-modes-for-bigip-scalability/sourcedestination-dag-sp-dag.html) is not supported on VELOS.
+ **sPVA** - some of the security Packet Velocity Acceleration (PVA) features do not have hardware support on VELOS - we need to either remove them, or ensure that they use software mode.
+ **TRUNK** - on VELOS Trunks cannot be defined on BIG-IP level.
+ **VirtualWire** - the [virtual-wire feature](https://techdocs.f5.com/kb/en-us/products/big-ip_ltm/manuals/product/big-ip-system-configuring-for-layer-2-transparency-14-0-0/01.html) is not supported on VELOS systems.
+ **VlanGroup** - on VELOS [vlan-groups](https://techdocs.f5.com/en-us/bigip-14-1-0/big-ip-tmos-routing-administration-14-1-0/vlans-vlan-groups-and-vxlan.html) cannot be defined on BIG-IP level.
+ **VLANMACassignment** - solves an issue with mac assignment set to `vmw-compat` that can happen when migration from a virtual edition BIG-IP. In the future this will be moved into a separate fix-up module.
+ **WildcardWhitelist** - a part of sPVA - extended-entries field in network-whitelist objects is not supported.

**Journey App does not support** following feature parity gaps, which:

+ Reside outside a UCS file to be migrated, eg. in a host UCS (not in a guest UCS):
    + Crypto/Compression Guest Isolation - Dedicated/Shared SSL-mode for guests is not supported on VELOS. [Feature details.](https://support.f5.com/csp/article/K22363295)
    + Traffic Rate Limiting (affects vCMP guests only) - assigning a traffic profile for vcmp guests is currently not supported on a VELOS tenant.

+ Do not cause any config load failures:

    + [Secure Vault](https://support.f5.com/csp/article/K73034260) - keys will be instead stored on the tenant file system. 
    + Several sPVA features which do not support hardware processing, where software support will occur instead (DDoS HW Vectors (Device and VS), Device/VS Block List, Device Vector Bad Actor (Greylist))
    + Wildcard SYN cookie protection - as above, software processing will replace hardware one.

----
## BIG-IP Prerequisites

Mandatory steps before running the Journeys App.

1. **Master key transfer** - to allow handling encypted objects, before you run the Journeys App, you need to set a device master key password on both Source and Destination Systems. There are two ways to do this:

    1. Copy the Source System master key with f5mku and re-key master key on the Destination System:

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
      
    1.  Set master-key password before saving the source UCS file
        - Set the device master key password on the Source System by entering the following commands 
          (**remember this password** because you'll need to use the same password on the destination device)
          ``` 
          tmsh modify sys crypto master-key prompt-for-password
          tmsh save sys config
          ```
       
        - Set the master key password on the Destination System by entering the following commands, using the password remembered in the previous step::
          ```
          tmsh modify sys crypto master-key prompt-for-password
          tmsh save sys config
           ```

   For more details, refer to:
      - [Platform-migrate option overview: K82540512](https://support.f5.com/csp/article/K82540512#p1)
      - [Installing UCS files containing encrypted passwords or passphrases: K9420](https://support.f5.com/csp/article/K9420)

1. **SSH public keys migration**
   * SSH public keys for passwordless authentication may stop work after UCS migration, since the UCS file may not contain SSH public keys for users.
   * If the version is affected by the problem then:
      - all key files have to be migrated manually from the Source System to the Destination System
      - /etc/ssh directory has to be added to the UCS backup configuration of the Source System
   * For more details on how to manually migrate SSH keys and verify if your version is affected by the problem, please read:
      - K22327083: UCS backup files do not include the /etc/ssh/ directory
      https://support.f5.com/csp/article/K22327083
      - K17318: Public key SSH authentication may fail after installing a UCS
      https://support.f5.com/csp/article/K17318
      - K13454: Configuring SSH public key authentication on BIG-IP systems (11.x - 15.x)
      https://support.f5.com/csp/article/K13454

1. **Destination System preparation**
   1. Destination VELOS BIG-IP VM tenant should be deployed and configured on the chassis partition
   1. VLANs, trunks and interfaces should already be configured and assigned to other VM Tenant (on System Controller level)
   1. All modules from the Source System should be provisioned on the destination host (with the exception for PEM and CGNAT, which are not yet supported on VELOS)

----
## Requirements
* [Docker](https://docs.docker.com/get-docker/)

## Usage

### Preparing the host
First, we want to prepare the directories and files on which the journeys app is meant to operate. You can use any directory in place of `/tmp/journeys`.

1. `mkdir /tmp/journeys`
1. `cd /tmp/journeys`
1. `cp <ucs_file> .`

### Running the application

There are two options to run the container:
1. By spawning a container for each command (aliasing it here for simplicity)
* Linux: 
```
alias journey="docker run --rm -it -v /tmp/journeys:/migrate f5devcentral/journeys:latest
```
* Windows: 
```
doskey journey=docker run --rm -it -v /tmp/journeys:/migrate f5devcentral/journeys:latest
```
2. By dropping into an interactive bash shell inside the container
```
docker run -it --rm -v /tmp/journeys:/migrate f5devcentral/journeys:latest --shell
```

> Note that in this example we mount the previously created `/tmp/journeys` directory onto `/migrate` inside the container, which is the working directory there.

Now we can start the migration process. Use `journey --help` to get you started.

### Usage details

Outputs from subsequent commands (starting at `journey --help`) will guide you through the commands you need to run to perform the migration. This section will explain the whole process.

#### Retrieving the source configuration
This can be done either manually, or with the help of an utility `journey download-ucs` command.
   1. Manual 
      - Run the following command on your source BIG-IP:
       ```
       tmsh save sys ucs <ucs_name> passphrase <passphrase>
       ```
      - Transfer the resulting UCS file from `/var/local/ucs/` onto your journey host, to your working directory.  
   1. Via the journeys app:
      ```
      journey download-ucs --host <bigip host> --username <bigip username> --ucs-passphrase <passphrase> --output <ucs file>
      ```
   >IMPORTANT: For security reasons, 
   >the account used here should be a READ-ONLY and should only have the permission to generate and fetch the UCS.
   >Generated UCS configuration should be encrypted with a passphrase.

#### Starting the migration
   ```
   journey start <ucs file> --ucs-passphrase <passphrase>
   ```
   After the command is run, the tool extracts the UCS file, parses the configuration and searches it for any issues inside and returns information about them.

##### AS3 support

   It is also possible to pass an AS3 declaration in addition to the UCS.
   ```
   journey start <ucs file> --ucs-passphrase <passphrase> --as3-path <as3 declaration>
   ```
   The tool will track any changes made to the configuration by resolving the issues and mirror them in the AS3 declaration.
   
   >WARNING: Vlans, trunks and vlan-groups may uniquely identify virtual servers.
   >In some resolutions, the tool might remove one of these identifiers,  which might result in having several non-unique virtual servers, causing configuration load errors.


#### Resolving issues
   The issue tag to use in with the resolve command can be taken from the output of the previous command.
   1. **Resolve one-by-one**
      ``` 
      journey resolve <issue_tag>
      ```
      <details>
      <summary>Details of further steps in a one-by-one resolution</summary>

      1. **Check the resolve output** - Output of the command above should look like this:
         
         ```
         journey(12 issues left): migrate> journey resolve TRUNK
         Workdir: /migrate
         Config path: /migrate/wip/config

         Resolving issue TRUNK

         Resolve issues on objects commented with 'TRUNK' in the following files:
	          bigip_base.conf

         Available issue mitigations are:
	          F5_Recommended_TRUNK_delete_objects
         ```
         This shows you all the important info - where to look for the config files and which files are impacted by the current issue.

         A list of mitigations proposed by the journeys app is listed at the end - one of them will be marked as the one recommended by F5.
        
      1. **View the issues** - You can preview any issues in the affected files listed above with any text viewer (like vi). Any problematic objects will be prepended with a comment containing an issue tag to make them searchable. 
         ```
         #TRUNK: Type net trunk is not supported on target platform
         net trunk trunk_external {
            description "Test trunk for virtual wire"
            interfaces {
               1.3
               1.4
            }
            lacp enabled
         }
         ```
      
      1. **Review a mitigation proposal** - the `journey show` command shows a standard file diff between the original config file, and a would-be file after applying the selected mitigation.
         ```
         journey show F5_Recommended_TRUNK_delete_objects
         ```
         
         The output shows all the changes ("-" stands for line removal, +" stands for line insertion).
         
         ```
         commit 46769f75963de9c7a1d1aac30f4dc74f11e6627a
         Author: root <root@194d95145de1>
         Date:   Thu Oct 22 13:55:46 2020 +0000

            F5_Recommended_TRUNK_delete_objects

         diff --git a/config/bigip_base.conf b/config/bigip_base.conf
         index f3c35ab..fd3de1a 100644
         --- a/config/bigip_base.conf
         +++ b/config/bigip_base.conf
         @@ -244,27 +230,6 @@ net stp /Common/cist {
          net stp-globals {
              config-name 00-94-A1-11-E8-80
          }
         -net trunk test_trunk {
         -    interfaces {
         -        2.0
         -    }
         -}  
         ```  
           
      1. **Choose a resolution** - you can either apply a selected mitigation, do a manual edit, or abort resolving the issue and return to the previous step.
         1. **Select a proposed mitigation**
            ```
            journey use F5_Recommended_TRUNK_delete_objects   
            ```
         1. **Abort the current resolution**
            ```
            journey abort
            ```
         1. **Perform manual changes** - edit the configuration files inside your working directory as desired (e.g. `/tmp/journeys/wip/config/bigip_base.conf`; hint: use the issue tag to find the problematic objects). After this, run the following command
            ```
            journey migrate --message <message that will be added to change history>
            ```
            The tool should verify whether the issue no longer appears after your changes.
         
      1. **Revert a change** - optionally, you can go back and redo your resolutions.

         First, list the change history
         ```
         journey history
         ```
         The output should look like:
         ```
         The following changes have been applied successfully:
               1: F5_Recommended_TRUNK_delete_objects
               2: F5_Recommended_SPDAG_change_value_to_default
         ```
         
         Now you can pick a change which you want to revert (along with any subsequent changes).
         ```
         journey revert F5_Recommended_SPDAG_change_value_to_default
         ```
      1. **Repeat until no more issues appear** - from the `journey resolve` step.
      </details>
   1. **Resolve all issues automatically** - apply all of the F5 recommended changes to your configuration files.
      ```
      journey resolve-all
      ```
      After the command is run, the tool will go through all of the issues and pick the F5 recommended resolutions, applying them sequentially to the configuration files. Details about the applied changes can be retrieved by generating one of the available reports.
   
         
#### Generating VELOS-ready output configuration file
   Once all issues are resolved, the following command will generate an output UCS file.
   > NOTE: While the resulting file will have entries fixed for VELOS feature parity, UCS version will still be the same as the source BIG-IP one.
   ```
   journey generate --output <output_ucs_name> --ucs-passphrase <passphrase>
   ```
##### AS3 support

   If an AS3 declaration was passed to start method, you can also rename the output as3 json file.
   ```
   journey generate --output <output_ucs_name> --ucs-passphrase <passphrase> --output-as3 <output_as3_name>
   ```
    
#### Resources
   Before deploying the UCS, the user may check if the Destination System has enough resources to load the configuration.
   Application leverages the `mprov.pl` internal script, which verifies if all BIG-IP modules residing in the bigip_base.conf file from the Source System UCS can be provisioned on the given Destination System. During the check, the script verifies required CPU, Disk and RAM usage of the used BIG-IP modules.
   
   If you are running the Journeys App in an environment with connectivity to the Destination System, 
   then please provide the '--host' option. If not, the application can generate for you a `mprov.cfg` file
   with instructions on how to execute the resource verification manually.
   
   * With connectivity:
   ```
   journey resources --host=10.144.19.99
   ```
   * Without connectivity:
   ```
   journey resources
   ```
  
#### Deployment and Validation
If you're running the Journeys App in an environment where the journeys host has connectivity to Source and Destination BIG-IP systems, you can use the Deployment and Validation features to have the configuration deployed automatically on the Destination BIG-IP, as well as run a series of automated tests. 

1. Deploy output UCS to the destination system
   ```
   journey deploy --input-ucs <ucs> --ucs-passphrase <ucs_passphrase> --destination-host <ip_or_fqdn> --destination-username <username> --destination-admin-username <admin_user>
   ```
##### Backup

During the deployment process, the tool will automatically create a backup UCS on destination system. The file will be named `auto_backup_from_%Y%m%d%H%M%S.ucs`

#### Diagnostics
After loading the UCS to the Destination System, you can run a diagnose function that collects information relevant to your system condition and compares its state and configuration with the Source BIG-IP System.
   ```
   journey diagnose --source-host <ip_or_fqdn> --destination-host <ip_or_fqdn>
   ```
To skip desired diagnose methods, use option `--exclude-checks <JSON_list_of_checks_to_skip>`.
Please note that some methods just gather data and require user's evaluation.

<details>
<summary>Diagnose methods</summary>

* ### MCP status check

   Area:| error detection
   -----|-----

   Checks if values of returned fields are correct. 
   This method uses `tmsh show sys mcp-state field-fmt` that can be executed manually. 

* ### TMM status

   Area:| resource management
   -----|-----

   Function logs status of TMM. Requires manual evaluation.

* ### Prompt state

   Area:| error detection
   -----|-----

   Checks if prompt state is in active mode. 

* ### Core dumps detection

   Area:| error detection
   -----|-----

   Checks if diagnostic core dumps were created. 

* ### Database Comparison

   Area:| config migration
   -----|-----

   Compares two system DBs getting them from iControl endpoint for sys db. Requires manual evaluation. 

* ### Memory footprint Comparison

   Area:| information, resource management
   -----|-----

   Compares information from `tmsh show sys provision` for both systems. Requires manual evaluation.

* ### Version Comparison

   Area:| information
   -----|-----

   Compares information from `tmsh show sys version` for both systems. Requires manual evaluation.

* ### Local Traffic Manager (LTM) module comparison checks

   Area:| config migration, resource management
   -----|-----

   Check lists of all defined LTM nodes and Virtual Servers configured in the new system. 
   If both devices are on-line, it will check conformance of both configuration and resource availability.
   Requires manual evaluation.

* ### Log Watcher check

   Area:| error detection
   -----|-----

   Log watcher check runs only together with UCS deployment to the Destination Platform using
   `journey deploy <attributes...>`. This check looks for "ERR" and "CRIT" phrases (case insensitive) that might appear in logs during UCS deployment. Current scope of log file lookup:
   - /var/log/ltm"
   - /var/log/apm"
   - /var/log/gtm"
   - /var/log/tmm"
   - /var/log/liveinstall.log
   - /var/log/asm"
   - /var/log/ts/bd.log
   - /var/log/ts/asm_config_server.log
   - /var/log/ts/pabnagd.log
   - /var/log/ts/db_upgrade.log
   - /var/log/daemon.log
   - /var/log/kern.log
   - /var/log/messages

   If you see log watcher output includes only some of these files, it means rest of them does not appear on your system (they may be not provisioned). 
   Sample output:
   ```json
   Log watcher output:
   {
      "/var/log/ltm": [],
   }
   ```
   Empty list as a value means no lines containing "ERR" and "CRIT" phrases were found, there still may be any information about potential problems in logs. 
   Therefore this check requires manual evaluation. 
</details>

## Contributing

### Bug reporting

Let us know if something went wrong. By reporting issues, you support development of this project and get a chance of having it fixed soon. 
Please use bug template available [here](https://github.com/f5devcentral/f5-bigip-journeys-app/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D)

### Feature requests

Ideas for enhancements are welcome [here](https://github.com/f5devcentral/f5-bigip-journeys-app/issues/new?assignees=&labels=&template=feature_request.md&title=%5BFEAT%5D)

### Code contribution 

If you wish to contribute, please contact: p.purc@f5.com to get a CLA document. The below section explains why.  

#### F5 Networks Contributor License Agreement

Before you start contributing to any project sponsored by F5 Networks, Inc. (F5) on GitHub, you will need to sign a Contributor License Agreement (CLA).

If you are signing as an individual, we recommend that you talk to your employer (if applicable) before signing the CLA since some employment agreements may have restrictions on your contributions to other projects.
Otherwise, by submitting a CLA you represent that you are legally entitled to grant the licenses recited therein.

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
