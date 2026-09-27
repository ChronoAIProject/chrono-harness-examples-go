#!/usr/bin/env python3
"""Install the pinned harness release, then the explicitly registered host SDKs."""
import argparse, base64, hashlib, io, json, platform, shutil, subprocess, sys, tarfile, urllib.request
from pathlib import Path

def verified(data, integrity):
    algorithm, expected = integrity.split('-', 1)
    if algorithm not in ('sha256', 'sha512'):
        raise ValueError('unsupported digest')
    actual = hashlib.new(algorithm, data).digest()
    matches = actual.hex() == expected if algorithm == 'sha256' else base64.b64encode(actual).decode() == expected
    if not matches:
        raise ValueError('distribution integrity mismatch')
    return data

def unpack(data, target):
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError('unsupported archive member: '+member.name)
            if member.issym():
                resolved = (target / path.parent / member.linkname).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise ValueError('archive link escapes distribution')
        archive.extractall(target)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=Path)
    args = parser.parse_args()
    root = args.host.resolve()
    cfg = json.loads((root / '.chrono-harness/bootstrap.json').read_text())
    if cfg['schema'] != 'chrono-example-sdk/v1':
        raise ValueError('unsupported bootstrap configuration')
    subprocess.run([sys.executable, str(root / '.chrono-harness/install.py'), str(root)], check=True)
    distribution = json.loads((root / '.chrono-harness/state/distribution.json').read_text())
    state = root / '.chrono-harness/state'
    cache_root = root / '.chrono-harness/cache'
    state.mkdir(parents=True, exist_ok=True)
    installed = []
    platform_id = platform.system().lower()+'-'+platform.machine().lower()
    for item in cfg['downloads']:
        variant = item['variants'].get(platform_id) or item['variants'].get('any')
        if not variant:
            raise ValueError('undeclared tool platform: '+platform_id)
        cache = cache_root / 'downloads' / variant['integrity'].replace('/', '_').replace('+', '_')
        cache.parent.mkdir(parents=True,exist_ok=True)
        data = cache.read_bytes() if cache.exists() else urllib.request.urlopen(variant['url'],timeout=120).read()
        verified(data, variant['integrity'])
        if not cache.exists():
            cache.write_bytes(data)
        unpack(data, root / item['directory'])
        for source_path, destination in variant.get('install', []):
            installed.append((root / item['directory'] / source_path, root / destination))
    for source_path, destination in installed:
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source_path,destination)
    versions = {}
    for key, argv in cfg['probes'].items():
        versions[key] = subprocess.check_output(argv,cwd=root,text=True).strip()
    (state / 'bootstrap-result.json').write_text(json.dumps({'release_version':distribution['version'],'source_revision':distribution['source_commit'],'versions':versions,'harness_installed':distribution['installed'],'installed':[{'path':str(dst.relative_to(root)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()} for _,dst in installed]},indent=2)+'\n')
    print(json.dumps(versions))

if __name__ == '__main__':
    main()
