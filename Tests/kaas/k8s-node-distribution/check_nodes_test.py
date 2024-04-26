"""
Unit tests for node distribution check functions.

(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 4/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

from pathlib import Path
import importlib
import yaml

import pytest


check_nodes = importlib.import_module("k8s-node-distribution-check").check_nodes


HERE = Path(__file__).parent


def load_testdata(filename):
    with open(Path(HERE, "testdata", filename)) as stream:
        return yaml.safe_load(stream)


@pytest.mark.parametrize("yaml_file", ["test-success-1.yaml", "test-success-2.yaml"])
def test_success_single_region_warning(yaml_file, caplog):
    data = load_testdata(yaml_file)
    assert check_nodes(data.values()) == 0
    assert len(caplog.records) == 2
    for record in caplog.records:
        assert "no distribution across multiple regions" in record.message
        assert record.levelname == "WARNING"


def test_not_enough_nodes(caplog):
    data = load_testdata("test-not-enough-nodes.yaml")
    assert check_nodes(data.values()) == 2
    assert len(caplog.records) == 1
    assert "cluster only contains a single node" in caplog.records[0].message
    assert caplog.records[0].levelname == "ERROR"


@pytest.mark.parametrize("yaml_file", ["test-no-distribution-1.yaml", "test-no-distribution-2.yaml"])
def test_no_distribution(yaml_file, caplog):
    data = load_testdata(yaml_file)
    with caplog.at_level("ERROR"):
        assert check_nodes(data.values()) == 2
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert "distribution of nodes described in the standard couldn't be detected" in record.message
    assert record.levelname == "ERROR"


def test_missing_label(caplog):
    data = load_testdata("test-missing-labels.yaml")
    assert check_nodes(data.values()) == 2
    hostid_missing_records = [
        record for record in caplog.records
        if "label for host-ids" in record.message
    ]
    assert len(hostid_missing_records) == 1
    assert hostid_missing_records[0].levelname == "ERROR"
