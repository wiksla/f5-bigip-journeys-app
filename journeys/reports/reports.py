from pathlib import Path
from typing import Dict
from typing import List

import pdfkit

from journeys.reports.html import make_deployment_validations_html
from journeys.reports.html import make_styled_conflicts_html
from journeys.reports.html import make_styled_conflicts_res_html

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"


def generate_conflicts_report(output_path: str, conflicts: List[Dict]):
    """Generate pdf report to output_path from conflicts list

    Parameters:
    output_path (str): path to where the report file should be created
    conflicts (List[Dict]): list of conflicts objects that are equivalent of following JSON:
    [
        {
            "id": "SPDAG",
            "summary": "net vlan /Common/vlan1: Value of field cmp hash is not supported on target platform",
            "affected_objects": {
                "net vlan /Common/vlan1": {
                    "file": "bigip_base.conf",
                    "comment": "Value of field cmp hash is not supported on target platform",
                    "object": [
                      "net vlan /Common/vlan1 {",
                      "    cmp-hash src-ip",
                      "    tag 4094",
                      "}"
                    ]
                }
            }
        }
    ]
    """

    html = make_styled_conflicts_html(
        conflicts,
        styles_file=str(RESOURCE_DIR / "styles_conflicts.css"),
        logo_file=str(RESOURCE_DIR / "logo.png"),
    )

    options = {"allow": "."}
    pdfkit.from_string(input=html, output_path=output_path, options=options)


def generate_changes_report(output_path: str, changes: List[Dict]):
    """Generate pdf report to output_path from changes list

    Parameters:
    output_path (str): path to where the report file should be created
    changes (List[Dict]): list of conflicts objects that are equivalent of following JSON:
    [
        {
            "id": 11,
            "message": "change example",
            "url": "http://localhost:8000/sessions/31/changes/11",
            "diffs": {
                "config/bigip.conf": [
                    {
                        "change_type": "insert",
                        "previous_text": [],
                        "current_text": [
                            "apm report default-report {",
                            "    report-name sessionReports/sessionSummary",
                            "    user /Common/admin",
                            "}"
                        ],
                        "previous_line": 21,
                        "current_line": 21
                    },
                    {
                        "change_type": "replace",
                        "previous_text": [
                            "ltm node /Common/10.171.190.20 {",
                            "    address 10.171.190.20"
                        ],
                        "current_text": [
                            "ltm node /Common/10.171.190.100 {",
                            "    address 10.171.190.100"
                        ],
                        "previous_line": 75,
                        "current_line": 79
                    },
                    {
                        "change_type": "delete",
                        "previous_text": [
                            "ltm pool /Common/pcf-gorouter1-mdc-pc1_9060 {",
                            "    load-balancing-mode least-connections-member",
                            "    members {",
                            "        /Common/10.175.24.22:80 {",
                            "            address 10.175.24.22",
                            "        }",
                            "    }",
                            "    monitor /Common/rubicon-sso-prod-mdc-pcf"
                        ],
                        "current_text": [],
                        "previous_line": 3611,
                        "current_line": 3615
                    }
                ]
            }
        }
    ]
    """

    html = make_styled_conflicts_res_html(
        changes,
        styles_file=str(RESOURCE_DIR / "styles_resolutions.css"),
        logo_file=str(RESOURCE_DIR / "logo.png"),
    )

    options = {"allow": "."}
    pdfkit.from_string(input=html, output_path=output_path, options=options)


def generate_deployment_validations_report(
    output_path: str, validation: Dict[str, Dict]
):
    html = make_deployment_validations_html(
        validation,
        styles_file=str(RESOURCE_DIR / "styles_deployment.css"),
        logo_file=str(RESOURCE_DIR / "logo.png"),
    )

    options = {"allow": "."}
    pdfkit.from_string(input=html, output_path=output_path, options=options)
