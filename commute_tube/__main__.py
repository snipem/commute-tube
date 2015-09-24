from commute_tube import CommuteTube
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    ct = CommuteTube()

    parser.add_argument('-c', action='store_true',
                        help='Check if USB pen is present')
    args = parser.parse_args()

    if (args.c == True):
        ct.checkForPen()
    else:
        ct.main()
