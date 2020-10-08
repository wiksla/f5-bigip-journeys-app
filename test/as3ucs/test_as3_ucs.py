from .configs import process_as3_test_helper


def test_ltm_virtual():
    source_files = ["bigip-2.conf", "bigip-1.conf", "bigip-0.conf"]
    pattern_files = ["ltm-2.json", "ltm-1.json", "ltm-0.json"]

    for source_file, pattern_file in zip(source_files, pattern_files):
        process_as3_test_helper(source_file, "ltm-2.json", pattern_file)


def test_firewall_policy():
    source_files = ["bigip-2.conf", "bigip-1.conf", "bigip-0.conf"]
    pattern_files = ["policy-2.json", "policy-1.json", "policy-0.json"]

    for source_file, pattern_file in zip(source_files, pattern_files):
        process_as3_test_helper(source_file, "policy-2.json", pattern_file)


def test_firewall_rule_list():
    source_files = ["bigip-2.conf", "bigip-1.conf", "bigip-0.conf"]
    pattern_files = ["rule-list-2.json", "rule-list-1.json", "rule-list-0.json"]

    for source_file, pattern_file in zip(source_files, pattern_files):
        process_as3_test_helper(source_file, "rule-list-2.json", pattern_file)


def test_nat():
    source_files = ["bigip-2.conf", "bigip-1.conf", "bigip-0.conf"]
    pattern_files = ["nat-2.json", "nat-1.json", "nat-0.json"]

    for source_file, pattern_file in zip(source_files, pattern_files):
        process_as3_test_helper(source_file, "nat-2.json", pattern_file)
