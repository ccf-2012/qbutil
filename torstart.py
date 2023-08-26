import os
import argparse
import psutil
import time
import qbittorrentapi
from cfgdata import ConfigData


# 网络流量低于此阈值时，启动最早暂停的种子（以 KB/s 为单位）
THRESHOLD = 10000


def connect_to_qbittorrent():
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


# 获取暂停的种子列表
def get_paused_torrents(qb):
    return qb.torrents_info(status_filter="paused", sort="added_on")


# 启动种子下载
def start_torrent_download(qb, torrent_hash):
    qb.torrents_resume(torrent_hash)


# 检查网络速度
def calc_network_speed():
    interval = 1
    t0 = time.time()
    upload0 = psutil.net_io_counters().bytes_sent
    download0 = psutil.net_io_counters().bytes_recv
    time.sleep(interval)

    t1 = time.time()
    upload1 = psutil.net_io_counters().bytes_sent
    download1 = psutil.net_io_counters().bytes_recv

    upload_speed = (upload1 - upload0) / (t1 - t0) / 1024
    download_speed = (download1 - download0) / (t1 - t0) / 1024

    return upload_speed


# 监测网络流量逐一启动暂停的种子
def start_paused_torrents():
    while True:
        current_speed = calc_network_speed()
        if current_speed < THRESHOLD:
            try:
                currrent_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                qb = connect_to_qbittorrent()
                paused_torrents = get_paused_torrents(qb)
                print(f"{len(paused_torrents)} torrents in qbit.")
                if paused_torrents:
                    # paused_torrents.sort(key=lambda x: x.added_on)
                    torrent_to_start = paused_torrents[0]
                    start_torrent_download(qb, torrent_to_start.hash)
                    print(f"{currrent_time} 启动种子：{torrent_to_start.name}")
                else:
                    print(f"{currrent_time} 所有种子已经启动。")
                    break
            except Exception as e:
                print(f"连接到 qbittorrent 失败：{str(e)}")
        else:
            print(f"Network busy: {current_speed:.2f} mbps, wait for 3 minutes.")
            time.sleep(180)  # 每分钟检查一次网络流量


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(
        description="start paused torrent one by one when network not busy."
    )
    parser.add_argument("-c", "--config", help="config file.")
    ARGS = parser.parse_args()
    if not ARGS.config:
        ARGS.config = os.path.join(os.path.dirname(__file__), "config.ini")
    else:
        ARGS.config = os.path.expanduser(ARGS.config)


def main():
    loadArgs()
    global CONFIG
    CONFIG = ConfigData()
    CONFIG.readConfig(ARGS.config)

    if CONFIG.qbServer:
        # 启动流量监测并启动种子
        start_paused_torrents()
        print("任务完成。")
    else:
        print("config.ini 没有配置好。")

if __name__ == "__main__":
    main()
