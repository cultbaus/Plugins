import json
import os
from time import time
from sys import argv
from os.path import getmtime
from zipfile import ZipFile
from argparse import ArgumentParser

DOWNLOAD_URL = 'https://github.com/{repo}/raw/main/plugins/{plugin_name}/latest.zip'
ICON_URL = 'https://github.com/{repo}/raw/main/plugins/{plugin_name}/images/icon.png'

DEFAULTS = {
    'IsHide': False,
    'IsTestingExclusive': False,
    'ApplicableVersion': 'any',
}

DUPLICATES = {
    'DownloadLinkInstall': ['DownloadLinkTesting', 'DownloadLinkUpdate'],
}

TRIMMED_KEYS = [
    'Author',
    'Name',
    'Description',
    'InternalName',
    'AssemblyVersion',
    'RepoUrl',
    'ApplicableVersion',
    'Tags',
    'DalamudApiLevel',
]

def main():
    parser = ArgumentParser("create_json")
    parser.add_argument("--repo", "-repo", default="cultbaus/Plugins")
    parser.add_argument("--file_name", "-f", help="File to read/write to", default="repo.json")
    args = parser.parse_args()
    # extract the manifests from inside the zip files
    master = extract_manifests()

    # trim the manifests
    master = [trim_manifest(manifest) for manifest in master]

    # convert the list of manifests into a master list
    add_extra_fields(args.repo, master)

    # write the master
    write_master(args.file_name, master)

    # update the LastUpdated field in master
    last_updated(args.file_name)

def extract_manifests():
    manifests = []

    for dirpath, dirnames, filenames in os.walk('./plugins'):
        if len(filenames) == 0 or 'latest.zip' not in filenames:
            continue
        plugin_name = dirpath.split('/')[-1]
        latest_zip = f'{dirpath}/latest.zip'
        with ZipFile(latest_zip) as z:
            manifest = json.loads(z.read(f'{plugin_name}.json').decode('utf-8'))
            manifests.append(manifest)

    return manifests

def add_extra_fields(repo_name, manifests):
    for manifest in manifests:
        # generate the download link from the internal assembly name
        manifest['DownloadLinkInstall'] = DOWNLOAD_URL.format(repo=repo_name, plugin_name=manifest["InternalName"])
        manifest['IconUrl'] = ICON_URL.format(repo=repo_name, plugin_name=manifest["InternalName"])
        # add default values if missing
        for k, v in DEFAULTS.items():
            if k not in manifest:
                manifest[k] = v
        # duplicate keys as specified in DUPLICATES
        for source, keys in DUPLICATES.items():
            for k in keys:
                if k not in manifest:
                    manifest[k] = manifest[source]
        manifest['DownloadCount'] = 0

def write_master(file_name, master):
    # write as pretty json
    with open(file_name, 'w') as f:
        json.dump(master, f, indent=4)

def trim_manifest(plugin):
    return {k: plugin[k] for k in TRIMMED_KEYS if k in plugin}

def last_updated(file_name):
    with open(file_name) as f:
        master = json.load(f)

    for plugin in master:
        latest = f'plugins/{plugin["InternalName"]}/latest.zip'
        modified = int(getmtime(latest))

        if 'LastUpdated' not in plugin or modified != int(plugin['LastUpdated']):
            plugin['LastUpdated'] = str(modified)

    with open(file_name, 'w') as f:
        json.dump(master, f, indent=4)

if __name__ == '__main__':
    main()
