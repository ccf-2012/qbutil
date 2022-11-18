import argparse
import qbittorrentapi
import urllib.parse
from humanbytes import HumanBytes
from cfgdata import ConfigData
import re


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
        print('There was an error during client.torrents_delete: %s', ex)


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
    print(f'{torrent.hash[:6]}: \033[32m{torrent.name}\033[0m' +
          f' ({HumanBytes.format(torrent.total_size, True)})' +
          f' - \033[31m {abbrevTracker(torrent.tracker)}\033[0m' +
          f'    \033[34m  {trackMessage} \033[0m')


def torSameSize(sizeA, sizeB):
    if sizeA < 50000000:
        return sizeA == sizeB
    elif sizeA < 1000000000:
        return (abs(sizeA - sizeB) < 2000)
    elif sizeA < 50000000000:
        return (abs(sizeA - sizeB) < 10000)
    else:
        return (abs(sizeA - sizeB) < 2000000)


def abbrevTracker(trackerstr):
    hostnameList = urllib.parse.urlparse(trackerstr).netloc.split('.')
    if len(hostnameList) == 2:
        abbrev = hostnameList[0]
    elif len(hostnameList) == 3:
        abbrev = hostnameList[1]
    else:
        abbrev = ''
    return abbrev


def matchTitleNotRegex(torname):
    if ARGS.name_not_regex:
        m0 = re.search(ARGS.name_not_regex, torname, flags=re.A)
        if m0:
            # print('Info regex not match.')
            return True
    return False


def listCrossedTorrents(withoutTrks=[], sizeGt=0):
    qbClient = connQb()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort='total_size')
    matchCount = 0
    # torIndex = 0
    # while torIndex < len(allTorrents):
    #     reseedtor = allTorrents[torIndex]
    #     if reseedtor.total_size < sizeGt:
    #         torIndex += 1
    #         continue

    #     curSize = reseedtor.total_size
    #     reseedList = []
    #     curtor = reseedtor
    #     while (torIndex < len(allTorrents)) and torSameSize(reseedtor.total_size, curSize):
    #         reseedList.append(abbrevTracker(reseedtor.tracker))
    #         torIndex += 1
    #         reseedtor = allTorrents[torIndex] if torIndex < len(allTorrents) else reseedtor

    iterList = iter(allTorrents)
    tor = next(iterList, None)
    while tor and tor.total_size < sizeGt:
        tor = next(iterList, None)

    while tor:
        if matchTitleNotRegex(tor.name):
            tor = next(iterList, None)
            continue

        reseedList = []
        groupSize = tor.total_size
        groupTor = tor
        while tor and torSameSize(tor.total_size, groupSize):
            reseedList.append(abbrevTracker(tor.tracker))
            tor = next(iterList, None)

        if not withoutTrks or (withoutTrks and not [z for z in withoutTrks if z in reseedList]):
            matchCount += 1
            print(f'{matchCount} -------------------')
            printTorrent(groupTor)
            print("    - " + str(reseedList))

    print(f'Total torrents: {len(allTorrents)}')


def deleteCrossedTorrents(matchHash):
    qbClient = connQb()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort='total_size')
    matchCount = 0
    # torIndex = 0
    # while torIndex < len(allTorrents):
    #     reseedtor = allTorrents[torIndex]
    #     curSize = reseedtor.total_size
    #     reseedList = []
    #     while torSameSize(reseedtor.total_size, curSize):
    #         reseedList.append(reseedtor)
    #         torIndex += 1
    #         if torIndex < len(allTorrents):
    #             reseedtor = allTorrents[torIndex]
    #         else:
    #             break
    iterList = iter(allTorrents)
    tor = next(iterList, None)
    while tor:
        groupTorList = []
        groupSize = tor.total_size
        while tor and torSameSize(tor.total_size, groupSize):
            groupTorList.append(tor)
            tor = next(iterList, None)

        if [z for z in groupTorList if z.hash.startswith(matchHash)]:
            for tor in groupTorList:
                printTorrent(tor)
                qbDeleteTorrent(qbClient, tor.hash)
                matchCount += 1

    print(f'Deleted torrents: {matchCount}')


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(description='a qbittorrent utils')
    parser.add_argument('--list',
                        action='store_true',
                        help='list torrents of cross seeding.')
    parser.add_argument('--list-without',
                        help='list torrents without trackers...')
    parser.add_argument('--size-gt',
                        type=int,
                        help='list torrents with size greater than...')
    parser.add_argument('--delete', help='delete reseeding torrents of hash')
    parser.add_argument('--name-not-regex', help='regex to not match the tor name.')
    parser.add_argument('--not-working',
                        action='store_true',
                        help='list torrents of not working.')
    ARGS = parser.parse_args()
    if not ARGS.size_gt:
        ARGS.size_gt = 0
    else:
        ARGS.size_gt = ARGS.size_gt * 1024 * 1024 * 1024


def main():
    loadArgs()

    global CONFIG
    CONFIG = ConfigData()
    CONFIG.readConfig('config.ini')

    if ARGS.list:
        listCrossedTorrents(sizeGt=ARGS.size_gt)
    elif ARGS.list_without:
        argTrks = ARGS.list_without.split(',')
        listCrossedTorrents(withoutTrks=argTrks, sizeGt=ARGS.size_gt)
    elif ARGS.delete:
        deleteCrossedTorrents(ARGS.delete)
    elif ARGS.not_working:
        listQbNotWorking()


if __name__ == '__main__':
    main()
