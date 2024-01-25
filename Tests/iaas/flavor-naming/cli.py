#!/usr/bin/env python3
import click
import sys

from flavor_name_check import parser_v1, parser_v2


class Version:
    def __init__(self, parser):
        self.parser = parser


VERSIONS = {
    'v1': Version(parser_v1),
    'v2': Version(parser_v2),
    'v3': Version(parser_v2),
}
VERSIONS['latest'] = VERSIONS['v3']


@click.group()
@click.argument('version', type=click.Choice(list(VERSIONS), case_sensitive=False))
@click.pass_context
def cli(ctx, version):
    vobj = VERSIONS.get(version)
    ctx.obj['version'] = vobj


@cli.result_callback()
def process_pipeline(rc, *args, **kwargs):
    sys.exit(rc)


@cli.command()
@click.argument('namestr', nargs=-1)
@click.pass_context
def check(ctx, namestr):
    version = ctx.obj['version']
    errors = 0
    for name in namestr:
        try:
            flavorname = version.parser(name)
        except ValueError as exc:
            print(f"✘ {name}: ERROR {exc}")
            errors += 1
        else:
            if flavorname is None:
                print(f"  {name}: NOT an SCS flavor")
            else:
                print(f"✓ {name}: OK")
    return errors


if __name__ == '__main__':
    cli(obj={})
