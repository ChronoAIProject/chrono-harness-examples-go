#!/usr/bin/env python3
"""Independent rejection/acceptance checks; never builds the host or redownloads tools."""
import json, sys, hashlib, importlib.util, io, tarfile, tempfile, unittest, shutil, subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('bootstrap',Path(__file__).with_name('bootstrap.py'))
bootstrap=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
class Distribution(unittest.TestCase):
    def test_instruction_projection_matches_registered_sources(self):
        root=Path(__file__).resolve().parent.parent
        sources=['.chrono-harness/instructions/catalog.json','.chrono-harness/instructions/manifest.json','.chrono-harness/instructions/host-context.md','CLAUDE.md']
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)
            for name in sources:
                destination=target/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(root/name,destination)
            (target/'AGENTS.md').symlink_to('CLAUDE.md')
            subprocess.run([str(root/'.chrono-harness/bin/chrono-instructions'),'generate','--host-root',str(target)],check=True,capture_output=True)
            self.assertEqual((target/'CLAUDE.md').read_bytes(),(root/'CLAUDE.md').read_bytes())
            self.assertEqual((root/'AGENTS.md').readlink(),Path('CLAUDE.md'))
    def test_exact_digest_accepts_and_corruption_rejects(self):
        data=b'pinned SDK bytes'
        digest='sha256-'+hashlib.sha256(data).hexdigest()
        self.assertEqual(bootstrap.verified(data,digest),data)
        with self.assertRaisesRegex(ValueError,'integrity mismatch'):
            bootstrap.verified(data+b'changed',digest)
    def test_paths_preserved_and_escape_rejected(self):
        for name, permitted in [('different/layout.txt',True),('../escape',False)]:
            buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
                entry=tarfile.TarInfo(name); entry.size=3
                archive.addfile(entry,io.BytesIO(b'yes'))
            with tempfile.TemporaryDirectory() as d:
                if permitted:
                    bootstrap.unpack(buffer.getvalue(),Path(d))
                    self.assertEqual((Path(d)/name).read_bytes(),b'yes')
                else:
                    with self.assertRaisesRegex(ValueError,'unsupported archive member'):
                        bootstrap.unpack(buffer.getvalue(),Path(d))
    def run_profile(self, config, root):
        config_path=root/'.chrono-harness/bootstrap.json'
        config_path.write_text(json.dumps(config))
        return subprocess.run([sys.executable,str(Path(__file__).with_name('bootstrap.py')),str(root),'--profile','unit'],capture_output=True,text=True)
    def fixture(self, root):
        (root/'.chrono-harness').mkdir()
        (root/'.chrono-harness/install.py').write_text('from pathlib import Path\nimport json,sys\nr=Path(sys.argv[1]);s=r/".chrono-harness/state";s.mkdir();(s/"installer-ran").touch();(s/"distribution.json").write_text(json.dumps({"version":"fixture", "source_commit":"fixed", "installed":[]}))\n')
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
            entry=tarfile.TarInfo('sdk/input');entry.size=3
            archive.addfile(entry,io.BytesIO(b'yes'))
        data=buffer.getvalue();archive=root/'sdk.tgz';archive.write_bytes(data)
        return {'schema':'chrono-example-sdk/v2','default_profile':'all','downloads':[{'id':'needed','directory':'.chrono-harness/cache/needed','variants':{'any':{'url':archive.as_uri(),'integrity':'sha256-'+hashlib.sha256(data).hexdigest()}}},{'id':'unrelated','directory':'.chrono-harness/cache/unrelated','variants':{'any':{'url':(root/'must-not-download').as_uri(),'integrity':'sha256-'+'0'*64}}}],'probes':{'selected':[sys.executable,'-c','print("selected-sdk")'],'unrelated':[str(root/'must-not-run')]},'profiles':{'all':{'downloads':['needed','unrelated'],'probes':['selected','unrelated']},'unit':{'downloads':['needed'],'probes':['selected']}}}
    def test_profile_installs_only_explicit_sdk_and_probe(self):
        with tempfile.TemporaryDirectory(prefix='unit SDK 中文 ') as d:
            root=Path(d);cfg=self.fixture(root);p=self.run_profile(cfg,root)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual((root/'.chrono-harness/cache/needed/sdk/input').read_bytes(),b'yes')
            self.assertFalse((root/'.chrono-harness/cache/unrelated').exists())
            report=json.loads((root/'.chrono-harness/state/bootstrap-result.json').read_text())
            self.assertEqual(report['profile'],'unit')
            self.assertEqual(report['downloads'],['needed'])
            self.assertEqual(report['versions'],{'selected':'selected-sdk'})
    def test_profile_invalid_references_fail_before_installation(self):
        for case in ['unknown-profile','missing-download','missing-probe','duplicate-selection','duplicate-download']:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                root=Path(d);cfg=self.fixture(root)
                if case=='unknown-profile':del cfg['profiles']['unit']
                elif case=='missing-download':cfg['profiles']['unit']['downloads']=['absent']
                elif case=='missing-probe':cfg['profiles']['unit']['probes']=['absent']
                elif case=='duplicate-selection':cfg['profiles']['unit']['downloads']=['needed','needed']
                else:cfg['downloads'].append(cfg['downloads'][0])
                p=self.run_profile(cfg,root)
                self.assertNotEqual(p.returncode,0)
                self.assertIn('E_BOOTSTRAP_PROFILE',p.stderr)
                self.assertFalse((root/'.chrono-harness/state/installer-ran').exists())

if __name__=='__main__':
    unittest.main()
