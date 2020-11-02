import json

from yattag import Doc
from yattag import indent


# html generators
def make_styled_conflicts_html(conflicts, styles_file, logo_file):
    # TODO: error handler (conflicts)
    doc, tag, text = Doc().tagtext()
    with tag("html"):

        # stylesheet
        with tag("head"):
            doc.stag("link", rel="stylesheet", href=styles_file)

        # conflicts report
        with tag("body"):

            # report title row
            with tag("div", klass="report-title-row"):
                with tag("div", klass="logo-box"):
                    doc.stag("img", src=logo_file, alt="F5 Logo", klass="logo")

                with tag("div", klass="report-title"):
                    text("Journeys")

            # conflicts section
            with tag("div", klass="conflicts"):
                for conflict in conflicts:

                    # conflict item
                    with tag("div", klass="conflict-item"):

                        # conflict summury row
                        with tag("div", klass="conflict-item-summary"):
                            text(conflict["id"])

                        # affected objects section
                        is_even = False
                        affected_obj_item_row_klass = ""

                        for affected_obj_id, affected_obj in conflict[
                            "affected_objects"
                        ].items():
                            # set affected object item item css class
                            if is_even:
                                affected_obj_item_row_klass = "affected-obj-item-row"
                            else:
                                affected_obj_item_row_klass = (
                                    "affected-obj-item-row even"
                                )
                            is_even = not is_even

                            # set affected object item html
                            with tag("div", klass=affected_obj_item_row_klass):

                                # labels column
                                with tag("div", klass="affected-obj-item-labels-col"):
                                    # file name label cell
                                    with tag(
                                        "div",
                                        klass="affected-obj-item-label-cell horizontal-divider",
                                    ):
                                        text("File Name: ")

                                    # comment label cell
                                    with tag(
                                        "div",
                                        klass="affected-obj-item-label-cell horizontal-divider",
                                    ):
                                        text("Comment: ")

                                    # affected object label cell
                                    with tag(
                                        "div", klass="affected-obj-item-label-cell"
                                    ):
                                        text("Object: ")

                                # data column
                                with tag("div", klass="affected-obj-item-data-col"):
                                    # file name data cell
                                    with tag(
                                        "div",
                                        klass="affected-obj-item-data-cell horizontal-divider",
                                    ):
                                        with tag("div", klass="affected-obj-item-file"):
                                            text(affected_obj["file"])

                                    # comment data cell
                                    with tag(
                                        "div",
                                        klass="affected-obj-item-data-cell horizontal-divider",
                                    ):
                                        with tag(
                                            "div", klass="affected-obj-item-comment"
                                        ):
                                            text(affected_obj["comment"])

                                    # object data cell
                                    with tag(
                                        "div", klass="affected-obj-item-data-cell"
                                    ):
                                        with tag(
                                            "div", klass="affected-obj-item-object"
                                        ):
                                            for item in affected_obj["object"]:
                                                with tag("div", klass="obj-list-item"):
                                                    text(item)

    html = indent(doc.getvalue())
    return html


# css generators
def get_dif_class(diff_type):
    klass = ""
    if diff_type == "delete":
        klass = "removed"
    elif diff_type == "insert":
        klass = "added"
    elif diff_type == "replace":
        klass = "replaced"
    return klass


# aggregators
def normalize_add_remove_diff_item(raw_diff_item):
    # TODO: error handler (raw_diff_item arg)
    change_type = raw_diff_item["change_type"]
    change_type_label = ""
    line_num = ""
    text = ""
    klass = ""

    # insert diff
    if change_type == "insert":
        line_num = raw_diff_item["current_line"]
        text = raw_diff_item["current_text"]
        klass = "added"
        change_type_label = "Added"

    # delete diff
    elif change_type == "delete":
        line_num = raw_diff_item["previous_line"]
        text = raw_diff_item["previous_text"]
        klass = "removed"
        change_type_label = "Deleted"

    norm_diff_item = {
        "change_type": change_type,
        "change_type_label": change_type_label,
        "line_num": line_num,
        "text": text,
        "klass": klass,
    }

    return norm_diff_item


