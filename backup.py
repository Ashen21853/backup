#!/usr/bin/python3.7

import sys
import os
import datetime
import ftplib

class backup :

    def __init__ (self, conf_file) :
        """ """
        self.confFile = conf_file

        self.ftpIp  =   None
        self.ftpId  =   None
        self.ftpPw  =   None
        self.ftpRotation = None

        self.logDir =   None
        self.logLevel = None

        self.toSave =   []
    
        self.archive = None

        self.loadConf()

    
    def buildArchive (self, name="/tmp/backup") :
        """ Create an archive with all the file specified in the configuration file
            The archive is in .tar.gz format
        """
        os.mkdir(name)
        for location in self.toSave :
            path = os.path.join(name, location[1:])
            os.makedirs(path)
            os.system("/usr/bin/cp -r " + location + "/* " + path)

        archive = name + datetime.datetime.now().strftime("_%d-%m-%Y_%H-%M-%S") + ".tar.gz"
        
        os.system("/usr/bin/tar -czf "+ archive + " " + name) 

        os.system("/usr/bin/rm -rf "+name)
        self.archive = archive
        return archive


    def fatal (self, msg, ret=-1) :
        """ Print an error message and exit 
        """
        print("[!] FATAL :", msg)
        sys.exit(ret)

    
    def ftpPush (self) :
        """ Connect to the ftp server and upload the archive created previously
        """
        try :
            ftp = ftplib.FTP(self.ftpIp, self.ftpId, self.ftpPw)
            f = open(self.archive, 'rb')
            ftp.storbinary('STOR ' + os.path.split(self.archive)[-1], f)
            f.close()
            os.remove(self.archive)
            ftp.quit()
        except Exception as e :
            self.fatal(e)


    def ftpRotate (self) :
        """ Connect to the ftp server and delete the oldest archive 
            to keep the last N backup
        """
        try :
            ftp = ftplib.FTP(self.ftpIp, self.ftpId, self.ftpPw)
            content = ftp.nlst()
            content.sort()
            toDel = content[:-self.ftpRotation]
            for f in toDel :
                ftp.delete(f)

            ftp.quit()
        except Exception as e :
            self.fatal(e)



    def ftpRestoreLast (self) :
        """ """
        ftp = ftplib.FTP(self.ftpIp, self.ftpId, self.ftpPw)
        backupLast = "/tmp/backupLast.tar.gz"
        last = ftp.nlst()
        last.sort()
        last = last[-1]
        ftp.retrbinary("RETR "+ last, open(backupLast, "wb").write)
        ftp.quit()

        os.system("/usr/bin/tar zxf "+backupLast)
        os.system("/usr/bin/cp -r backup/* /")
        os.system("rm -rf "+ backupLast.split(".tar")[0] + " backup") 




    def loadConf (self) :
        """ """
        f = open(self.confFile)

        for line in f.readlines():
            
            if line[0] == '#':   # its a commentary
                pass
    
            elif line[0] == '@':    # its a file to save
                self.toSave += [line[1:-1]]

            elif line[0] == '$':    # its a option
                cmd = line[1:-1].split("=")
                if len(cmd) != 2:
                    self.fatal("invalid options in :" + cmd[0])
               
                # FTP options
                if cmd[0] == 'ftp.login' :
                    self.ftpId = cmd[1]
                elif cmd[0] == 'ftp.pass' :
                    self.ftpPw = cmd[1]
                elif cmd[0] == 'ftp.ip' :
                    self.ftpIp = cmd[1]
                elif cmd[0] == 'ftp.rotation' :
                    self.ftpRotation = cmd[1]

                # LOG options
                elif cmd[0] == 'log.dir' :
                    self.logDir = cmd[1]
                elif cmd[0] == 'log.level' :
                    self.logLevel = cmd[1]
                else :
                    self.fatal("unknow options in :"+cmd[0])

        f.close()



def ftpBackupUsage (retValue=0) :
    """ """
    print()
    print("Usage :", sys.argv[0], "save | restore | help")
    print()
    print("\tsave\t: save data according with /etc/backup.conf")
    print("\trestore\t: restore the last save done")
    print("\thelp\t: Display this help")
    print()
    sys.exit(0)


if __name__ == '__main__' :
    if len(sys.argv) <= 1 :
        ftpBackupUsage(-1) 

    if sys.argv[1] == 'save' :
        b = backup("/etc/backup.conf")
        b.buildArchive("./backup")
        b.ftpPush()
        b.ftpRotate()

    elif sys.argv[1] == 'restore' :
        b =backup("/etc/backup.conf")
        b.ftpRestoreLast()

    elif sys.argv[1] == 'help' :
        ftpBackupUsage(0)
    
    else :
        ftpBackupUsage(-1)

    sys.exit(0)

