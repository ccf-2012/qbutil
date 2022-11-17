# torls 
qbittorrent utility to list torrents with reseeding.

purpose of this script, in Chinese:
* `--seed-without` 看看哪些种子还没 发/辅 在 mmtbits 站上
* `--delete` 删除一个种子和它的所有辅种
* `--not-working` 看看哪些种子 `未工作`，并在qbit中打上标签


## Install 
```sh
git clone https://github.com/ccf-2012/qbutil.git
cd qbutil
pip install -r requirements.txt
```

## Write a config.ini

* 填写 `config.ini` 信息
```sh 
cp config-sample.ini config.ini
vi config.ini
```

* 参考注释和示例，编写其中的各项信息：
```ini
[QBIT]
server_ip=192.168.5.199
port=8091
user=MyQbitUsername
pass=MyQbitPassword
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

