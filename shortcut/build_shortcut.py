#!/usr/bin/env python3
"""
Builds "Upload HR to GitHub.shortcut": uploads the newest Health Auto Export
CSV from iCloud Drive to incoming/ in the hr-mon repo via the GitHub API.

The token and the export folder are asked for at import time on the
iPhone, so neither is stored in this repo. Needs macOS (for signing):
    python3 shortcut/build_shortcut.py
"""
import plistlib
import subprocess
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNSIGNED = HERE / "unsigned.shortcut"
SIGNED = HERE / "Upload HR to GitHub.shortcut"
REPO_CONTENTS_URL = "https://api.github.com/repos/eshwarpotturi/hr-mon/contents/incoming/"


def uid():
    return str(uuid.uuid4()).upper()


def var(output_uuid, name):
    """Reference to an earlier action's output."""
    return {"OutputUUID": output_uuid, "OutputName": name, "Type": "ActionOutput"}


def var_param(output_uuid, name):
    return {"Value": var(output_uuid, name), "WFSerializationType": "WFTextTokenAttachment"}


def text(*parts):
    """Text with embedded variables; parts are str or (uuid, name)."""
    string, attachments = "", {}
    for part in parts:
        if isinstance(part, str):
            string += part
        else:
            attachments[f"{{{len(string)}, 1}}"] = var(*part)
            string += "￼"
    return {
        "Value": {"string": string, "attachmentsByRange": attachments},
        "WFSerializationType": "WFTextTokenString",
    }


def dict_item(key, value):
    return {"WFItemType": 0, "WFKey": text(key), "WFValue": value}


def dictionary(*items):
    return {
        "Value": {"WFDictionaryFieldValueItems": list(items)},
        "WFSerializationType": "WFDictionaryFieldValue",
    }


def action(identifier, params):
    return {"WFWorkflowActionIdentifier": f"is.workflow.actions.{identifier}",
            "WFWorkflowActionParameters": params}


token_id, folder_id, filter_id, b64_id, name_id, url_id = (uid() for _ in range(6))

actions = [
    # 0: GitHub token (filled in at import)
    action("gettext", {"UUID": token_id, "WFTextActionText": ""}),
    # 1: contents of the export folder (picked at import)
    action("file.getfoldercontents", {"UUID": folder_id, "Recursive": False}),
    # 2: newest file only
    action("filter.files", {
        "UUID": filter_id,
        "WFContentItemInputParameter": var_param(folder_id, "Contents of Folder"),
        "WFContentItemSortProperty": "Last Modified Date",
        "WFContentItemSortOrder": "Latest First",
        "WFContentItemLimitEnabled": True,
        "WFContentItemLimitNumber": 1.0,
    }),
    # 3: base64, no line breaks (GitHub rejects wrapped base64)
    action("base64encode", {
        "UUID": b64_id,
        "WFEncodeMode": "Encode",
        "WFBase64LineBreakMode": "None",
        "WFInput": var_param(filter_id, "Files"),
    }),
    # 4: file name (without extension)
    action("properties.files", {
        "UUID": name_id,
        "WFContentItemPropertyName": "Name",
        "WFInput": var_param(filter_id, "Files"),
    }),
    # 5: PUT to GitHub contents API
    action("downloadurl", {
        "UUID": url_id,
        "WFURL": text(REPO_CONTENTS_URL, (name_id, "Name"), ".csv"),
        "WFHTTPMethod": "PUT",
        "ShowHeaders": True,
        "WFHTTPHeaders": dictionary(
            dict_item("Authorization", text("Bearer ", (token_id, "Text"))),
            dict_item("Accept", text("application/vnd.github+json")),
        ),
        "WFHTTPBodyType": "JSON",
        "WFJSONValues": dictionary(
            dict_item("message", text("Upload from iPhone: ", (name_id, "Name"))),
            dict_item("content", text((b64_id, "Base64 Encoded"))),
        ),
    }),
    # 6: show the result
    action("notification", {
        "WFNotificationActionTitle": "HR upload",
        "WFNotificationActionBody": text((url_id, "Contents of URL")),
    }),
]

shortcut = {
    "WFWorkflowClientVersion": "2605.0.5",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983,
                       "WFWorkflowIconGlyphNumber": 59511},
    "WFWorkflowTypes": [],
    "WFWorkflowInputContentItemClasses": [],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowHasShortcutInputVariables": False,
    "WFWorkflowImportQuestions": [
        {"ActionIndex": 0, "Category": "Parameter", "ParameterKey": "WFTextActionText",
         "Text": "Paste your GitHub token (starts with github_pat_)", "DefaultValue": ""},
        {"ActionIndex": 1, "Category": "Parameter", "ParameterKey": "WFFolder",
         "Text": "Pick the folder: iCloud Drive > Health Auto Export > Daily hr"},
    ],
    "WFWorkflowActions": actions,
}

with UNSIGNED.open("wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
subprocess.run(["shortcuts", "sign", "--mode", "anyone",
                "--input", str(UNSIGNED), "--output", str(SIGNED)], check=True)
UNSIGNED.unlink()
print(f"Wrote {SIGNED}")