def normalize_replace_diff_item(raw_diff_item):
    # TODO: error handler (raw_diff_item arg)
    change_type = "replace"
    change_type_label = "Modified"
    prev_line = {
        "line_num": raw_diff_item["previous_line"],
        "diff_text": raw_diff_item["previous_text"],
    }
    curr_line = {
        "line_num": raw_diff_item["current_line"],
        "diff_text": raw_diff_item["current_text"],
    }
    klass = "replaced"

    norm_diff_item = {
        "change_type": change_type,
        "change_type_label": change_type_label,
        "klass": klass,
        "prev_line": prev_line,
        "curr_line": curr_line,
    }

    return norm_diff_item


# html generators
def make_styled_conflicts_res_html(data, styles_file, logo_file):
    # TODO: error handler (data)
    doc, tag, text = Doc().tagtext()
    with tag("html"):

        # stylesheet
        with tag("head"):
            doc.stag("link", rel="stylesheet", href=styles_file)

        # conflict resolution report
        with tag("body"):

            # report title row
            with tag("div", klass="report-title-row"):
                with tag("div", klass="logo-box"):
                    doc.stag("img", src=logo_file, alt="F5", klass="logo")

                with tag("div"):
                    text("Journeys")

            # conflicts resolution section
            with tag("div", klass="conf-res-list"):
                for resolution in data:

                    # resolution item
                    with tag("div", klass="res-item"):

                        # resolution message row
                        with tag("div", klass="res-item-msg"):
                            text(resolution["message"])

                        # resolution files section
                        with tag("div", klass="files-section"):

                            # files section header row
                            with tag("div", klass="files-section-header-row"):

                                # file name header cell
                                with tag(
                                    "div",
                                    klass="files-section-header-cell file-name-header",
                                ):
                                    with tag("div", klass="files-section-header-text"):
                                        text("File Name")

                                # vertical divider
                                with tag("div", klass="vertical-divider"):
                                    text("")

                                # change type header cell
                                with tag(
                                    "div",
                                    klass="files-section-header-cell change-type-name-header",
                                ):
                                    with tag("div", klass="files-section-header-text"):
                                        text("Change Type")

                                # vertical divider
                                with tag("div", klass="vertical-divider"):
                                    text("")

                                # differences header cell
                                with tag("div", klass="files-section-header-cell"):
                                    with tag("div", klass="files-section-header-text"):
                                        text("Differences")

                            # horizontal divider
                            with tag("div", klass="horizontal-divider"):
                                text("")

                            # files section content row
                            with tag("div", klass="files-section-content-row"):

                                # diff row css class handler
                                is_even = False
                                is_even_klass = ""

                                for file_name in resolution["diffs"]:

                                    # toggle diff row is_even css class
                                    if is_even:
                                        is_even_klass = "even"
                                    else:
                                        is_even_klass = ""
                                    is_even = not is_even

                                    # file item row
                                    with tag(
                                        "div", klass="file-item-row " + is_even_klass
                                    ):

                                        # file name column
                                        with tag("div", klass="file-name-col"):

                                            # file name cell
                                            with tag("div", klass="file-name-cell"):
                                                with tag("div", klass="file-name-text"):
                                                    text(file_name)

                                        # vertical divider
                                        with tag("div", klass="vertical-divider"):
                                            text("")

                                        # file differences column
                                        with tag("div", klass="file-diffs-col"):

                                            # diff row
                                            for diff_item in resolution["diffs"][
                                                file_name
                                            ]:

                                                # add / remove diff type
                                                if (
                                                    diff_item["change_type"] == "insert"
                                                    or diff_item["change_type"]
                                                    == "delete"
                                                ):
                                                    norm_dif_item = normalize_add_remove_diff_item(
                                                        diff_item
                                                    )
                                                    with tag(
                                                        "div",
                                                        klass="diff-item-row "
                                                        + " "
                                                        + norm_dif_item["klass"],
                                                    ):

                                                        # diff type column
                                                        with tag(
                                                            "div",
                                                            klass="diff-item-type-col",
                                                        ):
                                                            with tag(
                                                                "div",
                                                                klass="diff-item-type-cell",
                                                            ):
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-type-text",
                                                                ):
                                                                    text(
                                                                        norm_dif_item[
                                                                            "change_type_label"
                                                                        ]
                                                                    )

                                                        # vertical divider
                                                        with tag(
                                                            "div",
                                                            klass="vertical-divider",
                                                        ):
                                                            text("")

                                                        # diff details column
                                                        with tag(
                                                            "div",
                                                            klass="diff-item-details-col",
                                                        ):
                                                            # diff line number cell
                                                            with tag(
                                                                "div",
                                                                klass="diff-item-line-num-cell",
                                                            ):
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-line-num-text",
                                                                ):
                                                                    text(
                                                                        norm_dif_item[
                                                                            "line_num"
                                                                        ]
                                                                    )

                                                            # vertical divider
                                                            with tag(
                                                                "div",
                                                                klass="vertical-divider",
                                                            ):
                                                                text("")

                                                            # diff text cell
                                                            with tag(
                                                                "div",
                                                                klass="diff-item-text-cell",
                                                            ):
                                                                # diff text lines
                                                                for (
                                                                    diff_text_line
                                                                ) in norm_dif_item[
                                                                    "text"
                                                                ]:
                                                                    with tag(
                                                                        "div",
                                                                        klass="diff-text-line-row",
                                                                    ):
                                                                        with tag(
                                                                            "div",
                                                                            klass="diff-text-line",
                                                                        ):
                                                                            text(
                                                                                diff_text_line
                                                                            )

                                                elif (
                                                    diff_item["change_type"]
                                                    == "replace"
                                                ):
                                                    norm_dif_item = normalize_replace_diff_item(
                                                        diff_item
                                                    )
                                                    with tag(
                                                        "div",
                                                        klass="diff-item-row "
                                                        + " "
                                                        + norm_dif_item["klass"],
                                                    ):

                                                        # diff type column
                                                        with tag(
                                                            "div",
                                                            klass="diff-item-type-col replaced",
                                                        ):
                                                            with tag(
                                                                "div",
                                                                klass="diff-item-type-cell",
                                                            ):
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-type-text",
                                                                ):
                                                                    text(
                                                                        norm_dif_item[
                                                                            "change_type_label"
                                                                        ]
                                                                    )

                                                        # vertical divider
                                                        with tag(
                                                            "div",
                                                            klass="vertical-divider",
                                                        ):
                                                            text("")

                                                        # diff details column
                                                        with tag(
                                                            "div",
                                                            klass="diff-item-details-col replace",
                                                        ):

                                                            # prev data row
                                                            with tag(
                                                                "div",
                                                                klass="prev-data-row removed",
                                                            ):

                                                                # prev data line number cell
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-line-num-cell",
                                                                ):
                                                                    with tag(
                                                                        "div",
                                                                        klass="diff-item-line-num-text",
                                                                    ):
                                                                        text(
                                                                            norm_dif_item[
                                                                                "prev_line"
                                                                            ][
                                                                                "line_num"
                                                                            ]
                                                                        )

                                                                # vertical divider
                                                                with tag(
                                                                    "div",
                                                                    klass="vertical-divider",
                                                                ):
                                                                    text("")

                                                                # prev data text cell
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-text-cell",
                                                                ):
                                                                    # prev data text lines
                                                                    for (
                                                                        diff_text_line
                                                                    ) in norm_dif_item[
                                                                        "prev_line"
                                                                    ][
                                                                        "diff_text"
                                                                    ]:
                                                                        with tag(
                                                                            "div",
                                                                            klass="diff-text-line-row",
                                                                        ):
                                                                            with tag(
                                                                                "div",
                                                                                klass="diff-text-line",
                                                                            ):
                                                                                text(
                                                                                    diff_text_line
                                                                                )

                                                            # horizontal divider
                                                            with tag(
                                                                "div",
                                                                klass="horizontal-divider",
                                                            ):
                                                                text("")

                                                            # current data row
                                                            with tag(
                                                                "div",
                                                                klass="curr-data-row added",
                                                            ):
                                                                # current data line number cell
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-line-num-cell",
                                                                ):
                                                                    with tag(
                                                                        "div",
                                                                        klass="diff-item-line-num-text",
                                                                    ):
                                                                        text(
                                                                            norm_dif_item[
                                                                                "curr_line"
                                                                            ][
                                                                                "line_num"
                                                                            ]
                                                                        )

                                                                # vertical divider
                                                                with tag(
                                                                    "div",
                                                                    klass="vertical-divider",
                                                                ):
                                                                    text("")

                                                                # current data text cell
                                                                with tag(
                                                                    "div",
                                                                    klass="diff-item-text-cell",
                                                                ):
                                                                    # current data text lines
                                                                    for (
                                                                        diff_text_line
                                                                    ) in norm_dif_item[
                                                                        "curr_line"
                                                                    ][
                                                                        "diff_text"
                                                                    ]:
                                                                        with tag(
                                                                            "div",
                                                                            klass="diff-text-line-row",
                                                                        ):
                                                                            with tag(
                                                                                "div",
                                                                                klass="diff-text-line",
                                                                            ):
                                                                                text(
                                                                                    diff_text_line
                                                                                )

                                    # horizontal divider
                                    with tag("div", klass="horizontal-divider"):
                                        text("")

    html = indent(doc.getvalue())
    return html


