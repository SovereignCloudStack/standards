import logging
import typing

import openstack

from . import flavor_names


logger = logging.getLogger(__name__)


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
            flavorname = f"error parsing {flv.name}: {exc}"
        result.append((flv, flavorname))
    return result


def compute_scs_0100_syntax_check(scs_flavors: list) -> bool:
    """This test ensures that each SCS flavor is indeed named correctly."""
    return [flavorname for _, flavorname in scs_flavors if isinstance(flavorname, str)]


def compute_scs_0100_semantics_check(scs_flavors: list) -> bool:
    """
    This test ensures that each SCS flavor 'does what it says on the tin'.

    In particular, no flavor name may overpromise anything.
    NOTE that this test is incomplete; it only checks the most obvious properties.
    See also <https://github.com/SovereignCloudStack/standards/issues/554>.
    """
    problems = []
    for flv, flavorname in scs_flavors:
        if isinstance(flavorname, str):
            continue  # this case is handled by syntax check
        cpuram = flavorname.cpuram
        if flv.vcpus < cpuram.cpus:
            problems.append(f"CPU overpromise for {flv.name!r}: {flv.vcpus} < {cpuram.cpus}")
        elif flv.vcpus > cpuram.cpus:
            logger.info(f"CPU underpromise for {flv.name!r}: {flv.vcpus} > {cpuram.cpus}")
        # RAM
        flvram = int((flv.ram + 51) / 102.4) / 10
        # Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
        if flvram >= 10 and flvram != int(flvram) or flvram * 2 != int(flvram * 2):
            logger.info(f"Discouraged uneven size of memory for {flv.name!r}: {flvram:.1f} GiB")
        if flvram < cpuram.ram:
            problems.append(f"RAM overpromise for {flv.name!r}: {flvram:.1f} < {cpuram.ram:.1f}")
        elif flvram > cpuram.ram:
            logger.info(f"RAM underpromise for {flv.name!r}: {flvram:.1f} > {cpuram.ram:.1f}")
        # Disk could have been omitted
        disksize = flavorname.disk.disksize if flavorname.disk else 0
        # We have a recommendation for disk size steps
        if disksize not in ACC_DISK:
            logger.info(f"Non-standard disk size for {flv.name!r}: {disksize} not in (5, 10, 20, 50, 100, 200, ...)")
        if flv.disk < disksize:
            problems.append(f"Disk overpromise for {flv.name!r}: {flv.disk} < {disksize}")
        elif flv.disk > disksize:
            logger.info(f"Disk underpromise for {flv.name!r}: {flv.disk} > {disksize}")
    return problems
