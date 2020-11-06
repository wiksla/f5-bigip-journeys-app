# CHANGELOG

<!--- next entry here -->

## 1.0.2
2020-11-06

### Fixes

- use public image in dockerfile, internal in ci (9a9d2ecc2b9efafbf00aedc5a91780f24e483822)

## 1.0.1
2020-11-05

### Fixes

- avoid validation json dump TypeError (f63792804ef52504b6d9d0df97ab54a60c045c10)
- avoid validation json dump TypeError (d0385cc52e4b01bf0bd83cdb0c6046fb6498d9a0)

## 1.0.0
2020-11-05

### Features

- Add "next step" expeirience to diff, show and download-ucs commands (a4827eae4a25503d4781de0b1c6d16065dfff212)
- Check if input has the .ucs extension (c66b112c76030ea4690b22006233c8f030391e72)
- Print all parameters in "rerun" request (7f91be16f13e71d92484d3d67f52be77b9310700)
- Update handling of Changes (bd07cbe7b9dde4f26018be070307cda711692f4e)
- supported_validators endpoint (11afb3f3f44b58f5173323ff7b4105f0f4e5b8ed)
- add ssl support for the gui (2b7ae0359dacadaa007fc538eb210cb315f72705)
- Deployment and validation changes (5844cca405d8685af6efa9d6cca79c4c82aa4e26)
- Add reports functionality (5a3410d99c710984c3e49bb6d1d89db749c95968)
- Split UCS to applications by virtual servers (4d3e3e8a7ef54d944a2b8580658181489bec528d)
- Add auto-complete for use, show and resolve (a3dd7812725476528bcb1df877d321911f15b48e)

### Fixes

- for handling FileNotFound exception nicely (0dd6c06ca18749689e08debc0f1bdcd29f90eb28)
- ignore pem if no contents (4f5f55299158c8d1dbd3880ebefa2060d2c3bcbb)
- truncate long conflict summaries in cli (9b521faf88cdc1a834a49e984d0bc7c108c20e73)
- add "value" key to json. (164ab234f09743fbad93e8dcbe7ee2da369ee54d)
- enquoting improvements (e2beddd187938dc9103c62248e0a9cb2298197d4)
- unify validators output - `value` contains a dict (adb5e6979a87e199197e9dc11a63e82d27313401)
- add condition to interrupt deployment method (82e00cc64d097f17c7d7153701b05da90cc00d70)
- add vs rule dependency, restore pem ignore (b66c529df5bb5df9007dd43fd9e0ede1900cb7ed)
- add method to cover own pretty resposens from DeepDiff (02a80ff097abbb130846ba803243b33c0ce81713)
- remove redundant info "Diagnostic core dumps found." && fix typo (4c62bc4096b0a8e4236940cb9667a7cc9effde36)
- very quick fix (1d1c638bee74cfa3e341456c9ede374272bfa9a8)
- remove legacy func obtain hw resources (5691f28c92ff01a47eebf87a3474a8b20764d916)
- Fix resolutions report (2d7398290ddc1c21929045ce03158a2e505ba61d)
- diagnose - no password prompt without --destination-host (778047f0ddf5e3be04c7353767011e7847e13427)
- README update - cmd resources (905b821f063a8e86f1f915f6cb02c601a9874b7a)
- Log watcher improvements (8fef2743ad72498cc9fe101c5fbf86f9139fd1f7)
- restructure the readme, minor cli reword (52ba450f925a48f1a6bc3e8b1a8f56960d614d1d)
- add links to bug report and feature request. (015274ddb8e1c0dccae9307e038596e7b38f075e)
- Mcp status improvements (ec34982a2102effda07515b4d8496b2c90571999)

## 0.2.0
2020-10-13

### Features

- Add Django based backend for journeys application (4e4469b9344e839ea15702c57b49bffec90623d3)
- Unify source input (b84bc82026a525172c9134d4399cf82c80a924bf)

### Fixes

- recognize virtual-wire-specific vlans by tag (ed6a914f9f6e8911935546b8ba27da52acc6dc2f)
- remove required tags from passwords (a461340c68b6ed5e51415a503cc3f27ce1ca7b2a)
- add missing Log Watcher to deploy method (11666f3f9d385a24ab97ab596848bc30f044f848)
- add error handler to diagnose method (43977ea127ddc632583b7579ec99eedd242f8810)
- gather module exceptions in one file (d1c35bf23bd3ac610a8f70d3db723ab7641c079f)