# aggregators
def get_res_item_type(res_item):
    # TODO: add error handler (res_item arg)
    res_type = ""
    if res_item["result"] == "PASSED":
        res_type = "pass"
    elif res_item["result"] == "FOR_USER_EVALUATION":
        res_type = "eval"
    else:
        res_type = "fail"

    return res_type


def stringify_res_item_val(res_item):
    # TODO: add error handler (res_item)
    item_txt = json.dumps(res_item["value"], indent=4)
    return item_txt


def get_summary_bar_data(validation_results):
    # TODO: error handler (validation_results arg)
    summary_bar_data = {"pass": 0, "fail": 0, "eval": 0}

    for key in validation_results:
        item = validation_results[key]
        item_type = get_res_item_type(item)
        summary_bar_data[item_type] += 1

    return summary_bar_data


def get_norm_val_res_data(validation_results):
    # TODO: error handler (validation_results arg)
    norm_data = {"pass": {}, "fail": {}, "eval": {}}
    for key in validation_results:
        item = validation_results[key]
        item_type = get_res_item_type(item)
        item_text = stringify_res_item_val(item)
        norm_data[item_type][key] = item_text

    return norm_data


# html handlers
def make_deployment_validations_html(data, styles_file, logo_file):
    # TODO: error handler (data, styles_file, logo_file args)
    doc, tag, text = Doc().tagtext()
    with tag("html"):

        # stylesheet
        with tag("head"):
            doc.stag("link", rel="stylesheet", href=styles_file)

        # deployment validations report
        with tag("body"):

            # report title row
            with tag("div", klass="report-title-row"):
                with tag("div", klass="logo-box"):
                    doc.stag("img", src=logo_file, alt="F5", klass="logo")

                with tag("div"):
                    text("Journeys")

            # summary bar section
            with tag("div", klass="sum-bar-section"):

                # normalize summary bar raw data
                sum_bar_norm_data = get_summary_bar_data(data)

                # summary bar title row
                with tag("div", klass="sum-bar-title-row"):
                    with tag("div", klass="sum-bar-title"):
                        text("Deployment Validations Summary")

                # horizontal divider
                with tag("div", klass="sum-bar-title-divider"):
                    text("")

                # summary bar content row
                with tag("div", klass="sum-bar-content-row"):
                    # pass cell
                    with tag("div", klass="sum-bar-cell pass"):
                        # pass cell text box
                        with tag("div", klass="sum-bar-text-box pass"):
                            # pass cell title
                            with tag("div", klass="sum-bar-cell-title-box"):
                                with tag("div", klass="sum-bar-cell-title pass"):
                                    text("Successful Validations")

                            # pass cell data
                            with tag("div", klass="sum-bar-cell-data-box"):
                                with tag("div", klass="sum-bar-cell-data"):
                                    text(sum_bar_norm_data["pass"])

                        # pass cell icon box
                        with tag("div", klass="sum-bar-icon-box pass"):
                            # TODO: get svg icons from UX
                            text("")

                    # fail cell
                    with tag("div", klass="sum-bar-cell fail"):
                        # fail cell text box
                        with tag("div", klass="sum-bar-text-box fail"):
                            # fail cell title
                            with tag("div", klass="sum-bar-cell-title-box"):
                                with tag("div", klass="sum-bar-cell-title fail"):
                                    text("Failed Validations")

                            # fail cell data
                            with tag("div", klass="sum-bar-cell-data-box"):
                                with tag("div", klass="sum-bar-cell-data"):
                                    text(sum_bar_norm_data["fail"])

                        # fail cell icon box
                        with tag("div", klass="sum-bar-icon-box fail"):
                            # TODO: get svg icons from UX
                            text("")

                    # eval cell
                    with tag("div", klass="sum-bar-cell eval"):
                        # eval cell text box
                        with tag("div", klass="sum-bar-text-box eval"):
                            # eval cell title
                            with tag("div", klass="sum-bar-cell-title-box"):
                                with tag("div", klass="sum-bar-cell-title eval"):
                                    text("Validations Requiring User Evaluation")

                            # eval cell data
                            with tag("div", klass="sum-bar-cell-data-box"):
                                with tag("div", klass="sum-bar-cell-data"):
                                    text(sum_bar_norm_data["eval"])

                        # eval cell icon box
                        with tag("div", klass="sum-bar-icon-box eval"):
                            # TODO: get svg icons from UX
                            text("")

            # details section
            with tag("div", klass="details-section"):

                # normalize details section raw data
                details_norm_data = get_norm_val_res_data(data)

                # pass validations section
                with tag("div", klass="val-res-section"):

                    # section header row
                    with tag("div", klass="val-res-section-title-row pass"):

                        # section title
                        with tag("div", klass="val-res-section-title"):
                            text("Successful Validations")

                        # section sub-title
                        with tag("div", klass="val-res-section-sub-title"):
                            sub_title = "(" + str(sum_bar_norm_data["pass"]) + ")"
                            text(sub_title)

                    # section data row
                    with tag("div", klass="val-res-section-data-row"):

                        # validation results text lines
                        is_even = False
                        is_even_klass = ""
                        for key in details_norm_data["pass"]:

                            # set text line css class
                            if is_even:
                                is_even_klass = "even"
                            else:
                                is_even_klass = ""
                            is_even = not is_even

                            # set text line html
                            item_text = details_norm_data["pass"][key]
                            with tag("div", klass="val-res-txt-row " + is_even_klass):

                                # validator name
                                with tag("div", klass="val-res-label-box"):
                                    with tag("div", klass="val-res-label"):
                                        text(key + ":")

                                # validator text
                                with tag("div", klass="val-res-txt-box"):
                                    with tag("div", klass="val-res-txt"):
                                        text(item_text)

                # fail validations section
                with tag("div", klass="val-res-section"):

                    # section header row
                    with tag("div", klass="val-res-section-title-row fail"):

                        # section title
                        with tag("div", klass="val-res-section-title"):
                            text("Failed Validations")

                        # section sub-title
                        with tag("div", klass="val-res-section-sub-title"):
                            sub_title = "(" + str(sum_bar_norm_data["fail"]) + ")"
                            text(sub_title)

                    # section data row
                    with tag("div", klass="val-res-section-data-row"):

                        # validation results text lines
                        is_even = False
                        is_even_klass = ""
                        for key in details_norm_data["fail"]:

                            # set text line css class
                            if is_even:
                                is_even_klass = "even"
                            else:
                                is_even_klass = ""
                            is_even = not is_even

                            # set text line html
                            item_text = details_norm_data["fail"][key]

                            # validator name
                            with tag("div", klass="val-res-label-box"):
                                with tag("div", klass="val-res-label"):
                                    text(key + ":")

                            # validator text
                            with tag("div", klass="val-res-txt-box"):
                                with tag("div", klass="val-res-txt"):
                                    text(item_text)

                # eval validations section
                with tag("div", klass="val-res-section"):

                    # section header row
                    with tag("div", klass="val-res-section-title-row eval"):

                        # section title
                        with tag("div", klass="val-res-section-title"):
                            text("Validations Requiring User Evaluation")

                        # section sub-title
                        with tag("div", klass="val-res-section-sub-title"):
                            sub_title = "(" + str(sum_bar_norm_data["eval"]) + ")"
                            text(sub_title)

                    # section data row
                    with tag("div", klass="val-res-section-data-row"):

                        # validation results text lines
                        is_even = False
                        is_even_klass = ""
                        for key in details_norm_data["eval"]:

                            # set text line css class
                            if is_even:
                                is_even_klass = "even"
                            else:
                                is_even_klass = ""
                            is_even = not is_even

                            # set text line html
                            item_text = details_norm_data["eval"][key]
                            with tag("div", klass="val-res-txt-row " + is_even_klass):

                                # validator name
                                with tag("div", klass="val-res-label-box"):
                                    with tag("div", klass="val-res-label"):
                                        text(key + ":")

                                # validator text
                                with tag("div", klass="val-res-txt-box"):
                                    with tag("div", klass="val-res-txt"):
                                        text(item_text)

    html = indent(doc.getvalue())
    return html
