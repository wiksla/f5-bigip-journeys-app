NONAME = {
    "auth": [["password-policy"], ["remote-role"], ["remote-user"], ["source"]],
    "cli": [["admin-partitions"], ["global-settings"], ["preference"]],
    "ltm": [
        ["default-node-monitor"],
        ["dns", "analytics", "global-settings"],
        ["dns", "cache", "global-settings"],
    ],
    "net": [
        ["cos global-settings"],
        ["lldp-globals"],
        ["packet-filter-trusted"],
        ["stp-globals"],
    ],
    "sys": [
        ["datastor"],
        ["dns"],
        ["global-settings"],
        ["httpd"],
        ["log-rotate"],
        ["ntp"],
        ["outbound-smtp"],
        ["scriptd"],
        ["snmp"],
        ["software", "update"],
        ["sshd"],
        ["state-mirroring"],
    ],
    "wom": [["endpoint-discovery"]],
}
BLOBTYPES = {
    "cli": [["script"]],
    "ltm": [["rule"]],
    "gtm": [["rule"]],
    "sys": [
        ["application", "apl-script"],
        ["application", "template"],
        ["icall", "script"],
    ],
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