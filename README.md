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

usage: torls.py [-h] [--reseed-without RESEED_WITHOUT] [--reseed-list]
                [--not-working]

a qbittorrent utils

optional arguments:
  -h, --help            show this help message and exit
  --reseed-without RESEED_WITHOUT
                        list torrents without trackers...
  --reseed-list         list torrents of cross seeding.
  --not-working         list torrents of not working.
```

