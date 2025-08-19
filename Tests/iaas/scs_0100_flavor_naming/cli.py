#!/usr/bin/env python3
"""Command-line interface for validation and interactive construction of flavor names"""
import logging
import sys

import click
import yaml

from flavor_names import parser_v1, parser_v2, parser_v3, inputflavor, outputter, flavorname_to_dict, \
    prettyname, ParsingStrategy


PARSERS = {ps.vstr: ps for ps in [
    ParsingStrategy(vstr='v1', parsers=(parser_v1, ), invalid_parsers=(parser_v2, )),
    ParsingStrategy(vstr='v1/v2', parsers=(parser_v1, ), tolerated_parsers=(parser_v2, )),
    ParsingStrategy(vstr='v2/v1', parsers=(parser_v2, ), tolerated_parsers=(parser_v1, )),
    ParsingStrategy(vstr='v2', parsers=(parser_v2, ), invalid_parsers=(parser_v1, )),
    ParsingStrategy(vstr='v3', parsers=(parser_v3, ), invalid_parsers=(parser_v1, )),
]}
_, PARSERS['latest'] = max(PARSERS.items())


def noop(*args, **kwargs):
    pass


class Config:
    def __init__(self):
        self.verbose = False

    @property
    def printv(self):
        return print if self.verbose else noop


@click.group()
@click.option('-d', '--debug', 'debug', is_flag=True)
@click.option('-v', '--verbose', 'verbose', is_flag=True)
@click.pass_obj
def cli(cfg, debug=False, verbose=False):
    cfg.verbose = verbose


@cli.result_callback()
def process_pipeline(rc, *args, **kwargs):
    sys.exit(rc)


@cli.command()
@click.argument('version', type=click.Choice(list(PARSERS), case_sensitive=False))
@click.argument('name', nargs=-1)
@click.option('-o', '--output', 'output', type=click.Choice(['none', 'prose', 'yaml']),
              help='select output format (default: none)')
@click.pass_obj
def parse(cfg, version, name, output='none'):
    """Validates flavor names, optionally turns into prose/yaml.

    The first argument selects the version of the flavor naming standard upon which to base the syntax
    validation. With 'v1/v2', flavor names of both kinds are accepted, but warnings are emitted for v2,
    and similarly with 'v2/v1', where warnings are emitted for v1.
    """
    parser = PARSERS.get(version)
    printv = cfg.printv
    errors = 0
    for namestr in name:
        try:
            flavorname = parser(namestr)
        except ValueError as exc:
            print(f"{exc}: {namestr}")
            errors += 1
        else:
            if flavorname is None:
                print(f"NOT an SCS flavor: {namestr}")
            elif output == 'prose':
                printv(namestr, end=': ')
                print(f"{prettyname(flavorname)}")
            elif output == 'yaml':
                print(yaml.dump(flavorname_to_dict(flavorname), explicit_start=True))
            else:
                printv(f"OK: {namestr}")
    return errors


@cli.command()
def input():
    """Interactively constructs a flavor name."""
    flavorname = inputflavor()
    print(outputter(flavorname))


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli(obj=Config())
