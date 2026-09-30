#!/usr/bin/env python3
"""Install pinned harness tools and SDKs from the selected explicit host profile."""
import argparse, base64, hashlib, io, json, os, platform, shutil, subprocess, sys, tarfile, urllib.request
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

def selection(cfg, requested):
    """Validate explicit profile references before performing installation effects."""
    if cfg['schema'] != 'chrono-example-sdk/v2':
        raise ValueError('E_BOOTSTRAP_PROFILE: unsupported bootstrap schema')
    downloads = {}
    for item in cfg['downloads']:
        key = item.get('id')
        if not isinstance(key, str) or not key or key in downloads:
            raise ValueError('E_BOOTSTRAP_PROFILE: invalid or duplicate download ID')
        downloads[key] = item
    profiles = cfg['profiles']
    if not isinstance(profiles, dict) or not profiles or cfg['default_profile'] not in profiles:
        raise ValueError('E_BOOTSTRAP_PROFILE: missing default profile')
    for key, profile in profiles.items():
        if not key or set(profile) != {'downloads', 'probes'}:
            raise ValueError('E_BOOTSTRAP_PROFILE: invalid profile fields')
        for field, registered in [('downloads', downloads), ('probes', cfg['probes'])]:
            names = profile[field]
            if (not isinstance(names, list) or any(not isinstance(name, str) for name in names)
                    or len(set(names)) != len(names) or any(name not in registered for name in names)):
                raise ValueError('E_BOOTSTRAP_PROFILE: unknown or duplicate '+field+' reference')
    name = requested if requested is not None else cfg['default_profile']
    if name not in profiles:
        raise ValueError('E_BOOTSTRAP_PROFILE: unknown profile '+name)
    profile = profiles[name]
    return name, [downloads[key] for key in profile['downloads']], {key: cfg['probes'][key] for key in profile['probes']}

def observe_probe(root, argv):
    """Observe only an explicitly selected command; never update expected identities."""
    if not isinstance(argv,list) or not argv or any(not isinstance(arg,str) for arg in argv) or not argv[0]:
        raise ValueError('invalid registered probe argv')
    if '/' in argv[0]:
        selected=root/argv[0]
    else:
        selected=next((root/entry/argv[0] for entry in os.get_exec_path()
                       if (root/entry/argv[0]).is_file() and os.access(root/entry/argv[0],os.X_OK)),None)
        if selected is None:
            raise ValueError('registered probe executable missing: '+argv[0])
    program=selected.resolve(strict=True)
    before=hashlib.sha256(program.read_bytes()).hexdigest()
    child=subprocess.run([str(selected),*argv[1:]],cwd=root,capture_output=True)
    errors=[]
    after=None
    try:
        after=hashlib.sha256(program.read_bytes()).hexdigest()
        if selected.resolve(strict=True)!=program or before!=after:
            errors.append('executable changed')
    except OSError as error:
        errors.append('executable identity unavailable: '+str(error))
    if child.returncode:
        errors.append('probe exit '+str(child.returncode))
    streams={}
    for key,data in [('stdout',child.stdout),('stderr',child.stderr)]:
        streams[key+'_base64']=base64.b64encode(data).decode('ascii')
        streams[key+'_sha256']=hashlib.sha256(data).hexdigest()
        try:
            streams[key]=data.decode('utf-8')
        except UnicodeDecodeError:
            streams[key]=None
            errors.append('non-UTF-8 '+key)
    return {'scope':'executable-and-version-only','requested_argv':argv,
            'argv':[str(selected),*argv[1:]],'path':str(selected),'resolved_path':str(program),'sha256':before,
            'after_sha256':after,'exit_code':child.returncode,**streams,
            'status':'failed' if errors else 'passed','errors':errors}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=Path)
    parser.add_argument('--profile')
    args = parser.parse_args()
    root = args.host.resolve()
    cfg = json.loads((root / '.chrono-harness/bootstrap.json').read_text())
    profile, downloads, probes = selection(cfg, args.profile)
    subprocess.run([sys.executable, str(root / '.chrono-harness/install.py'), str(root)], check=True)
    distribution = json.loads((root / '.chrono-harness/state/distribution.json').read_text())
    state = root / '.chrono-harness/state'
    cache_root = root / '.chrono-harness/cache'
    state.mkdir(parents=True, exist_ok=True)
    installed = []
    platform_id = platform.system().lower()+'-'+platform.machine().lower()
    for item in downloads:
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
    report={'profile':profile,'downloads':[item['id'] for item in downloads],
            'release_version':distribution['version'],'source_revision':distribution['source_commit'],
            'versions':{},'tools':{},'status':'failed','harness_installed':distribution['installed'],
            'installed':[{'path':str(dst.relative_to(root)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()} for _,dst in installed]}
    try:
        for key, argv in probes.items():
            observed=observe_probe(root,argv)
            report['tools'][key]=observed
            if observed['status']!='passed':
                raise ValueError('registered probe failed: '+key+': '+', '.join(observed['errors']))
            report['versions'][key]=observed['stdout'].strip()
        report['status']='passed'
    finally:
        (state / 'bootstrap-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['versions']))

if __name__ == '__main__':
    main()
