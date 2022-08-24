from argparse import ArgumentParser
from utils.router import route
from utils.parser import parse
from utils import clear_cache

# Settings -- TODO: extract into separate file
COLLECTIONS = ["hmd", "lwm", "jisc", "bna"]
CACHE_HOME = "../.alto2txtcache"
MOUNTPOINT = "../alto2txt"
JISC_PAPERS = "../metadata/fixture-files/JISC papers.csv"
REPORT_DIR = "../alto2txt2fixture-reports"
MAX_ELEMENTS_PER_FILE = int(2e6)
OUTPUT = "./fixtures"


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        "-c",
        "--collections",
        nargs="+",
        help="<Required> Set collections",
        required=False,
    )
    parser.add_argument("-o", "--output", type=str, required=False)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    if args.collections:
        COLLECTIONS = args.collections

    if args.output:
        OUTPUT = args.output.rstrip("/")

    # Routing alto2txt into subdirectories with structured files
    route(COLLECTIONS, CACHE_HOME, MOUNTPOINT, JISC_PAPERS, REPORT_DIR)

    # Parsing the resulting JSON files
    parse(COLLECTIONS, CACHE_HOME, OUTPUT, MAX_ELEMENTS_PER_FILE)

    clear_cache(CACHE_HOME)
