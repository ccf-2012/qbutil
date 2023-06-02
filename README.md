# torls 
qbit工具，用于查看辅种情况，以及删除种子时删除所有辅种

主要功能
* `--list-without` 看看哪些种子还没辅(或发)在 mmtbits 站
* `--delete` 删除一个种子和它的所有辅种
* `--not-working` 看看哪些种子 `未工作`，并在qbit中打上标签
* `--tag-tracker` 对种子按tracker打上标签，其中 `未工作` 也会单独标签
* `--edit-tracker` 修改 tracker


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

usage: torls.py [-h] [-C CONFIG] [--list] [--list-without LIST_WITHOUT] [--size-gt SIZE_GT] [--delete DELETE] [--name-not-regex NAME_NOT_REGEX] [--not-working] [--tag-tracker]
                [--site SITE] [--edit-tracker EDIT_TRACKER]

a qbittorrent utils

optional arguments:
  -h, --help            show this help message and exit
  -C CONFIG, --config CONFIG
                        config file.
  --list                list torrents of cross seeding.
  --list-without LIST_WITHOUT
                        list torrents without trackers...
  --size-gt SIZE_GT     list torrents with size greater than...
  --delete DELETE       delete reseeding torrents of hash
  --name-not-regex NAME_NOT_REGEX
                        regex to not match the tor name.
  --not-working         list torrents of not working.
  --tag-tracker         tag torrents tracker.
  --site SITE           the pt site to edit.
  --edit-tracker EDIT_TRACKER
                        edit tracker.
```

## 例子
```sh
# 列出所有作种的组
python3 torls.py --list

# 列出没有在trackbits 辅种的种子
python3 torls.py --list-without trackbits

# 列出大于 20G， 且没有在trackbits,mmtbits 辅种
python3 torls.py --list-without trackbits,mmtbits  --size-gt 20

# 列出大于 20G， 且没有在trackbits,mmtbits 辅种, 且种子名中不包含 cfandora的
python3 torls.py --list-without trackbits,mmtbits  --size-gt 20 --name-not-regex cfandora

# 删除hash为 156c96 开头的种子和所有辅种
python3 torls.py --delete  156c96

# 给qb中种子加 站点 和 未工作 标签
python3 torls.py --tag-tracker

# 修改一个站的tracker
python3 torls.py --site piggo --edit-tracker 'https://tracker.piggo.me/announce.php?passkey=your_passkey_in_control_panel

```
