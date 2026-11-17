"""Fetch upstream public model files, verifying pinned GitHub release digests.
No inference API or paid service. Model files stay out of Git.
"""
import argparse,hashlib,json,os,tempfile
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
def fetch(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    for item in json.loads((ROOT/'assets/voice-models.json').read_text()):
        target=directory/item['file']
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256']:continue
        with tempfile.NamedTemporaryFile(dir=directory,delete=False) as temp:
            pending=Path(temp.name)
            try:
                with urlopen(item['url'],timeout=120) as response:
                    while block:=response.read(1024*1024):temp.write(block)
                temp.flush()
                if hashlib.sha256(pending.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Upstream model checksum mismatch: '+item['file'])
                pending.replace(target)
            finally:
                if pending.exists():pending.unlink()
        print('Verified public model:',item['file'])
    return directory
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=ROOT/'.cache/voice');args=p.parse_args();fetch(args.directory)
