"""
Pytest based unit and regression tests for check_yaml.

(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 3/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

import pytest
from check_yaml import check
from pathlib import Path


HERE = Path(__file__).parent
TEST_ROOT = HERE.parent.parent

CLEAN_YAML_DIR = Path(TEST_ROOT, "iaas")
BUGGY_YAML_DIR = Path(TEST_ROOT, "testing")

EXPECTED_ERRORS = """
ERROR: flavor 'SCS-1V-4': field 'scs:cpu-type' contradicting name-v2 'SCS-1V-4'; found 'crowded-core', expected 'shared-core'
ERROR: flavor 'SCS-2V-8': field 'scs:name-v1' contradicting name-v2 'SCS-2V-8'; found 'SCS-2V-8', expected 'SCS-2V:8'
ERROR: flavor 'SCS-4V-16': field 'ram' contradicting name-v2 'SCS-4V-16'; found 12, expected 16.0
ERROR: flavor 'SCS-8V-32': field 'disk' contradicting name-v2 'SCS-8V-32'; found 128, expected undefined
ERROR: flavor 'SCS-1V-2': field 'cpus' contradicting name-v2 'SCS-1V-2'; found 2, expected 1
ERROR: flavor 'SCS-2V-4-20s': field 'scs:disk0-type' contradicting name-v2 'SCS-2V-4-20s'; found 'network', expected 'ssd'
ERROR: flavor 'SCS-4V-16-100s': field 'disk' contradicting name-v2 'SCS-4V-16-100s'; found 10, expected 100
ERROR: file 'scs-0103-v1-flavors-wrong.yaml': found 7 errors
""".strip()

TEST_PARAMS = (
    (CLEAN_YAML_DIR, 0, ""),
    (BUGGY_YAML_DIR, 1, EXPECTED_ERRORS),
)


@pytest.mark.parametrize("directory, num_errors, expected_output", TEST_PARAMS)
def test_check_yaml(capsys, directory, num_errors, expected_output):
    assert check(directory) == num_errors
    captured = capsys.readouterr()
    assert captured.err.strip() == expected_output
