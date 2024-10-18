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

from kaas.plugin.run_plugin import run_plugin_create, run_plugin_delete

logger = logging.getLogger(__name__)
MONITOR_URL = "https://compliance.sovereignit.cloud/"


class Config:
    def __init__(self):
        self.cwd = os.path.abspath(os.path.dirname(sys.argv[0]) or os.getcwd())
        self.scs_compliance_check = os.path.join(self.cwd, 'scs-compliance-check.py')
        self.cleanup_py = os.path.join(self.cwd, 'cleanup.py')
        self.ssh_keygen = shutil.which('ssh-keygen')
        self.curl = shutil.which('curl')
        self.secrets = {}
        self.presets = {}
        self.scopes = {}
        self.subjects = {}
        self._auth_token = None

    def load_toml(self, path):
        self.cwd = os.path.abspath(os.path.dirname(path))
        with open(path, "rb") as fileobj:
            toml_dict = tomli.load(fileobj)
        self.scopes.update(toml_dict.get('scopes', {}))
        self.subjects.update(toml_dict.get('subjects', {}))
        self.presets.update(toml_dict.get('presets', {}))
        self.secrets.update(toml_dict.get('secrets', {}))

    @property
    def auth_token(self):
        if self._auth_token is None:
            pass
        with open(self.abspath(self.secrets['tokenfile']), "r") as fileobj:
            self._auth_token = fileobj.read().strip()
        return self._auth_token

    def get_subject_mapping(self, subject):
        default_mapping = self.subjects.get('_', {}).get('mapping', {})
        mapping = {key: value.format(subject=subject) for key, value in default_mapping.items()}
        mapping.update(self.subjects.get(subject, {}).get('mapping', {}))
        return mapping

    def generate_compliance_check_jobs(self, subjects, scopes):
        jobs = []
        for subject in subjects:
            for scope in scopes:
                if scope == "scs-compatible-iaas":
                    jobs.append([scope, subject])
                if scope == "scs-compatible-kaas":
                    k8s_setup = self.get_kubernetes_setup(subject)
                    for k8s_version in k8s_setup["kube_versions"]:
                        kaas_subject = f"{subject}.{k8s_version}"
                        jobs.append([scope, kaas_subject, k8s_version, k8s_setup["kube_plugin"]])
        return jobs

    def get_kubernetes_setup(self, subject):
        default_kubernetes_setup = self.subjects.get('_', {}).get('kubernetes_setup', {})
        kubernetes_setup = {"kube_plugin": default_kubernetes_setup['kube_plugin'], "kube_versions": default_kubernetes_setup['kube_versions']}
        kubernetes_setup.update(self.subjects.get(subject, {}).get('kubernetes_setup', {}))
        return kubernetes_setup

    def build_clusters_for_jobs_in_sequence(self, jobs):
        for i in range(len(jobs)):
            if jobs[i][0] == "scs-compatible-kaas":
                cluster_id = f"{jobs[i][1]}"
                logger.debug(f"Provide cluster '{cluster_id}'")
                kubeconfig_path = os.getcwd() + "/k8s_test_kubeconfigs/"
                if not os.path.exists(kubeconfig_path):
                    os.mkdir(kubeconfig_path)
                kubeconfig_filepath = kubeconfig_path + f"{cluster_id}.yaml"
                kubeconfig = run_plugin_create(jobs[i][3], cluster_id, jobs[i][2], (kubeconfig_filepath))
                jobs[i].append(kubeconfig)
        return jobs

    def delete_clusters_for_jobs_in_sequence(self, jobs):
        for i in range(len(jobs)):
            if jobs[i][0] == "scs-compatible-kaas":
                cluster_id = f"{jobs[i][1]}"
                logger.debug(f"Delete cluster '{cluster_id}'")
                run_plugin_delete(jobs[i][3], cluster_id)

    def abspath(self, path):
        return os.path.join(self.cwd, path)

    def build_check_command(self, job, output):
        scope = job[0]
        subject = job[1]
        # TODO figure out when to supply --debug here (but keep separated from our --debug)
        cmd = [
            sys.executable, self.scs_compliance_check, self.abspath(self.scopes[scope]['spec']),
            '--debug', '-C', '-o', output, '-s', subject,
        ]
        for key, value in self.get_subject_mapping(subject).items():
            cmd.extend(['-a', f'{key}={value}'])
        if len(job) == 5 and scope == "scs-compatible-kaas":
            cmd.extend(['-a', f'kubeconfig={job[4]}'])
            cmd.extend(['-a', f'result_dir_name={job[1]}-{job[2]}'])
        elif len(job) != 5 and scope == "scs-compatible-kaas":
            logger.Error(f"Scope is '{job[0]}' but no kubeconfig was provided")
        return cmd

    def build_cleanup_command(self, subject):
        # TODO figure out when to supply --debug here (but keep separated from our --debug)
        return [
            sys.executable, self.cleanup_py,
            '-c', self.get_subject_mapping(subject)['os_cloud'],
            '--prefix', '_scs-',
            '--ipaddr', '10.1.0.',
            '--debug',
        ]

    def build_sign_command(self, target_path):
        return [
            self.ssh_keygen,
            '-Y', 'sign',
            '-f', self.abspath(self.secrets['keyfile']),
            '-n', 'report',
            target_path,
        ]

    def build_upload_command(self, target_path, monitor_url):
        if not monitor_url.endswith('/'):
            monitor_url += '/'
        return [
            self.curl,
            '--fail-with-body',
            '--data-binary', f'@{target_path}.sig',
            '--data-binary', f'@{target_path}',
            '-H', 'Content-Type: application/x-signed-yaml',
            '-H', f'Authorization: Basic {self.auth_token}',
            f'{monitor_url}reports',
        ]


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


