#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# scs-test-runner.py
#
# (c) Matthias Büchse <matthias.buechse@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import os.path
import shutil
import subprocess
import sys
import tempfile
import time

import click
import tomli


logger = logging.getLogger(__name__)
MONITOR_URL = "https://compliance.sovereignit.cloud/"


class Config:
    def __init__(self):
        self.cwd = os.path.abspath(os.path.dirname(sys.argv[0]) or os.getcwd())
        self.scs_compliance_check = os.path.join(self.cwd, 'scs-compliance-check.py')
        self.ssh_keygen = shutil.which('ssh-keygen')
        self.curl = shutil.which('curl')
        self.secrets = {}
        self.presets = {}
        self.scopes = {}
        self.subjects = {}

    def load_toml(self, path):
        self.cwd = os.path.abspath(os.path.dirname(path))
        with open(path, "rb") as fileobj:
            toml_dict = tomli.load(fileobj)
        self.scopes.update(toml_dict.get('scopes', {}))
        self.subjects.update(toml_dict.get('subjects', {}))
        self.presets.update(toml_dict.get('presets', {}))
        self.secrets.update(toml_dict.get('secrets', {}))

    def abspath(self, path):
        return os.path.join(self.cwd, path)

    def build_command(self, scope, subject, output):
        cmd = [
            sys.executable, self.scs_compliance_check, self.abspath(self.scopes[scope]['spec']),
            '--debug', '-C', '-o', output, '-s', subject
        ]
        for key, value in self.subjects[subject]['mapping'].items():
            cmd.extend(['-a', f'{key}={value}'])
        return cmd


@click.group()
@click.option('-d', '--debug', 'debug', is_flag=True)
@click.option('-c', '--config', 'config', type=click.Path(exists=True, dir_okay=False), default='config.toml')
@click.pass_obj
def cli(cfg, debug=False, config=None):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    cfg.load_toml(config)


@cli.result_callback()
def process_pipeline(rc, *args, **kwargs):
    sys.exit(rc)


def _run_all(commands, num_workers=5):
    processes = []
    while commands or processes:
        while commands and len(processes) < num_workers:
            processes.append(subprocess.Popen(commands.pop()))
        processes[:] = [p for p in processes if p.poll() is None]
        time.sleep(0.5)


@cli.command()
@click.option('--scope', 'scopes', type=str)
@click.option('--subject', 'subjects', type=str)
@click.option('--preset', 'preset', type=str)
@click.option('--num-workers', 'num_workers', type=int, default=5)
@click.option('--monitor-url', 'monitor_url', type=str, default=MONITOR_URL)
@click.option('-o', '--output', 'report_yaml', type=click.Path(exists=False), default=None)
@click.pass_obj
def run(cfg, scopes, subjects, preset, num_workers, monitor_url, report_yaml):
    """
    run compliance tests and upload results to compliance monitor
    """
    if not scopes and not subjects and not preset:
        preset = 'default'
    if preset:
        preset_dict = cfg.presets.get(preset)
        if preset_dict is None:
            raise KeyError('preset not found')
        scopes = preset_dict['scopes']
        subjects = preset_dict['subjects']
        num_workers = preset_dict.get('workers', num_workers)
    else:
        scopes = [scope.strip() for scope in scopes.split(',')] if scopes else []
        subjects = [subject.strip() for subject in subjects.split(',')] if subjects else []
    if not scopes or not subjects:
        raise click.UsageError('both scope(s) and subject(s) must be non-empty')
    if not monitor_url.endswith('/'):
        monitor_url += '/'
    logger.debug(f'running tests for scope(s) {", ".join(scopes)} and subject(s) {", ".join(subjects)}')
    logger.debug(f'monitor url: {monitor_url}, num_workers: {num_workers}, output: {report_yaml}')
    with open(cfg.abspath(cfg.secrets['tokenfile']), "r") as fileobj:
        auth_token = fileobj.read().strip()
    with tempfile.TemporaryDirectory(dir=cfg.cwd) as tdirname:
        jobs = [(scope, subject) for scope in scopes for subject in subjects]
        outputs = [os.path.join(tdirname, f'report-{idx}.yaml') for idx in range(len(jobs))]
        commands = [cfg.build_command(job[0], job[1], output) for job, output in zip(jobs, outputs)]
        _run_all(commands, num_workers=num_workers)
        report_yaml_tmp = os.path.join(tdirname, f'report.yaml')
        with open(report_yaml_tmp, 'wb') as tfileobj:
            for output in outputs:
                with open(output, 'rb') as sfileobj:
                    shutil.copyfileobj(sfileobj, tfileobj)
        subprocess.run([
            cfg.ssh_keygen,
            '-Y', 'sign',
            '-f', cfg.abspath(cfg.secrets['keyfile']),
            '-n', 'report',
            report_yaml_tmp,
        ])
        subprocess.run([
            cfg.curl,
            '--fail-with-body',
            '--data-binary', f'@{report_yaml_tmp}.sig',
            '--data-binary', f'@{report_yaml_tmp}',
            '-H', 'Content-Type: application/x-signed-yaml',
            '-H', f'Authorization: Basic {auth_token}',
            f'{monitor_url}reports',
        ])
        if report_yaml is not None:
            # for Windows people, remove target first
            try:
                os.remove(report_yaml)
            except FileNotFoundError:
                pass
            os.rename(report_yaml_tmp, report_yaml)
    return 0


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli(obj=Config())
