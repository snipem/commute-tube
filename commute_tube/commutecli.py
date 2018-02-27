from commute_tube import CommuteTube
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--check', '-c', action='store_true',
                    help='Check if USB pen is present')
parser.add_argument('--config', default='config.json', help="Path to config file")
args = parser.parse_args()

ct = CommuteTube(args.config)

if (args.check):
    ct.check_for_pen()
else:
    ct.main()
