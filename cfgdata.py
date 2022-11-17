import configparser


class configData():
    interval = 3
    qbServer = ''
    qbPort = ''
    qbUser = ''
    qbPass = ''
    addPause = False
    dryrun = False
    
    def readConfig(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)

        if 'QBIT' in config:
            self.qbServer = config['QBIT'].get('server_ip', '')
            self.qbPort = config['QBIT'].get('port', '')
            self.qbUser = config['QBIT'].get('user', '')
            self.qbPass = config['QBIT'].get('pass')

            self.addPause = config['QBIT'].getboolean('pause', False)
            self.dryrun = config['QBIT'].getboolean('dryrun', False)


CONFIG = configData()
CONFIG.readConfig('config.ini')



