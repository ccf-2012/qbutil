# torls 
qbittorrent utility to list torrents with reseeding.


## Install 
```sh
git clone https://github.com/ccf-2012/qbutil.git
cd qbutil
pip install -r requirements.txt
```

## Usage
```
python torls.py -h

usage: torls.py [-h] [--seed-without SEED_WITHOUT] [--delete DELETE]
                [--seed-list] [--not-working]

a qbittorrent utils

optional arguments:
  -h, --help            show this help message and exit
  --seed-without SEED_WITHOUT
                        list torrents without trackers...
  --delete DELETE       delete reseeding torrents of hash
  --seed-list           list torrents of cross seeding.
  --not-working         list torrents of not working.
```

