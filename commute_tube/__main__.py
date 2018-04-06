from .commute_tube import CommuteTube
import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--check', '-c', action='store_true',
                        help='Check if USB pen is present')
    parser.add_argument('--config', default='config.json', 
                        help="Path to config file")
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
