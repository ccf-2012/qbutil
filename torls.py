import argparse
import qbittorrentapi
import urllib.parse
from humanbytes import HumanBytes
from cfgdata import ConfigData
import os
import time
import re


def qbConnect():
    qbClient = qbittorrentapi.Client(
        host=CONFIG.qbServer,
        port=CONFIG.qbPort,
        username=CONFIG.qbUser,
        password=CONFIG.qbPass,
    )
    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)

    return qbClient


def qbAddWithTag(downlink, imdbtag):
    qbClient = qbConnect()
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
            use_auto_torrent_management=False,
        )
        # breakpoint()
        if "OK" in result.upper():
            print("Torrent added.")
        else:
            print("Torrent not added! something wrong with qb api ...")
    except Exception as e:
        print("Torrent not added! Exception: " + str(e))
        return False

    return True


def qbDeleteTorrent(qbClient, tor_hash):
    try:
        qbClient.torrents_delete(True, torrent_hashes=tor_hash)
    except Exception as ex:
        print("There was an error during client.torrents_delete: %s", ex)


NOT_WORKING_STATUS = 4


def allTrackersNotWorking(trackers):
    return all(
        tracker["status"] == NOT_WORKING_STATUS
        for tracker in trackers
        if tracker["status"] > 0
    )


def listQbNotWorking():
    qbClient = qbConnect()
    if not qbClient:
        return False

    countNotWorking = 0
    for torrent in qbClient.torrents_info(sort="name"):
        if allTrackersNotWorking(torrent.trackers):
            countNotWorking += 1
            printTorrent(torrent)
            torrent.addTags(["未工作"])
        else:
            torrent.removeTags(["未工作"])

    print(f"Total not working: {countNotWorking}")


def tagTracker():
    qbClient = qbConnect()
    if not qbClient:
        return False

    countAll = 0
    countNotWorking = 0
    for torrent in qbClient.torrents_info(sort="name"):
        checkContentExits(torrent)
        countAll += 1
        if allTrackersNotWorking(torrent.trackers):
            countNotWorking += 1
            printTorrent(torrent)
            torrent.addTags(["未工作"])
        else:
            torrent.removeTags()
            printTorrent(torrent)
            torrent.addTags([abbrevTracker(torrent.tracker)])

    print(f"Total torrents: {countAll}, not working: {countNotWorking}")


def getTorrentFirstTracker(torrent):
    noneTracker = {"url": "", "msg": ""}
    firstTracker = next(
        (tracker for tracker in torrent.trackers if tracker["status"] > 0), noneTracker
    )
    return firstTracker


def printTorrent(torrent):
    firstTracker = getTorrentFirstTracker(torrent)
    print(
        f"{torrent.hash[:6]}: \033[32m{torrent.name}\033[0m"
        + f" ({HumanBytes.format(torrent.total_size, True)})"
        + f' - \033[31m {abbrevTracker(firstTracker["url"])}\033[0m'
        + f'    \033[34m  {firstTracker["msg"]} \033[0m'
    )


def torSameSize(sizeA, sizeB):
    if sizeA < 50000000:   # < 50M
        return sizeA == sizeB
    elif sizeA < 5000000000:  # < 5G, diff < 2K
        return abs(sizeA - sizeB) < 2000   
    elif sizeA < 50000000000:  # 5G <-> 50G, diff < 1M
        return abs(sizeA - sizeB) < 1000000 
    else:  # > 50G, diff < 2M
        return abs(sizeA - sizeB) < 3000000 


def abbrevTracker(trackerstr):
    hostnameList = urllib.parse.urlparse(trackerstr).netloc.split(".")
    if len(hostnameList) == 2:
        abbrev = hostnameList[0]
    elif len(hostnameList) == 3:
        abbrev = hostnameList[1]
    else:
        abbrev = ""
    return abbrev


def matchTitleNotRegex(torname):
    if ARGS.name_not_regex:
        m0 = re.search(ARGS.name_not_regex, torname, flags=re.A)
        if m0:
            # print('Info regex not match.')
            return True
    return False


def editTorrentsTracker(trackerAbrev, newTrackerUrl):
    qbClient = qbConnect()
    if not qbClient:
        return False
    allTorrents = qbClient.torrents_info(sort="total_size")
    print(f"Total torrents: {len(allTorrents)}")
    for tor in allTorrents:
        if abbrevTracker(tor.tracker) == trackerAbrev:
            printTorrent(tor)
            firstTracker = next(
                (tracker for tracker in tor.trackers if tracker["status"] > 0), None
            )
            tor.edit_tracker(firstTracker["url"], newTrackerUrl)


def compare_seednum(item):
    return item["num_complete"]


def checkContentExits(tor):
    contentExists = os.path.exists(os.path.join(tor["save_path"], tor["name"]))
    if not contentExists:
        tor.pause()
        tor.addTags(["文件丢失"])
    return contentExists


