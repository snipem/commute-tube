commute-tube
============
commute-tube is your friend on your daily commute. It will download videos of your interest to your USB pen by night so that you're able to watch the program in bus or train. It is basically a configurable front end for "youtube-dl".

commute-tube is a tool written in Python and should be run in a headless environment such as a server with a USB pen attached. It will look for your USB pen, automatically mount it, download your configured content and unmount the pen afterwards. Only thing that should be done regularly is to plug in your pen after work and catch it before you begin your commute.


Configuration
-------------
See example `config.json` file.

### Pen section
In the pen section you may declare basic settings such as `penPath` (path to your pen), `mountAndUnmount` (if the path in `penPath` shall be mounted for every run) and `downloadFolder` (the path where files are going be downloaded inside your `penPath`).

### Source section
The source section contains all the various sources you want to download from.  Besides `description` which contains a description of the source and `shellscript` all the parameters are basic youtube-dl options. See the [youtube-dl implementation](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py) for a detailed overview over the parameters available and how to set them.

#### Shell script support
In addition to the basic youtube-dl it is possible to set the value `shellscript` which invokes a shell script or command that you specify and takes the output one line at a time for youtube-dl as input. This is helpful if you want to parse a video source that is not yet supported by youtube-dl.

Mount point for USB pen
----------------------
Best way would be to use a FAT32 formatted USB pen. Since there is a good working and hassle free implementation of FAT32 on almost any Unix machine. At first you should create a mount point with `mkdir /mnt/commuteUSB` and after that configure `/etc/fstab`.

In order to do so, extract the UUID of your USB pen and put it into the `/etc/fstab` configuration. The user flag will allow any user to mount and unmount the pen by using `mount /mnt/commuteUSB` or `umount /mnt/commuteUSB` respectively:

```shell
[matze@beatle ~]$ sudo blkid
/dev/sdd1: LABEL="KINGSTON" UUID="25E6-B035" TYPE="vfat" PARTUUID="c3072e18-01"
[matze@beatle ~]$ cat /etc/fstab
UUID=25E6-B035    /mnt/commuteUSB  vfat   user,noauto,rw,umask=000              0  0
```
