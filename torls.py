import argparse
import qbittorrentapi
import urllib.parse
from humanbytes import HumanBytes
from cfgdata import CONFIG


def connQb():
    qbClient = qbittorrentapi.Client(host=CONFIG.qbServer,
                                     port=CONFIG.qbPort,
                                     username=CONFIG.qbUser,
                                     password=CONFIG.qbPass)
    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)

    return qbClient


def addQbitWithTag(downlink, imdbtag):
    qbClient = connQb()
    if not qbClient:
        return False

    try:
        # curr_added_on = time.time()
        result = qbClient.torrents_add(
            urls=downlink,
            is_paused=CONFIG.addPause,
            # save_path=download_location,
            # download_path=download_location,
            # category=timestamp,
            tags=[imdbtag],
            use_auto_torrent_management=False)
        # breakpoint()
        if 'OK' in result.upper():
            print('Torrent added.')
        else:
            print('Torrent not added! something wrong with qb api ...')
    except Exception as e:
        print('Torrent not added! Exception: ' + str(e))
        return False

    return True


def listQbNotWorking():
    qbClient = connQb()
    if not qbClient:
        return False

    count = 0
    for torrent in qbClient.torrents_info(sort='name'):
        # breakpoint()
        # 这里偷懒了，多tracker情况这里就不对了，用者自行想办法了
        tr3 = torrent.trackers[3]

        # 列出tracker 未工作
        if tr3['status'] == 4:
            count += 1
            printTorrent(torrent, tr3["msg"])
            torrent.addTags(['未工作'])
        else:
            torrent.removeTags(['未工作'])

    print(f'Total: {count}')


def printTorrent(torrent, trackMessage=''):
    print(
        f'{torrent.hash[-6:]}: \033[32m{torrent.name}\033[0m ({HumanBytes.format(torrent.total_size, True)})'
    )
    if trackMessage:
        print(f'\033[31m {abbrevTracker(torrent.tracker)}\033[0m    \033[34m  {trackMessage} \033[0m')
    else:
        print(f'\033[31m {abbrevTracker(torrent.tracker)}\033[0m')


def abbrevTracker(trackerstr):
    hostnameList = urllib.parse.urlparse(trackerstr).netloc.split('.')
    if len(hostnameList) == 2:
        abbrev = hostnameList[0]
    elif len(hostnameList) == 3:
        abbrev = hostnameList[1]
    else:
        abbrev = ''
    return abbrev


def listReseed(without=''):
    qbClient = connQb()
    if not qbClient:
        return False

    count = 0
    alltorrents = qbClient.torrents_info(sort='total_size')
    i = 0
    count = 0
    while i < len(alltorrents):
        cursize = alltorrents[i].total_size
        reseedtor = alltorrents[i]
        count += 1
        reseedList = []
        while reseedtor and reseedtor.total_size == cursize:
            trk = abbrevTracker(reseedtor.tracker)
            if trk: reseedList.append(trk)
            i += 1
            if i >= len(alltorrents): break
            reseedtor = alltorrents[i]
        if not without or (without and without not in reseedList):
            print(f'{count} -------------------')
            printTorrent(reseedtor)
            print(reseedList)
    print(f'Total: {i}')


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(description='a qbittorrent utils')
    parser.add_argument('--reseed-list',
                        action='store_true',
                        help='list reseed torrents.')
    parser.add_argument('--not-working',
                        action='store_true',
                        help='list torrents not working.')
    ARGS = parser.parse_args()


def main():
    loadArgs()
    if ARGS.reseed_list:
        listReseed('chdbits')
        pass
    elif ARGS.not_working:
        listQbNotWorking()


if __name__ == '__main__':
    main()
