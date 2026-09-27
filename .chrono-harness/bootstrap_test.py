#!/usr/bin/env python3
"""Independent rejection/acceptance checks; never builds the host or redownloads tools."""
import hashlib, importlib.util, io, tarfile, tempfile, unittest, shutil, subprocess
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
if __name__=='__main__':
    unittest.main()
