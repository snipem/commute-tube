commute-tube
============
commute-tube is your friend on your daily commute. It will download videos of your interest to your USB pen by night so that you're able to watch the program in bus or train. It is basically a configurable frontend for "youtube-dl". 

commute-tube is a tool written in Python and should be run in a headless environment such as a server with a USB pen attachted. It will look for your USB pen, automatically mount it, download your configured content and unmount the pen afterwards. Only thing that should be done regulary is to plug in your pen after work and catch it before you begin your commute.


Configuration
-------------
See example `config.json` file.

More to follow.

Mountpoint for USB pen
----------------------
Best way would be to use a FAT32 formatted USB pen. Since there is a good working and hasle free implementation of FAT32 on almost any Unix machine. At first you should create a mountpoint with `mkdir /mnt/commuteUSB` and after that configure `/etc/fstab`.

In order to do so, extract the UUID of your USB pen and put it into the `/etc/fstab` configuration. The user flag will allow any user to mount and unmount the pen by using `mount /mnt/commuteUSB` or `umount /mnt/commuteUSB` respectively:

´´´
[matze@beatle ~]$ sudo blkid 
/dev/sdd1: LABEL="KINGSTON" UUID="25E6-B035" TYPE="vfat" PARTUUID="c3072e18-01" 
[matze@beatle ~]$ cat /etc/fstab 
UUID=25E6-B035    /mnt/commuteUSB  vfat   user,rw,umask=000              0  0
´´´