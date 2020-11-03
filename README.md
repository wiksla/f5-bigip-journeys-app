# BIG-IP Journeys app - BIG-IP migration utility to new F5 platforms and architectures

----
## Contents:
- [Descrpition](#description)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Usage](#usage)
- [Contributions](#contributions)

----
## Description
F5 BIG-IP Journeys app assists with migrating a configuration from BIG-IP versions 11.5.0 or higher to BIG-IP 14.1.x running on the VELOS platform. It allows:
+ flagging source configuration feature parity gaps and fixing them with custom or F5 recommended solutions,
+ automated deployment of the updated configuration to VELOS VM tenant and post deployment validation.

List of supported features:
+ Compatibility level,
+ Double Tagging,
+ Hardware Class of Service,
+ Management dhcp,
+ PEM [2],
+ Service Provider DAG,
+ sPVA [1],
+ Trunk,
+ Virtual Wire,
+ VLAN groups,
+ Wildcard allow-list.

**Journey App does not support** following feature parity gaps, which:

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
1. Mandatory steps before running the Journeys App or manually creating and loading source BIG-IP UCS configuration.

    Before you run the Journeys App, you need to set a device master key password on both Source and Destination Systems.
    There are two ways of doing this:

    1. Copying the Source System master key with f5mku and re-keying master key on the Destination System:

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
    1. Destination VELOS BIG-IP VM tenant deployed and configured on the chassis partition
    1. VLANs, trunks and interfaces configured and assigned to othe VM Tenant (on System Controller level)
    1. All modules from the Source System provisioned on the destination host (with the exception for PEM and CGNAT)

----
## Deployment

### Journeys App as a standalone tool

Available via setuptools as a standalone CLI. 

1. `pip install -r requirements.txt` 
1. `python migrate --help`

### Running Journeys app as a docker container: summary

Usage examples:

Preparing a temporary folder:
1. `docker build -t journeys .`
1. `mkdir /tmp/journeys`
1. `cd /tmp/journeys`
1. `cp <ucs_file> .`

Run commands one by one starting a separate docker container
1. `alias journey ="docker run --rm -v /tmp/journeys:/migrate journeys"`
1. `journey start spdag.ucs`
1. `journey resolve SPDAG`
1. `journey use SPDAG_change_value_to_default`
1. `journey migrate`
1. `journey generate`

Or use interactive container mode:
1. `docker run -it --rm -v /tmp/journeys:/migrate journeys --shell`
1. `journey migrate spdag.ucs`
1. `journey resolve SPDAG`
1. `journey use SPDAG_change_value_to_default`
1. `journey migrate`
1. `journey generate`

----
## Usage

### Tool Environment and Installation
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
    1. Non-Interactive mode
        1. On Linux-based hosts:
             ```
             alias journey="docker run --rm -it -v $(pwd):/migrate f5devcentral/journeys:latest"
             ```
        1. On Windows:
             ```
             doskey journey=docker run --rm -it -v %cd%:/migrate f5devcentral/journeys:latest
             ```

### Source configuration
1. Prepare source UCS file
   1. manually, by saving the UCS on a Source System:
       ```
       tmsh save sys ucs <ucs_name> passphrase <passphrase>
       ```
       and copying it (eg: scp, USB) to the working directory: /tmp/journey on a host system    
   1. automatically, by using Journeys App:
       1. download the ucs file from a live source BIG-IP system:
            ```
            journey download-ucs --host <bigip host> --username <bigip username> --ucs-passphrase <passphrase> --output <ucs file>
            ```
   >IMPORTANT for security reasons:
   >The account used should be a READ-ONLY and should have permission only to generate and fetch the ucs.
   >Generated UCS configuration should be encrypted with a passphrase.**

### Running the tool
   ```
   journey start <ucs file> --ucs-passphrase <passphrase>
   ```
   After the command is run, the tool searches for conflicts in a given source configuration.

   `AS3 support`

   It is also possible to pass AS3 declaration in addition to UCS.
   ```
   journey start <ucs file> --ucs-passphrase <passphrase> --as3-path <as3 declaration>
   ```
   The tool will track changes made by resolving the conflicts and apply them to AS3 declaration.
   
   >WARNING: Vlans, trunks and vlan-groups may uniquely identify virtual servers.
   >In some cases removing them may produce invalid configurations.

   

### Resolving conflicts
   If at least one conflict has been detected, the tool will print the entire list.
   1. One-by-one
      ``` 
      journey resolve <conflict_tag>
      ```
   1. Resolve all conflicts and apply F5 recommended changes to each
      ```
      journey resolve-all
      ```
      After the command is run, the tool will generate git branches with proposed conflict mitigations. 
      Detailed instructions about resolving conflicts are printed by the tool.
   
   1. Example of conflict resolution
        1. Resolve a conflict:
           ```
           journey resolve TRUNK
           ```
           The output should look like:       
           ```
           journey(12 conflicts left): migrate> journey resolve TRUNK
           Workdir: /migrate
           Config path: /migrate/wip/config

           Resolving conflict_info TRUNK

           Resolve issues on objects commented with 'TRUNK' in the following files:
	            bigip_base.conf

           Available conflict mitigations are:
	            F5_Recommended_TRUNK_delete_objects

           To review the mitigation content, run 'journey show <mitigation>'
           Example 'journey show F5_Recommended_TRUNK_delete_objects'

           To review issues found, run 'journey diff'

           To apply proposed changes, please run 'journey use <mitigation>'
           Example 'journey use F5_Recommended_TRUNK_delete_objects'

           Please note, that files can be also edited manually, followed by running 'journey migrate' command.

           To abort resolving current conflict, run 'journey abort'
           ```
        
        1. Preview the issues in the affected files (eg. wip/config/bigip_base.conf).
           Problematic objects are commented with a conflict tag name. 
           ```
           #TRUNK: Depends on an object 'net vlan /Common/vlan_with_trunk' which requires an action
           #TRUNK: Depends on an object 'net vlan /Common/testVirtWire_vlan_4096_2_902' which requires an action
           #TRUNK: Depends on an object 'net vlan /Common/testVirtWire_vlan_4096_1_902' which requires an action
           net route-domain /Common/0 {
             id 0
               vlans {
                  /Common/http-tunnel
                  /Common/socks-tunnel
                  /Common/subscriber
                  /Common/testVirtWire_vlan_4096_1_902
                  /Common/vlan1
                  /Common/vlan_spdag
                  /Common/vlan_qinq
                  /Common/vlan_with_trunk
                  /Common/vlan2
                  /Common/testVirtWire
                  /Common/test_vlan_group
                  /Common/testVirtWire_vlan_4096_2_902
                  /Common/internet
               }
           }
        
            #TRUNK: Type net trunk is not supported on target platform
            net trunk test_trunk {
              interfaces {
                2.0
              }
            }
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
      
        1. Review the mitigation.
           ```
           journey show F5_Recommended_TRUNK_delete_objects
           ```
           
           The output shows all the changes ("-" stands for line removal, "+" stands for line insertion).
           
           ```
           commit 46769f75963de9c7a1d1aac30f4dc74f11e6627a
           Author: root <root@194d95145de1>
           Date:   Thu Oct 22 13:55:46 2020 +0000

              F5_Recommended_TRUNK_delete_objects

           diff --git a/config/bigip_base.conf b/config/bigip_base.conf
           index f3c35ab..fd3de1a 100644
           --- a/config/bigip_base.conf
           +++ b/config/bigip_base.conf
           @@ -215,20 +215,6 @@ net stp /Common/cist {
                     internal-path-cost 2000
                 }
             }
           -    trunks {
           -        test_trunk {
           -            external-path-cost 500
           -            internal-path-cost 500
           -        }
           -        trunk_external {
           -            external-path-cost 2000
           -            internal-path-cost 2000
           -        }
           -        trunk_internal {
           -            external-path-cost 2000
           -            internal-path-cost 2000
           -        }
           -    }
                vlans {
                    /Common/internet
                    /Common/subscriber
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
           
        1. Apply a mitigation or abort resolving conflict step.
           ```
           journey use F5_Recommended_TRUNK_delete_objects   
           ```
           or
           ```
           journey abort
           ```
        1. Resolve another conflict.
           ```
           journey resolve SPDAG
           ```
           The output should look like:
           ```
           journey(11 conflicts left): migrate> journey resolve SPDAG
           Workdir: /migrate
           Config path: /migrate/wip/config

           Resolving conflict_info SPDAG

           Resolve issues on objects commented with 'SPDAG' in the following files:
             	bigip.conf
            	bigip_base.conf

           Available conflict mitigations are:
            	SPDAG_delete_objects
            	F5_Recommended_SPDAG_change_value_to_default

           To review the mitigation content, run 'journey show <mitigation>'
           Example 'journey show F5_Recommended_SPDAG_change_value_to_default'

           To review issues found, run 'journey diff'

           To apply proposed changes, please run 'journey use <mitigation>'
           Example 'journey use F5_Recommended_SPDAG_change_value_to_default'

           Please note, that files can be also edited manually, followed by running 'journey migrate' command.

           To abort resolving current conflict, run 'journey abort'
           ```
        1. Review a mitigation.
           ```
            journey(SPDAG): migrate> journey show F5_Recommended_SPDAG_change_value_to_default
            commit fcff94eff09debc39c3d8604615fbba8111ce60d
            Author: root <root@194d95145de1>
            Date:   Thu Oct 22 14:22:53 2020 +0000

               F5_Recommended_SPDAG_change_value_to_default

            diff --git a/config/bigip_base.conf b/config/bigip_base.conf
            index fd3de1a..765dba5 100644
            --- a/config/bigip_base.conf
            +++ b/config/bigip_base.conf
            @@ -231,11 +231,11 @@ net stp-globals {
                config-name 00-94-A1-11-E8-80
            }
            net vlan /Common/internet {
            -    cmp-hash dst-ip
            +    cmp-hash default
                tag 107
            }
            net vlan /Common/subscriber {
            -    cmp-hash src-ip
            +    cmp-hash default
                tag 1075
            }
            net vlan /Common/testVirtWire_vlan_4096_1_902 {
            @@ -277,7 +277,7 @@ net vlan /Common/vlan_qinq {
                tag 4094
            }
            net vlan /Common/vlan_spdag {
            -    cmp-hash src-ip
            +    cmp-hash default
                description "Test VLAN with SP-DAG"
                interfaces {
                    1.2 { }

            In order to apply the mitigation, run 'journey use F5_Recommended_SPDAG_change_value_to_default' 
           ```
        1. Apply a mitigation.
           ```
           journey use F5_Recommended_SPDAG_change_value_to_default
           ```
        1. Revert the mitigation.
           1. Check the history of applied mitigations / changes.
              ```
              journey history
              ```
              The output should look like:
              ```
              The following changes have been applied successfully:
                    1: F5_Recommended_TRUNK_delete_objects
                    2: F5_Recommended_SPDAG_change_value_to_default

              In order to revert conflict_info resolution, run 'journey revert <step name>'.

              Note that reverting a conflict_info resolution will also revert all subsequent resolutions.
              ```
           1. Select a step you want to revert.
              ```
              journey revert F5_Recommended_SPDAG_change_value_to_default
              ```
        1. Select a conflict to resolve 
           ```
           journey resolve SPVA
           ```
           and apply a desirable mitigation.
           Repeat the step until all conflicts are resolved.
        1. Mitigate a conflict manually.
           1. Select a conflict you want to resolve manually.
              ```
              journey resolve DoubleTagging
              ```
           1. Install your text editor of choice (eg. vim)
              ```
              apk add vim
              ```
           1. Manually edit files with conflicted objects by removing or editing them.
              ```
              vim wip/config/bigip_base.conf
              ```
              Find commented objects and edit them to fulfill the mitigation.
              ```
              #DoubleTagging: Type customer tag is not supported on target platform
              net vlan /Common/vlan_qinq {
                customer-tag 3210
                description "Test VLAN with Customer Tag"
                interfaces {
                    1.1 { }
                }
                sflow {
                    poll-interval-global no
                    sampling-rate-global no
                }
                tag 4094
              }
              ```
         
           1. Apply the mitigation.
              ```
              journey migrate --message "Your mitigation name"
              ```
         
### Generating VELOS-ready output configuration
   1. Generating output ucs configuration
   Once all conflicts are resolved, the following command will generate an output UCS file.
   NOTE: File will have entries fixed for VELOS parity but is still in the source BIG-IP version.
   ```
   journey generate --output <output_ucs_name> --ucs-passphrase <passphrase>
   ```
   `AS3 support`

   If AS3 declaration was passed to start method, the tool will also generate it.
   ```
   journey generate --output <output_ucs_name> --ucs-passphrase <passphrase> --output-as3 <output_as3_name>
   ```
    
### Resources
   Before deploying the UCS, the user may check if the Destination System has enough resources to load the configuration.
   Application leverages the `mprov.pl` internal script, which verifies if all BIG-IP modules residing in  
   the bigip_base.conf file from the Source System UCS can be provisioned on the given Destination System. 
   During the check, the script verifies required CPU, Disk and RAM usage of the used BIG-IP modules.
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
  
### Deployment and Validation
If you're running the Journeys App in an environment where there is a connectivity to Source and Destination BIG-IP systems, you can use the Deployment and Validation feature to have the configuration deployed automatically on the Destination system and run a series of automated tests. 

1. Deploy output configuration to destination system
   ```
   journey deploy --input-ucs <ucs> --ucs-passphrase <ucs_passphrase> --destination-host <ip_or_fqdn> --destination-username <username> --destination-admin-username <admin_user>
   ```
`Backup`

During the deployment process, the tool will automatically create a backup UCS on destination system. The file will be named:

`auto_backup_from_%Y%m%d%H%M%S.ucs`
1. Run diagnostics
After loading the UCS to the Destination System, you can run a diagnose function that collects information relevant to your system condition and compares its state and configuration with the Source BIG-IP System.
   ```
   journey diagnose --source-host <ip_or_fqdn> --destination-host <ip_or_fqdn>
   ```
To skip desired diagnose methods, use option `--exclude-checks <JSON_list_of_checks_to_skip>`.
Please note that some methods just gather data and require user's evaluation. For details check [Diagnose Methods](#diagnose-methods) section.

#### Diagnose Methods
##### MCP status check

Area:| error detection
-----|-----

Checks if values of returned fields are correct. 
This method uses `tmsh show sys mcp-state field-fmt` that can be executed manually. 

##### TMM status

Area:| resource management
-----|-----

Function logs status of TMM. Requires manual evaluation.

##### Prompt state

Area:| error detection
-----|-----

Checks if prompt state is in active mode. 

##### Core dumps detection

Area:| error detection
-----|-----

Checks if diagnostic core dumps were created. 

##### Database Comparison

Area:| config migration
-----|-----

Compares two system DBs getting them from iControl endpoint for sys db. Requires manual evaluation. 

##### Memory footprint Comparison

Area:| information, resource management
-----|-----

Compares information from `tmsh show sys provision` for both systems. Requires manual evaluation.

##### Version Comparison

Area:| information
-----|-----

Compares information from `tmsh show sys version` for both systems. Requires manual evaluation.

##### Local Traffic Manager (LTM) module comparison checks

Area:| config migration, resource management
-----|-----

Check lists of all defined LTM nodes and Virtual Servers configured in the new system. 
If both devices are on-line, it will check conformance of both configuration and resource availability.
Requires manual evaluation.

##### Log Watcher check

Area:| error detection
-----|-----

Log watcher check runs only together with UCS deployment to the Destination Platform using
`journey deploy <attributes...>`. This check looks for "ERR" and "CRIT" phrases (case insensitive).
that appear in log during UCS deployment process. Current scope of log files lookup table:
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

## Contributions

### Bug reporting

Let us know if something went wrong. By reporting issues, you support development of this project and get a chance of having it fixed soon. 
Please use bug template available [here]()

### Feature requests

Ideas for enhancements are welcome [here]()

### Code contribution 

If you wish to contribute, please contact: p.purc@f5.com to get a CLA document. The below section explains why.  

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
