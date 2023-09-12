import os
import sys
import argparse
import psutil
import time
import qbittorrentapi
import deluge_client
from cfgdata import ConfigData
from loguru import logger

# 网络流量低于此阈值时，启动最早暂停的种子（以 KB/s 为单位）
THRESHOLD = 30000


def getClient(downloader):
    if downloader == 'qb':
        return QBitClient('qb', CONFIG.qbServer, CONFIG.qbPort, CONFIG.qbUser, CONFIG.qbPass)
    if downloader == 'de':
        return DelugeClient('de', CONFIG.deServer, CONFIG.dePort, CONFIG.deUser, CONFIG.dePass)
    

class DownloadClientBase():
    def __init__(self, downloader, host, port, username, password):
        self.downloader = downloader
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        pass
    
    def get_paused_torrents(self):
        pass

class QBitClient(DownloadClientBase):
    def connect(self, ):
        logger.info('Connecting to ' + self.host + ':' + str(self.port))
        self.qbClient = qbittorrentapi.Client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        try:
            self.qbClient.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(e)

        return self.qbClient

    def getFirstPausedTorrentHash(self):
        torlist = self.qbClient.torrents_info(status_filter="paused", sort="added_on")
        if len(torlist) > 0:
            return torlist[0].hash, torlist[0].name
        else: 
            return '', ''

    def startTorrent(self, torrent_hash):
        self.qbClient.torrents_resume(torrent_hash)

class DelugeClient(DownloadClientBase):
    def connect(self):
        if self.downloader != 'de':
            return None

        logger.info('Connecting to ' + self.host + ':' + str(self.port))
        self.deClient = deluge_client.DelugeRPCClient(
            self.host, int(self.port),
            self.username, self.password)
        try:
            self.deClient.connect()
        except:
            logger.warning('Could not create DelugeRPCClient Object...')
            return None
        logger.success('Connected to '+self.host)
        return self.deClient


    def getFirstPausedTorrentHash(self):
        if not self.deClient.connected:
            return ''
        torList = self.deClient.call(
            'core.get_torrents_status', {"state": "Paused"}, [
                'name', 'hash', 'download_location', 'save_path', 'total_size',
                'tracker_host', 'time_added', 'state'
            ])
        firstEle = next(iter(torList.items()), None)
        if firstEle:
            return firstEle[0].decode(), firstEle[1]['name']
        else:
            return '', ''


    def startTorrent(self, tor_hash):
        try:
            st = self.deClient.call('core.get_torrent_status', tor_hash,
                                    ['state'])
            if st[b'state'] == b'Paused':
                self.deClient.call('core.resume_torrent', [tor_hash])
            # else:
                # self.deClient.call('core.pause_torrent', [tor_hash])
        except Exception as ex:
            logger.error(
                'There was an error during core.get_torrent_status: %s', ex)


# 检查网络速度
def calc_network_speed():
    interval = 2
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
    client = getClient('de') if ARGS.deluge else getClient('qb')
    client.connect()
    while True and client:
        current_speed = calc_network_speed()
        if current_speed < THRESHOLD:
            try:
                currrent_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                paused_torrent_hash, paused_torrent_name = client.getFirstPausedTorrentHash()
                if paused_torrent_hash:
                    client.startTorrent(paused_torrent_hash)
                    logger.success(f"{currrent_time} 启动种子：{paused_torrent_name}")
                    time.sleep(10)
                else:
                    logger.success(f"{currrent_time} 所有种子已经启动。")
                    break
            except Exception as e:
                logger.error(f"连接到 Client 失败：{str(e)}")
        else:
            logger.info(f"Network busy: {current_speed/1000:.2f} mbps, wait for 3 minutes.")
            time.sleep(180)  # 每3分钟检查一次网络流量


def loadArgs():
    global ARGS
    parser = argparse.ArgumentParser(
        description="start paused torrent one by one when network not busy."
    )
    parser.add_argument("-c", "--config", help="config file.")
    parser.add_argument("-d", "--deluge", action='store_true', help="deluge.")
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

    if CONFIG.qbServer or CONFIG.deServer:
        # 启动流量监测并启动种子
        start_paused_torrents()
        print("任务完成。")
    else:
        print("config.ini 没有配置好。")

if __name__ == "__main__":
    logger.remove()
    formatstr = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | - <level>{message}</level>"
    logger.add(sys.stdout, format=formatstr)
    main()
