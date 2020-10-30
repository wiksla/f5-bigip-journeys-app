"""
Copyright 2020 F5 Networks Inc.

Copyright 2018 NGINX, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file has been modified by F5 Networks Inc. for the purpose of adding support for processing bigip config files.
"""

NONAME = {
    ("auth", "password-policy"),
    ("auth", "remote-role"),
    ("auth", "remote-user"),
    ("auth", "source"),
    ("cli", "admin-partitions"),
    ("cli", "global-settings"),
    ("cli", "preference"),
    ("ltm", "default-node-monitor"),
    ("ltm", "dns", "analytics", "global-settings"),
    ("ltm", "dns", "cache", "global-settings"),
    ("net", "cos global-settings"),
    ("net", "lldp-globals"),
    ("net", "packet-filter-trusted"),
    ("net", "stp-globals"),
    ("sys", "datastor"),
    ("sys", "dns"),
    ("sys", "global-settings"),
    ("sys", "httpd"),
    ("sys", "log-rotate"),
    ("sys", "ntp"),
    ("sys", "outbound-smtp"),
    ("sys", "scriptd"),
    ("sys", "snmp"),
    ("sys", "software", "update"),
    ("sys", "sshd"),
    ("sys", "state-mirroring"),
    ("wom", "endpoint-discovery"),
}
BLOBTYPES = {
    ("cli", "script"),
    ("ltm", "rule"),
    ("gtm", "rule"),
    ("sys", "application", "apl-script"),
    ("sys", "application", "template"),
    ("sys", "icall", "script"),
}
LISTTYPES = {
    "analytics gui-widget": ("drilldown-entities", "drilldown-values", "metrics"),
    "analytics predefined-report": ("values",),
    "apm profile access": ("accept-languages",),
    "cm device": ("active-modules", "optional-modules"),
    "cm trust-domain": ("ca-devices",),
    "ltm policy": ("controls", "requires", "values"),
    "ltm profile client-ssl": ("cert-extension-includes", "options"),
    "ltm profile server-ssl": ("c3d-cert-extension-includes", "options"),
    "ltm profile http-compression": (
        "content-type-include",
        "content-type-exclude",
        "uri-include",
        "uri-exclude",
    ),
    "sys dns": ("name-servers",),
    "sys management-dhcp": ("request-options",),
    "sys ntp": ("servers",),
    "sys snmp": ("agent-addresses", "allowed-addresses"),
}
MODULES = (
    "analytics",
    "apm",
    "asm",
    "auth",
    "cli",
    "gtm",
    "ilx",
    "ltm",
    "net",
    "pem",
    "security",
    "sys",
    "vcmp",
    "wam",
    "wom",
)
