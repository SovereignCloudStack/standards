"""
Unit tests for node distribution check functions.

(c) Martin Morgenstern <martin.morgenstern@cloudandheat.com>, 4/2024
(c) Hannes Baum <hannes.baum@cloudandheat.com>, 5/2024
SPDX-License-Identifier: CC-BY-SA-4.0
"""

from pathlib import Path
import yaml

import pytest

from k8s_node_distribution_check import check_nodes


HERE = Path(__file__).parent


@pytest.fixture
def load_testdata():
    with open(Path(HERE, "testdata", "scenarios.yaml")) as stream:
        return yaml.safe_load(stream)


@pytest.mark.parametrize("yaml_key", ["success-1", "success-2"])
def test_success_single_region_warning(yaml_key, caplog, load_testdata):
    data = load_testdata[yaml_key]
    assert check_nodes(data.values()) == 0
    assert len(caplog.records) == 2
    for record in caplog.records:
        assert "no distribution across multiple regions" in record.message
        assert record.levelname == "WARNING"


def test_not_enough_nodes(caplog, load_testdata):
    data = load_testdata["not-enough-nodes"]
    assert check_nodes(data.values()) == 2
    assert len(caplog.records) == 1
    assert "cluster only contains a single node" in caplog.records[0].message
    assert caplog.records[0].levelname == "ERROR"


@pytest.mark.parametrize("yaml_key", ["no-distribution-1", "no-distribution-2"])
def test_no_distribution(yaml_key, caplog, load_testdata):
    data = load_testdata[yaml_key]
    with caplog.at_level("ERROR"):
        assert check_nodes(data.values()) == 2
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert "distribution of nodes described in the standard couldn't be detected" in record.message
    assert record.levelname == "ERROR"


def notest_missing_label(caplog, load_testdata):
    data = load_testdata["missing-labels"]
    assert check_nodes(data.values()) == 2
    hostid_missing_records = [
        record for record in caplog.records
        if "label for host-ids" in record.message
    ]
    assert len(hostid_missing_records) == 1
    assert hostid_missing_records[0].levelname == "ERROR"
