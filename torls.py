import argparse
import qbittorrentapi
import urllib.parse
from humanbytes import HumanBytes
from cfgdata import ConfigData


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


def qbAddWithTag(downlink, imdbtag):
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


def qbDeleteTorrent(qbClient, tor_hash):
    try:
        qbClient.torrents_delete(True, torrent_hashes=tor_hash)
    except Exception as ex:
        print(
            'There was an error during client.torrents_delete: %s', ex)


def listQbNotWorking():
    qbClient = connQb()
    if not qbClient:
        return False

    countNotWorking = 0
    for torrent in qbClient.torrents_info(sort='name'):
        # breakpoint()
        # 这里偷懒了，多tracker情况这里就不对了，用者自行想办法了
        tr3 = torrent.trackers[3]

        # 列出tracker 未工作
        if tr3['status'] == 4:
            countNotWorking += 1
            printTorrent(torrent, tr3["msg"])
            torrent.addTags(['未工作'])
        else:
            torrent.removeTags(['未工作'])

    print(f'Total not working: {countNotWorking}')


def printTorrent(torrent, trackMessage=''):
    print(
        f'{torrent.hash[:6]}: \033[32m{torrent.name}\033[0m' +
        f' ({HumanBytes.format(torrent.total_size, True)})' +
        f' - \033[31m {abbrevTracker(torrent.tracker)}\033[0m' +
        f'    \033[34m  {trackMessage} \033[0m'
    )


def abbrevTracker(trackerstr):
    hostnameList = urllib.parse.urlparse(trackerstr).netloc.split('.')
    if len(hostnameList) == 2:
        abbrev = hostnameList[0]
    elif len(hostnameList) == 3:
        abbrev = hostnameList[1]
    else:
        abbrev = ''
    return abbrev


def listCrossedTorrents(withoutTrks=[]):
    qbClient = connQb()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort='total_size')
    torIndex = 0
    matchCount = 0
    while torIndex < len(allTorrents):
        reseedtor = allTorrents[torIndex]
        curSize = reseedtor.total_size
        reseedList = []
        curtor = reseedtor
        while reseedtor.total_size == curSize:
            trackname = abbrevTracker(reseedtor.tracker)
            if trackname:
                reseedList.append(trackname)
            torIndex += 1
            if torIndex < len(allTorrents):
                reseedtor = allTorrents[torIndex]
            else:
                break
        if not withoutTrks or (withoutTrks and not [z for z in withoutTrks if z in reseedList]):
            matchCount += 1
            print(f'{matchCount} -------------------')
            printTorrent(curtor)
            print("    - " + str(reseedList))

    print(f'Total torrents: {len(allTorrents)}')


def deleteCrossedTorrents(matchHash):
    qbClient = connQb()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort='total_size')
    torIndex = 0
    matchCount = 0
    while torIndex < len(allTorrents):
        reseedtor = allTorrents[torIndex]
        curSize = reseedtor.total_size
        reseedList = []
        while reseedtor.total_size == curSize:
            reseedList.append(reseedtor)
            torIndex += 1
            if torIndex < len(allTorrents):
                reseedtor = allTorrents[torIndex]
            else:
                break
        if [z for z in reseedList if z.hash.startswith(matchHash)]:
            for tor in reseedList:
                printTorrent(tor)
                qbDeleteTorrent(tor.hash)
                matchCount += 1

    print(f'Deleted torrents: {matchCount}')


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(description='a qbittorrent utils')
    parser.add_argument('--seed-without', help='list torrents without trackers...')
    parser.add_argument('--delete', help='delete reseeding torrents of hash')
    parser.add_argument('--seed-list',
                        action='store_true',
                        help='list torrents of cross seeding.')
    parser.add_argument('--not-working',
                        action='store_true',
                        help='list torrents of not working.')
    ARGS = parser.parse_args()


def main():
    loadArgs()

    global CONFIG
    CONFIG = ConfigData()
    CONFIG.readConfig('config.ini')

    if ARGS.seed_list:
        listCrossedTorrents()
    elif ARGS.seed_without:
        argTrks = ARGS.seed_without.split(',')
        listCrossedTorrents(withoutTrks=argTrks)
    elif ARGS.delete:
        deleteCrossedTorrents(ARGS.delete)
    elif ARGS.not_working:
        listQbNotWorking()


if __name__ == '__main__':
    main()
