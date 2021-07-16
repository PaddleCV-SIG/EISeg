import os.path as osp
import sys

sys.path.append(osp.dirname(osp.dirname(osp.realpath(__file__))))

from run import main
from util import coco

if __name__ == "__main__":
    main()