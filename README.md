# torls 
qbit工具，用于查看辅种情况，以及删除种子时删除所有辅种

主要功能
* `--tag-tracker` 对种子按tracker打上标签，其中 `未工作` 也会单独标签
* `--edit-tracker` 批量修改 tracker
* `--cross-with`, `--cross-without` 列出在某站 有/无 辅种的种子，可以加`--seeds-gt` `--size-gt` 等条件，可加 `--delete` 对之删除


## 安装  
```sh
git clone https://github.com/ccf-2012/qbutil.git
cd qbutil
pip install -r requirements.txt
```

##  填写 `config.ini` 信息
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

## 使用
```
python torls.py -h

usage: torls.py [-h] [-c CONFIG] [--list] [--dryrun] [--cross-without CROSS_WITHOUT] [--cross-with CROSS_WITH] [--seed-min-gt SEED_MIN_GT]
                [--seed-avg-gt SEED_AVG_GT] [--size-gt SIZE_GT] [--days-gt DAYS_GT] [--delete] [--del-by-hash DEL_BY_HASH]
                [--name-not-regex NAME_NOT_REGEX] [--not-working] [--tag-tracker] [--site SITE] [--edit-tracker EDIT_TRACKER]

a qbittorrent utils

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file.
  --list                list torrents of cross seeding.
  --dryrun              test only, print the msg without delete.
  --cross-without CROSS_WITHOUT
                        list torrents without trackers...
  --cross-with CROSS_WITH
                        list torrents with trackers...
  --seed-min-gt SEED_MIN_GT
                        list torrents with seednum greater than...
  --seed-avg-gt SEED_AVG_GT
                        list torrents with seednum greater than...
  --size-gt SIZE_GT     list torrents with size greater than...
  --days-gt DAYS_GT     list torrents with size greater than...
  --delete              delete listed torrents of cross seeding.
  --del-by-hash DEL_BY_HASH
                        delete reseeding torrents by hash
  --name-not-regex NAME_NOT_REGEX
                        regex to not match the tor name.
  --not-working         list torrents of not working.
  --tag-tracker         tag torrents tracker.
  --site SITE           the pt site to edit.
  --edit-tracker EDIT_TRACKER
                        edit tracker.
```

## 给 qb 种子加站点标签
```sh
# 给qb中种子加 站点 和 未工作 标签
python3 torls.py --tag-tracker

```

## 查找种子
```sh
# 列出所有辅种的种子分组
python3 torls.py --list

# 列出没有在trackbits 辅种的种子
python3 torls.py --cross-without trackbits

# 列出大于 20G， 且没有在trackbits,mmtbits 辅种
python3 torls.py --cross-without trackbits,mmtbits  --size-gt 20

# 列出大于 20G， 且没有在trackbits,mmtbits 辅种, 且种子名中不包含 cfandora的
python3 torls.py --cross-without trackbits,mmtbits  --size-gt 20 --name-not-regex cfandora
```


## 删除种子及其辅种
* 例子中的 `--dryrun` 表示仅打印信息，并不真正删种，确认后去掉再运行
```sh

# 删除没在 pptbits 作种的种子
python3 torls.py --cross-without pptbits --delete --dryrun

# 删除在 mmtbits 有辅种，但没在 pptbits 辅种的种子，所有站添加时间大于90天的
python3 torls.py --cross-with mmtbits --cross-without pptbits --days-gt 90 --delete --dryrun

# 删除在 mmtbits 有辅种，但没在 pptbits 辅种的种子，所有站最小作种人数大于 2
python3 torls.py --cross-with mmtbits --cross-without pptbits --seed-min-gt 2 --delete --dryrun

# 删除在 mmtbits 有辅种，但没在 pptbits 辅种的种子，平均作种人数大于 1 (所有站除我外还有人在作种)
python3 torls.py --cross-with mmtbits --cross-without pptbits --seed-avg-gt 1 --delete --dryrun


# 删除hash为 156c96 开头的种子和所有辅种
python3 torls.py --del-by-hash  156c96

```

## 批量修改种子 tracker
```sh
# 修改一个站的tracker
python3 torls.py --site ptsite --edit-tracker 'https://tracker.site.pt/announce.php?passkey=your_passkey_in_control_panel

```

-----

# torstart
```
python torstart.py -h
usage: torstart.py [-h] [-c CONFIG] [-d]

start paused torrent one by one when network not busy.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file.
  -d, --deluge          deluge.
  ```

