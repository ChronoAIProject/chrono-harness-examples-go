#!/usr/bin/env python3
"""验证宿主 SDK 选择、安装转交和原探测结果；外部命令全部在执行边界模拟。"""
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).with_name('bootstrap.py'))
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class Distribution(unittest.TestCase):
    def probe_file(self, root, name='selected-probe'):
        path = root / name
        path.write_bytes(b'fixture executable bytes\n')
        return path

    def test_probe_retains_executable_identity_and_original_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            program = self.probe_file(root)
            argv = [str(program), '--version']
            result = subprocess.CompletedProcess(argv, 17, b'version\n', b'failure\n')
            with mock.patch.object(bootstrap.subprocess, 'run', return_value=result) as run:
                observed = bootstrap.observe_probe(root, argv)
            run.assert_called_once_with(argv, cwd=root, capture_output=True)
            self.assertEqual(observed['exit_code'], 17)
            self.assertEqual(observed['stdout'], 'version\n')
            self.assertEqual(observed['stderr'], 'failure\n')
            self.assertEqual(observed['sha256'], hashlib.sha256(program.read_bytes()).hexdigest())
            self.assertEqual(observed['stdout_sha256'], hashlib.sha256(b'version\n').hexdigest())
            self.assertEqual(observed['status'], 'failed')

    def test_probe_detects_mutation_without_losing_child_result(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            program = self.probe_file(root, 'version tool')
            def boundary(argv, **kwargs):
                program.write_bytes(b'changed fixture bytes\n')
                return subprocess.CompletedProcess(argv, 17, b'original', b'')
            with mock.patch.object(bootstrap.subprocess, 'run', side_effect=boundary):
                observed = bootstrap.observe_probe(root, ['./version tool'])
            self.assertEqual(observed['exit_code'], 17)
            self.assertEqual(observed['stdout'], 'original')
            self.assertNotEqual(observed['sha256'], observed['after_sha256'])
            self.assertIn('executable changed', observed['errors'])

    def test_probe_preserves_registered_alias_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            program = self.probe_file(root, 'actual-tool')
            alias = root / 'registered-alias'
            alias.symlink_to(program.name)
            result = subprocess.CompletedProcess([str(alias)], 0, str(alias).encode(), b'')
            with mock.patch.object(bootstrap.subprocess, 'run', return_value=result) as run:
                observed = bootstrap.observe_probe(root, ['./registered-alias'])
            run.assert_called_once_with([str(alias)], cwd=root, capture_output=True)
            self.assertEqual(observed['stdout'], str(alias))
            self.assertEqual(observed['resolved_path'], str(program.resolve()))

    def test_probe_alias_loop_keeps_the_completed_child_result(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            program = self.probe_file(root, 'actual-tool')
            alias = root / 'registered-alias'
            alias.symlink_to(program.name)
            def boundary(argv, **kwargs):
                alias.unlink()
                alias.symlink_to(alias.name)
                return subprocess.CompletedProcess(argv, 17, b'original', b'')
            with mock.patch.object(bootstrap.subprocess, 'run', side_effect=boundary):
                observed = bootstrap.observe_probe(root, ['./registered-alias'])
            self.assertEqual(observed['status'], 'failed')
            self.assertEqual(observed['exit_code'], 17)
            self.assertEqual(observed['stdout'], 'original')
            self.assertTrue(any('executable identity unavailable' in e for e in observed['errors']))

    def fixture(self, root):
        (root / '.chrono-harness').mkdir()
        (root / '.chrono-harness/install.sh').write_bytes(b'installer fixture; never executed\n')
        self.probe_file(root)
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            entry = tarfile.TarInfo('sdk/input')
            entry.size = 3
            archive.addfile(entry, io.BytesIO(b'yes'))
        data = buffer.getvalue()
        archive = root / 'sdk.tgz'
        archive.write_bytes(data)
        return {
            'schema': 'chrono-example-sdk/v2', 'default_profile': 'all',
            'downloads': [
                {'id': 'needed', 'directory': '.chrono-harness/cache/needed',
                 'variants': {'any': {'url': archive.as_uri(), 'integrity': 'sha256-' + hashlib.sha256(data).hexdigest()}}},
                {'id': 'unrelated', 'directory': '.chrono-harness/cache/unrelated',
                 'variants': {'any': {'url': (root / 'must-not-download').as_uri(), 'integrity': 'sha256-' + '0' * 64}}},
            ],
            'probes': {'selected': [str(root / 'selected-probe')], 'unrelated': [str(root / 'must-not-run')]},
            'profiles': {
                'all': {'downloads': ['needed', 'unrelated'], 'probes': ['selected', 'unrelated']},
                'unit': {'downloads': ['needed'], 'probes': ['selected']},
            },
        }

    def run_profile(self, config, root, probe=(0, b'selected-sdk\n', b''), installer_failure=None):
        root = root.resolve()
        (root / '.chrono-harness/bootstrap.json').write_text(json.dumps(config))
        installer = ['/bin/sh', str(root / '.chrono-harness/install.sh'), '--host-root', str(root)]
        def boundary(argv, **kwargs):
            if argv == installer:
                self.assertEqual(kwargs, {'check': True})
                if installer_failure is not None:
                    raise installer_failure
                state = root / '.chrono-harness/state'
                state.mkdir()
                (state / 'installer-ran').touch()
                (state / 'distribution.json').write_text(json.dumps({
                    'version': 'fixture', 'source_commit': 'fixed', 'installed': [],
                }))
                return subprocess.CompletedProcess(argv, 0)
            self.assertEqual(argv, config['probes']['selected'])
            self.assertEqual(kwargs, {'cwd': root, 'capture_output': True})
            return subprocess.CompletedProcess(argv, *probe)
        argv = ['bootstrap.py', str(root), '--profile', 'unit']
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(
            bootstrap.subprocess, 'run', side_effect=boundary
        ) as run, contextlib.redirect_stdout(io.StringIO()):
            bootstrap.main()
            return run.call_args_list

    def test_profile_installs_only_explicit_sdk_and_probe(self):
        with tempfile.TemporaryDirectory(prefix='unit SDK 中文 ') as d:
            root = Path(d)
            calls = self.run_profile(self.fixture(root), root)
            self.assertEqual(len(calls), 2)
            self.assertEqual((root / '.chrono-harness/cache/needed/sdk/input').read_bytes(), b'yes')
            self.assertFalse((root / '.chrono-harness/cache/unrelated').exists())
            report = json.loads((root / '.chrono-harness/state/bootstrap-result.json').read_text())
            self.assertEqual(report['profile'], 'unit')
            self.assertEqual(report['downloads'], ['needed'])
            self.assertEqual(report['versions'], {'selected': 'selected-sdk'})
            self.assertEqual(report['status'], 'passed')
            self.assertEqual(set(report['tools']), {'selected'})

    def test_installer_failure_preserves_exception_before_sdk_effects(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            config = self.fixture(root)
            failure = subprocess.CalledProcessError(17, 'installer', b'original', b'diagnostic')
            with self.assertRaises(subprocess.CalledProcessError) as caught:
                self.run_profile(config, root, installer_failure=failure)
            self.assertIs(caught.exception, failure)
            self.assertEqual(caught.exception.returncode, 17)
            self.assertEqual(caught.exception.output, b'original')
            self.assertEqual(caught.exception.stderr, b'diagnostic')
            self.assertFalse((root / '.chrono-harness/cache').exists())

    def test_profile_failure_publishes_original_probe_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            config = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'registered probe failed'):
                self.run_profile(config, root, probe=(17, b'original\n', b'diagnostic\n'))
            report = json.loads((root / '.chrono-harness/state/bootstrap-result.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertEqual(report['tools']['selected']['exit_code'], 17)
            self.assertEqual(report['tools']['selected']['stdout'], 'original\n')
            self.assertEqual(report['tools']['selected']['stderr'], 'diagnostic\n')
            self.assertEqual(report['versions'], {})

    def test_profile_invalid_references_fail_before_installation(self):
        for case in ['unknown-profile', 'missing-download', 'missing-probe', 'duplicate-selection', 'duplicate-download']:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                config = self.fixture(root)
                if case == 'unknown-profile':
                    del config['profiles']['unit']
                elif case == 'missing-download':
                    config['profiles']['unit']['downloads'] = ['absent']
                elif case == 'missing-probe':
                    config['profiles']['unit']['probes'] = ['absent']
                elif case == 'duplicate-selection':
                    config['profiles']['unit']['downloads'] = ['needed', 'needed']
                else:
                    config['downloads'].append(config['downloads'][0])
                with self.assertRaisesRegex(ValueError, 'E_BOOTSTRAP_PROFILE'):
                    self.run_profile(config, root)
                self.assertFalse((root / '.chrono-harness/state/installer-ran').exists())

    def test_exact_digest_accepts_and_corruption_rejects(self):
        data = b'pinned SDK bytes'
        digest = 'sha256-' + hashlib.sha256(data).hexdigest()
        self.assertEqual(bootstrap.verified(data, digest), data)
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            bootstrap.verified(data + b'changed', digest)

    def test_paths_preserved_and_escape_rejected(self):
        for name, permitted in [('different/layout.txt', True), ('../escape', False)]:
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
                entry = tarfile.TarInfo(name)
                entry.size = 3
                archive.addfile(entry, io.BytesIO(b'yes'))
            with tempfile.TemporaryDirectory() as d:
                if permitted:
                    bootstrap.unpack(buffer.getvalue(), Path(d))
                    self.assertEqual((Path(d) / name).read_bytes(), b'yes')
                else:
                    with self.assertRaisesRegex(ValueError, 'unsupported archive member'):
                        bootstrap.unpack(buffer.getvalue(), Path(d))


if __name__ == '__main__':
    unittest.main()