def _run_commands(commands, num_workers=5):
    processes = []
    while commands or processes:
        while commands and len(processes) < num_workers:
            processes.append(subprocess.Popen(commands.pop()))
        processes[:] = [p for p in processes if p.poll() is None]
        time.sleep(0.5)


def _concat_files(source_paths, target_path):
    with open(target_path, 'wb') as tfileobj:
        for path in source_paths:
            with open(path, 'rb') as sfileobj:
                shutil.copyfileobj(sfileobj, tfileobj)


def _move_file(source_path, target_path):
    # for Windows people, remove target first, but don't try too hard (Windows is notoriously bad at this)
    # this two-stage delete-rename approach does have a tiny (irrelevant) race condition (thx Windows)
    try:
        os.remove(target_path)
    except FileNotFoundError:
        pass
    os.rename(source_path, target_path)


@cli.command()
@click.option('--scope', 'scopes', type=str)
@click.option('--subject', 'subjects', type=str)
@click.option('--preset', 'preset', type=str)
@click.option('--num-workers', 'num_workers', type=int, default=5)
@click.option('--monitor-url', 'monitor_url', type=str, default=MONITOR_URL)
@click.option('-o', '--output', 'report_yaml', type=click.Path(exists=False), default=None)
@click.option('--upload/--no-upload', default=True)
@click.pass_obj
def run(cfg, scopes, subjects, preset, num_workers, monitor_url, report_yaml, upload):
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
    logger.debug(f'running tests for scope(s) {", ".join(scopes)} and subject(s) {", ".join(subjects)}')
    logger.debug(f'monitor url: {monitor_url}, num_workers: {num_workers}, output: {report_yaml}')
    with tempfile.TemporaryDirectory(dir=cfg.cwd) as tdirname:
        report_yaml_tmp = os.path.join(tdirname, 'report.yaml')
        jobs = cfg.generate_compliance_check_jobs(subjects, scopes)
        logger.debug("Create clusters and provide kubeconfig")
        jobs = cfg.build_clusters_for_jobs_in_sequence(jobs)
        outputs = [os.path.join(tdirname, f'report-{idx}.yaml') for idx in range(len(jobs))]
        commands = [cfg.build_check_command(job, output) for job, output in zip(jobs, outputs)]
        _run_commands(commands, num_workers=num_workers)
        _concat_files(outputs, report_yaml_tmp)
        if report_yaml is not None:
            _move_file(report_yaml_tmp, report_yaml)
        logger.debug("delete clusters")
        cfg.delete_clusters_for_jobs_in_sequence(jobs)
    return 0


@cli.command()
@click.option('--subject', 'subjects', type=str)
@click.option('--preset', 'preset', type=str)
@click.option('--num-workers', 'num_workers', type=int, default=5)
@click.pass_obj
def cleanup(cfg, subjects, preset, num_workers):
    """
    clean up any lingering resources
    """
    if not subjects and not preset:
        preset = 'default'
    if preset:
        preset_dict = cfg.presets.get(preset)
        if preset_dict is None:
            raise KeyError('preset not found')
        subjects = preset_dict['subjects']
        num_workers = preset_dict.get('workers', num_workers)
    else:
        subjects = [subject.strip() for subject in subjects.split(',')] if subjects else []
    if not subjects:
        raise click.UsageError('subject(s) must be non-empty')
    logger.debug(f'cleaning up for subject(s) {", ".join(subjects)}, num_workers: {num_workers}')
    commands = [cfg.build_cleanup_command(subject) for subject in subjects]
    _run_commands(commands, num_workers=num_workers)
    return 0


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    cli(obj=Config())