def listCrossedTorrents(withTrks=[], withoutTrks=[]):
    qbClient = qbConnect()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort="total_size")
    matchGroupCount = 0
    matchTorCount = 0
    matchSize = 0
    iterList = iter(allTorrents)
    tor = next(iterList, None)
    if ARGS.size_gt:
        while tor and tor.total_size < ARGS.size_gt:
            tor = next(iterList, None)

    while tor:
        if ARGS.name_not_regex:
            while tor and re.search(ARGS.name_not_regex, tor.name, flags=re.A):
                tor = next(iterList, None)

        # find cross-seed torrents by same size
        reseedList = []
        groupSize = tor.total_size
        groupTor = tor
        while tor and torSameSize(tor.total_size, groupSize):
            reseedList.append(tor)
            tor = next(iterList, None)

        if len(reseedList) > 0:
            reseedSitenameList = [ abbrevTracker(getTorrentFirstTracker(x)["url"]) for x in reseedList ]
            if (
                not withTrks
                or (withTrks and all(x in reseedSitenameList for x in withTrks))
            ) and (
                not withoutTrks
                or (
                    withoutTrks
                    and all(y not in reseedSitenameList for y in withoutTrks)
                )
            ):
                match_args = True
                min_seednum = min(reseedList, key=compare_seednum)['num_complete']
                sum_seednum = sum(item["num_complete"] for item in reseedList)
                avg_seednum = sum_seednum / len(reseedList)
                min_seed_time = min(item["completion_on"] for item in reseedList if item["completion_on"])
                days = (time.time() - min_seed_time) / 86400

                if ARGS.seed_min_gt and (min_seednum < ARGS.seed_min_gt):
                    match_args = False
                if ARGS.seed_avg_gt and avg_seednum < ARGS.seed_avg_gt:
                    match_args = False
                if ARGS.days_gt and days < ARGS.days_gt:
                    match_args = False

                if match_args:
                    matchGroupCount += 1
                    matchTorCount += len(reseedList)
                    matchSize += groupSize
                    if ARGS.delete:
                        # delCrossedTorrentsByHash(groupTor["hash"])
                        for deltor in reseedList:
                            firstTracker = getTorrentFirstTracker(deltor)
                            print(f'Deleting : {abbrevTracker(firstTracker["url"]):15}  - {deltor["name"]} ({HumanBytes.format(deltor["size"], True)})')
                            if not ARGS.dryrun:
                                qbDeleteTorrent(qbClient, deltor['hash'])
                    else:
                        print(f"{matchGroupCount} -------------------")
                        printTorrent(groupTor)
                        # print(f'added {days:.1f} days ago: {groupTor["name"]} ({HumanBytes.format(groupTor["size"], True)})')
                        print( f"sum seednum: {sum_seednum}, average seednum: {avg_seednum:.2f} min seednum: {min_seednum:.2f}, added {days:.1f} days ago " )

                        print("    - " + str(reseedSitenameList))

        # else:
        #     print(f'Not match ===========')

    print(
        f"Total: {len(allTorrents)}, matched: {matchTorCount}, {matchGroupCount} cross, {HumanBytes.format(matchSize, True)}"
    )


def delCrossedTorrentsByHash(matchHash):
    qbClient = qbConnect()
    if not qbClient:
        return False

    allTorrents = qbClient.torrents_info(sort="total_size")
    matchCount = 0

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
                print("xxx Deleting... xxx ")
                printTorrent(tor)
                if not ARGS.dryrun:
                    qbDeleteTorrent(qbClient, tor.hash)
                matchCount += 1

    print(f"Deleted torrents: {matchCount}")


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(description="a qbittorrent utils")
    parser.add_argument("-c", "--config", help="config file.")
    parser.add_argument(
        "--list", action="store_true", help="list torrents of cross seeding."
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="test only, print the msg without delete."
    )
    parser.add_argument("--cross-without", help="list torrents without trackers...")
    parser.add_argument("--cross-with", help="list torrents with trackers...")
    parser.add_argument(
        "--seed-min-gt", type=int, help="list torrents with seednum greater than..."
    )
    parser.add_argument(
        "--seed-avg-gt", type=int, help="list torrents with seednum greater than..."
    )
    parser.add_argument(
        "--size-gt", type=int, help="list torrents with size greater than..."
    )
    parser.add_argument(
        "--days-gt", type=int, help="list torrents with size greater than..."
    )
    parser.add_argument(
        "--delete", action="store_true", help="delete listed torrents of cross seeding."
    )
    parser.add_argument("--del-by-hash", help="delete reseeding torrents by hash")
    parser.add_argument("--name-not-regex", help="regex to not match the tor name.")
    parser.add_argument(
        "--not-working", action="store_true", help="list torrents of not working."
    )
    parser.add_argument(
        "--tag-tracker", action="store_true", help="tag torrents tracker."
    )
    parser.add_argument("--site", help="the pt site to edit.")
    parser.add_argument("--edit-tracker", help="edit tracker.")
    ARGS = parser.parse_args()
    if not ARGS.size_gt:
        ARGS.size_gt = 0
    else:
        ARGS.size_gt = ARGS.size_gt * 1024 * 1024 * 1024
    if not ARGS.config:
        ARGS.config = os.path.join(os.path.dirname(__file__), "config.ini")


def main():
    loadArgs()

    global CONFIG
    CONFIG = ConfigData()
    CONFIG.readConfig(ARGS.config)

    if ARGS.list:
        listCrossedTorrents()
    elif ARGS.cross_without or ARGS.cross_with or ARGS.seed_avg_gt or ARGS.days_gt:
        argWithoutTrks = ARGS.cross_without.split(",") if ARGS.cross_without else []
        argWithTrks = ARGS.cross_with.split(",") if ARGS.cross_with else []
        listCrossedTorrents(withTrks=argWithTrks, withoutTrks=argWithoutTrks)
    elif ARGS.del_by_hash:
        delCrossedTorrentsByHash(ARGS.del_by_hash)
    elif ARGS.not_working:
        listQbNotWorking()
    elif ARGS.tag_tracker:
        tagTracker()
    elif ARGS.edit_tracker:
        siteAbrev = ARGS.site
        editTorrentsTracker(trackerAbrev=siteAbrev, newTrackerUrl=ARGS.edit_tracker)


if __name__ == "__main__":
    main()
