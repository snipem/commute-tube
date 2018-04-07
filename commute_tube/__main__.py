from .commute_tube import CommuteTube
import argparse
import os

def main():
    parser = argparse.ArgumentParser()

    default_config = os.path.expanduser('~/.config/commutetube/config.json')
    default_download_archive = os.path.expanduser('~/.config/commutetube/already_downloaded.txt')

    parser.add_argument('--check', '-c', action='store_true',
                        help='Check if USB pen is present')
    parser.add_argument('--debug', action='store_true', 
                        help="For testing, doesn't download anything")
    parser.add_argument('--config', 
                        default=default_config,
                        help="Path to config file. Default is %s" % (default_config))
    parser.add_argument('--download-archive', 
                        default=default_download_archive,
                        help="Path to download archive. Default is %s" % (default_download_archive))
    parser.add_argument('--filter', default=None, 
                        help="Filter source by regexp")

    args = parser.parse_args()
    
    ct = CommuteTube(args)

    if (args.check):
        ct.check_for_pen()
    else:
        ct.main()

if __name__ == "__main__":
    main()
