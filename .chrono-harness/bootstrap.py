#!/usr/bin/env python3
"""Install explicitly pinned tool distributions; host projects are never inspected."""
import argparse, base64, hashlib, io, json, os, platform, shutil, subprocess, tarfile, urllib.request
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
    parser.add_argument('--local-product', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    root = args.host.resolve()
    cfg = json.loads((root / '.chrono-harness/bootstrap.json').read_text())
    if cfg['schema'] != 'chrono-example-bootstrap/v1':
        raise ValueError('unsupported bootstrap configuration')
    data = verified((root / cfg['distribution']['path']).read_bytes(), cfg['distribution']['integrity'])
    if args.verify_only:
        print('distribution digest verified; no installation or host checks executed')
        return
    state = root / '.chrono-harness/state'
    cache_root = root / '.chrono-harness/cache'
    state.mkdir(parents=True, exist_ok=True)
    if args.local_product:
        source = args.local_product.resolve()
        oid = subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        dirt = subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=source)
        if oid != cfg['distribution']['revision'] or dirt:
            raise ValueError('local product must be the exact clean pinned revision')
    else:
        source = cache_root / 'product-source' / cfg['distribution']['revision']
        unpack(data, source)
    env = dict(os.environ, RUSTUP_TOOLCHAIN=cfg['rust_toolchain'])
    if subprocess.run(['rustup','run',cfg['rust_toolchain'],'rustc','--version'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
        subprocess.run(['rustup','toolchain','install',cfg['rust_toolchain'],'--profile','minimal'],check=True)
    installed = []
    for item in cfg['builds']:
        subprocess.run(['cargo','build','--locked','--manifest-path',str(source / item['manifest'])],env=env,check=True)
        installed.append((source / item['binary'], root / item['install']))
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
    (state / 'bootstrap-result.json').write_text(json.dumps({'source_revision':cfg['distribution']['revision'],'versions':versions,'installed':[{'path':str(dst.relative_to(root)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()} for _,dst in installed]},indent=2)+'\n')
    print(json.dumps(versions))

if __name__ == '__main__':
    main()
