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

#### File copy support
Basic files on your host file system are also supported. Use the `path` element for specifying a file to the USB pen. In order to avoid re copying of already copied files, files are checked for their checksum.

#### Changes to older versions
Both `config.json` and `already_downloaded.txt` are now stored in `$HOME/.config/commutetube/`. Their location can also be changed via command line arguments.

Best Practices
--------------
Here are some best practices listed that I've used on my daily commute ever since creating commute-tube.

### Running a commute-tube once every night ###
For my scenario I've created a [Jenkins](https://jenkins.io/) job that will trigger commute-tube every night at 4 am. The job does also do the following tasks and will upload the log file to an internet resource for me to monitor in case of something went wrong.

Prior to the core job, Jenkins also checks if the USB pen has been plugged in using the `commute_tube --check` command. If not plugged-in, Jenkins will remind me by sending a push notification to my phone.

### Deleting contents of the USB pen ###
Eventually the disk space on your USB pen will run out. In my case I'm using a Windows host system for watching the contents on my pen. I wrote a Windows batch file that moves all the contents of the Download folder of the pen to a sub folder called `delete`.

The nightly routine for starting commute-tube will then delete all the contents of the `delete` folder. This will also keep the files on the pen in case of error or when I forget to plug-in the pen.

### Mount point for USB pen ###
Best way would be to use a FAT32 formatted USB pen. Since there is a good working and hassle free implementation of FAT32 on almost any Unix machine. At first you should create a mount point with `mkdir /mnt/commuteUSB` and after that configure `/etc/fstab`.

In order to do so, extract the UUID of your USB pen and put it into the `/etc/fstab` configuration. The user flag will allow any user to mount and unmount the pen by using `mount /mnt/commuteUSB` or `umount /mnt/commuteUSB` respectively:

```shell
[matze@beatle ~]$ sudo blkid
/dev/sdd1: LABEL="KINGSTON" UUID="25E6-B035" TYPE="vfat" PARTUUID="c3072e18-01"
[matze@beatle ~]$ cat /etc/fstab
UUID=25E6-B035    /mnt/commuteUSB  vfat   user,noauto,rw,umask=000              0  0
```

### Mounting the USB pen ###
Even though commute-tube brings it's own functionality for mounting and unmounting USB pens, I've found this behaviour rather unreliable compared to native `mount mountpoint` and `umount mountpoint` commands of the system. 
