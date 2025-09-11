import logging
import typing

import openstack

from . import flavor_names


logger = logging.getLogger(__name__)


TESTCASES = ('scs-0100-syntax-check', 'scs-0100-semantics-check', 'flavor-name-check')
STRATEGY = flavor_names.ParsingStrategy(
    vstr='v3',
    parsers=(flavor_names.parser_v3, ),
    tolerated_parsers=(flavor_names.parser_v2, flavor_names.parser_v1),
)
ACC_DISK = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)


def compute_scs_flavors(flavors: typing.List[openstack.compute.v2.flavor.Flavor], parser=STRATEGY) -> list:
    """
    Precompute the Flavorname instance for each openstack flavor where applicable.

    Returns a list of pairs of the form (flavor, flavorname_instance_or_none).
    This information is (re)used for multiple testcases.
    """
    result = []
    for flv in flavors:
        if not flv.name or flv.name[:4] != 'SCS-':
            continue  # not an SCS flavor; none of our business
        try:
            flavorname = parser(flv.name)
        except ValueError as exc:
            logger.info(f"error parsing {flv.name}: {exc}")
            flavorname = None
        result.append((flv, flavorname))
    return result


def compute_scs_0100_syntax_check(scs_flavors: list) -> bool:
    """This test ensures that each SCS flavor is indeed named correctly."""
    problems = [flv.name for flv, flavorname in scs_flavors if not flavorname]
    if problems:
        logger.error(f"scs-100-syntax-check: flavor(s) failed: {', '.join(sorted(problems))}")
    return not problems


def compute_scs_0100_semantics_check(scs_flavors: list) -> bool:
    """
    This test ensures that each SCS flavor 'does what it says on the tin'.

    In particular, no flavor name may overpromise anything.
    NOTE that this test is incomplete; it only checks the most obvious properties.
    See also <https://github.com/SovereignCloudStack/standards/issues/554>.
    """
    problems = set()
    for flv, flavorname in scs_flavors:
        if not flavorname:
            continue  # this case is handled by syntax check
        cpuram = flavorname.cpuram
        if flv.vcpus < cpuram.cpus:
            logger.error(f"Flavor {flv.name} CPU overpromise: {flv.vcpus} < {cpuram.cpus}")
            problems.add(flv.name)
        elif flv.vcpus > cpuram.cpus:
            logger.info(f"Flavor {flv.name} CPU underpromise: {flv.vcpus} > {cpuram.cpus}")
        # RAM
        flvram = int((flv.ram + 51) / 102.4) / 10
        # Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
        if flvram >= 10 and flvram != int(flvram) or flvram * 2 != int(flvram * 2):
            logger.info(f"Flavor {flv.name} uses discouraged uneven size of memory {flvram:.1f} GiB")
        if flvram < cpuram.ram:
            logger.error(f"Flavor {flv.name} RAM overpromise {flvram:.1f} < {cpuram.ram:.1f}")
            problems.add(flv.name)
        elif flvram > cpuram.ram:
            logger.info(f"Flavor {flv.name} RAM underpromise {flvram:.1f} > {cpuram.ram:.1f}")
        # Disk could have been omitted
        disksize = flavorname.disk.disksize if flavorname.disk else 0
        # We have a recommendation for disk size steps
        if disksize not in ACC_DISK:
            logger.info(f"Flavor {flv.name} non-standard disk size {disksize}, should have (5, 10, 20, 50, 100, 200, ...)")
        if flv.disk < disksize:
            logger.error(f"Flavor {flv.name} disk overpromise {flv.disk} < {disksize}")
            problems.add(flv.name)
        elif flv.disk > disksize:
            logger.info(f"Flavor {flv.name} disk underpromise {flv.disk} > {disksize}")
    if problems:
        logger.error(f"scs-100-semantics-check: flavor(s) failed: {', '.join(sorted(problems))}")
    return not problems
