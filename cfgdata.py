import configparser


class ConfigData():
    interval = 3
    qbServer = ''
    qbPort = ''
    qbUser = ''
    qbPass = ''
    addPause = False
    dryrun = False
    deServer = ''
    dePort = ''
    deUser = ''
    dePass = ''
    
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

        if 'DELUGE' in config:
            self.deServer = config['DELUGE'].get('server_ip', '')
            self.dePort = config['DELUGE'].get('port', '')
            self.deUser = config['DELUGE'].get('user', '')
            self.dePass = config['DELUGE'].get('pass')






