from pathlib import Path
from colorama import Fore, Style
from numpy import array_split
from pandas import read_csv

import datetime
import json
import pytz
import re


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


###### SETTINGS ########################################################
# ALTO2TXT_MNT: where to find containers for alto2txt metadata
# COLLECTIONS: a list of all the collections to process in our scripts
# OVERWRITE_CACHE: if set to True, drops all the lockfiles before processing a collection. (default: False)
# WRITE_FIXTURES: If set to True, writes the fixtures to the disk. (default: True)
# SKIP_FILE_SIZE: Zip files over this size (in GB) will be skipped in processing. (default: 1.5)
# CHUNK_THRESHOLD: Any list of zip files will be chunked up by this size. (default: 115)
# JISC_PAPERS_CSV:
# TEMP_OUTPUT:
# START_WITH_LARGEST:
# CACHE:
# FIXTURE:
# WRITE_LOCKFILES:

settings = dotdict(
    **{
        "ALTO2TXT_MNT": "../cache-alto2txt",
        "COLLECTIONS": ["jisc", "hmd", "lwm"],
        "OVERWRITE_CACHE": False,
        "WRITE_FIXTURES": True,
        "SKIP_FILE_SIZE": 1.5,
        "CHUNK_THRESHOLD": 1,  #
        "JISC_PAPERS_CSV": "./fixture-files/JISC papers.csv",
        "CACHE": dotdict(
            **{
                "newspaper": "../cache-newspaper",
                "item": "../cache-item",
                "metatable": "../cache-metatables",
            }
        ),
        "TEMP_OUTPUT": "../cache-fixture-ready",
        "FIXTURE": dotdict(
            **{
                "DataProvider": "../newspapers/fixtures/DataProvider-fixtures.json",
                "Digitisation": "../newspapers/fixtures/Digitisation-fixtures.json",
                "Ingest": "../newspapers/fixtures/Ingest-fixtures.json",
                "Issue": "../newspapers/fixtures/Issue-fixtures.json",
                "Newspaper": "../newspapers/fixtures/Newspaper-fixtures.json",
                "Item": lambda collection: f"../newspapers/fixtures/Items-{collection}-fixtures.json",
            }
        ),
        "START_WITH_LARGEST": False,
        "WRITE_LOCKFILES": False,  # True
    }
)

# correct settings to adhere to standards
settings.SKIP_FILE_SIZE *= 1e9

PUBLICATION_CODE = re.compile(r"\d{7}")


def get_now(as_str=False):
    now = datetime.datetime.now(tz=pytz.UTC)
    if as_str:
        return str(now)
    return now


NOW_str = get_now(True)


def success(msg):
    print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")


def info(msg):
    print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")


def warning(msg):
    print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")


def get_key(x=dict(), on=[]):
    """See create_lookup"""
    return f"{'-'.join([str(x['fields'][y]) for y in on])}"


def create_lookup(lst=[], on=[]):
    return {get_key(x, on): x["pk"] for x in lst}


def get_path_from(p):
    """Guarantees that p is set to Path"""
    """TODO: This function also exists in alto2txt2fixture. Consolidate."""
    if isinstance(p, str):
        p = Path(p)

    if not isinstance(p, Path):
        raise RuntimeError(f"Unable to handle type: {type(p)}")

    return p


def get_size_from_path(p, raw=False):
    """Returns a nice string for any given file size. Accepts a string or a Path as first argument."""
    """TODO: This function also exists in alto2txt2fixture. Consolidate."""

    p = get_path_from(p)

    bytes = p.stat().st_size
    if raw:
        return bytes

    rel_size = round(bytes / 1000 / 1000 / 1000, 1)

    if rel_size < 0.5:
        rel_size = round(bytes / 1000 / 1000, 1)
        rel_size = f"{rel_size}MB"
    else:
        rel_size = f"{rel_size}GB"

    return rel_size


def load_json(p, crash=False):
    """
    Easier access to reading JSON files.
    Accepts a string or Path as first argument.
    Returns the decoded JSON contents from the path.
    Returns an empty dictionary if file cannot be decoded and crash is set to False.
    """

    p = get_path_from(p)

    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        msg = f"Error: {p.read_text()}"
        if crash:
            raise RuntimeError(msg)
        else:
            print(msg)
            return {}


def list_json_files(p, drill=False, exclude_names=[], include_names=[]):
    """
    Easily access a list of all JSON files in a directory.
    Accepts a string or Path as first argument.
    Returns a list of JSON files.

    If drill is set to True, it will return any JSON files in child directories as well (i.e. recursive).
    If exclude_names or include_names are lists with values, the returned list will be filtered by either
        inclusive with include_names or exclusive on exclude_names.
    """

    q = "**/*.json" if drill else "*.json"
    files = get_path_from(p).glob(q)

    if exclude_names:
        return list({x for x in files if not x.name in exclude_names})
    elif include_names:
        return list({x for x in files if x.name in include_names})

    return files


def load_multiple_json(p, drill=False, filter_na=True, crash=False):
    """
    Easier loading of a bunch of JSON files.
    Accepts a string or Path as first argument.
    Returns a list of the decoded contents from the path.

    If drill is set to True, it will return any JSON files in child directories as well (i.e. recursive).
    If filter_na is set to True, it will filter out any empty elements.
    """

    files = list_json_files(p, drill=drill)
    content = [load_json(x, crash=crash) for x in files]
    return [x for x in content if x] if filter_na else content


def write_json(p, o, add_created=True):
    """
    Easier access to writing JSON files.
    Checks whether parent exists.
    Accepts a string or Path as first argument, and a dictionary as the second argument.
    The add_created argument will add created_at and updated_at to the dictionary's fields.
    (If created_at and updated_at already exist in the fields, they will be forcefully updated.)
    """

    _append_created_fields = lambda o: dict(
        **{k: v for k, v in o.items() if not k == "fields"},
        fields=dict(
            **{
                k: v
                for k, v in o["fields"].items()
                if not k == "created_at" and not k == "updated_at"
            },
            **{"created_at": NOW_str, "updated_at": NOW_str},
        ),
    )

    p = get_path_from(p)

    if not (isinstance(o, dict) or isinstance(o, list)):
        raise RuntimeError(f"Unable to handle data of type: {type(o)}")

    try:
        if add_created and isinstance(o, dict):
            o = _append_created_fields(o)
        elif add_created and isinstance(o, list):
            o = [_append_created_fields(x) for x in o]
    except KeyError:
        print(o)
        exit()

    p.parent.mkdir(parents=True, exist_ok=True)

    return p.write_text(json.dumps(o))


"""glob_filter is a macOS assistance that filters out any pesky, unwanted .DS_Store for instance"""
glob_filter = lambda p: [
    x for x in get_path_from(p).glob("*") if not x.name.startswith(".")
]


def lock(lockfile):
    """Writes a '.' to a lockfile, after making sure the parent directory exists."""
    lockfile.parent.mkdir(parents=True, exist_ok=True)
    lockfile.write_text("")


def get_lockfile(collection, kind, dic):
    """
    Provides the path to any given lockfile, which controls whether any existing files should be overwritten or not.
    Arguments passed:
        `kind`: either "newspaper" or "issue" or "item"
        `dic`: a dictionary with required information for either `kind` passed
    """
    base = Path(f"cache-lockfiles/{collection}")

    if kind == "newspaper":
        p = base / f"newspapers/{dic['publication_code']}"
    elif kind == "issue":
        p = base / f"issues/{dic['publication__publication_code']}/{dic['issue_code']}"
    elif kind == "item":
        try:
            if dic.get("issue_code"):
                p = base / f"items/{dic['issue_code']}/{dic['item_code']}"
            elif dic.get("issue__issue_identifier"):
                p = base / f"items/{dic['issue__issue_identifier']}/{dic['item_code']}"
        except KeyError:
            print()
            print()
            print()
            print()
            print(dic)
            print()
            print()
            print()
            print()
            exit()
    else:
        p = base / "lockfile"

    p.parent.mkdir(parents=True, exist_ok=True) if settings.WRITE_LOCKFILES else None

    return p


def get_chunked_zipfiles(path):
    zipfiles = sorted(
        path.glob("*.zip"),
        key=lambda x: x.stat().st_size,
        reverse=settings.START_WITH_LARGEST,
    )
    zipfiles = [x for x in zipfiles if x.stat().st_size <= settings.SKIP_FILE_SIZE]

    if len(zipfiles) > settings.CHUNK_THRESHOLD:
        chunks = array_split(zipfiles, len(zipfiles) / settings.CHUNK_THRESHOLD)
    else:
        chunks = [zipfiles]

    return chunks


def setup_jisc_papers(path=settings.JISC_PAPERS_CSV):
    """
    Creates a DataFrame with correct informations based on the JISC_PAPERS_CSV from the settings.

    Returns: DataFrame with all JISC titles.
    """

    if not Path(path).exists():
        raise RuntimeError(
            f"Could not find required JISC papers file. Put {Path(path).name} in {Path(path).parent} or correct the settings with a different path."
        )

    months = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "June": 6,
        "Jul": 7,
        "July": 7,
        "Aug": 8,
        "Sep": 9,
        "Sept": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
        "Dec.": 12,
    }

    jisc_papers = read_csv(
        path,
        usecols=[
            "Newspaper Title",
            "NLP",
            "Abbr",
            "StartD",
            "StartM",
            "StartY",
            "EndD",
            "EndM",
            "EndY",
        ],
    )
    jisc_papers["start_date"] = jisc_papers.apply(
        lambda x: datetime.datetime(
            year=int(x.StartY),
            month=months[x.StartM.strip(".").strip()],
            day=int(x.StartD),
        ),
        axis=1,
    )
    jisc_papers["end_date"] = jisc_papers.apply(
        lambda x: datetime.datetime(
            year=int(x.EndY), month=months[x.EndM.strip(".").strip()], day=int(x.EndD)
        ),
        axis=1,
    )
    jisc_papers.drop(
        ["StartD", "StartM", "StartY", "EndD", "EndM", "EndY"],
        axis="columns",
        inplace=True,
    )
    jisc_papers.rename(
        {"Newspaper Title": "title", "NLP": "publication_code", "Abbr": "abbr"},
        axis=1,
        inplace=True,
    )
    jisc_papers["title"] = jisc_papers["title"].apply(
        lambda x: "The " + x[:-5] if x.strip()[-5:].lower() == ", the" else x
    )
    jisc_papers["publication_code"] = jisc_papers["publication_code"].apply(
        lambda x: str(x).zfill(7)
    )

    return jisc_papers


def get_jisc_title(
    title, issue_date, jisc_papers, input_sub_path, publication_code, abbr=None
):
    """
    Takes an input_sub_path, a publication_code, and an (optional) abbreviation for any newspaper, and tries to
    locate the title in the jisc_papers DataFrame provided (usually loaded with the setup_jisc_papers function
    above).

    Returns a string (or crashes).
    """
    # first option, search the input_sub_path for a valid-looking publication_code
    g = PUBLICATION_CODE.findall(input_sub_path)

    if len(g) == 1:
        publication_code = g[0]
        # let's see if we can find title:
        title = (
            jisc_papers[
                jisc_papers.publication_code == publication_code
            ].title.to_list()[0]
            if jisc_papers[
                jisc_papers.publication_code == publication_code
            ].title.count()
            == 1
            else title
        )
        # print("TITLE2", title)
        return title

    # second option, look through JISC papers for best match (on publication_code if we have it, but abbr more importantly if we have it)
    if abbr:
        _publication_code = publication_code
        publication_code = abbr

    if jisc_papers.abbr[jisc_papers.abbr == publication_code].count():
        date = datetime.datetime.strptime(issue_date, "%Y-%m-%d")
        mask = (
            (jisc_papers.abbr == publication_code)
            & (date >= jisc_papers.start_date)
            & (date <= jisc_papers.end_date)
        )
        filtered = jisc_papers.loc[mask]
        if filtered.publication_code.count() == 1:
            publication_code = filtered.publication_code.to_list()[0]
            title = filtered.title.to_list()[0]
            # print("TITLE3", title)
            return title

    # last option: let's find all the possible titles in the jisc_papers for the abbreviation, and if it's just one unique title, let's pick it!
    if abbr:
        test = list({x for x in jisc_papers[jisc_papers.abbr == abbr].title})
        if len(test) == 1:
            # print("TITLE4", test[0])
            return test[0]
        else:
            mask1 = (jisc_papers.abbr == publication_code) & (
                jisc_papers.publication_code == _publication_code
            )
            test1 = jisc_papers.loc[mask1]
            test1 = list({x for x in jisc_papers[jisc_papers.abbr == abbr].title})
            if len(test) == 1:
                # print("TITLE5", test1[0])
                return test1[0]

    # fallback: if abbreviation is set, we'll return that:
    if abbr:
        # print("TITLE6", abbr)
        # For these exceptions, see issue comment:
        # https://github.com/alan-turing-institute/Living-with-Machines/issues/2453#issuecomment-1050652587
        if abbr == "IPJL":
            return "Ipswich Journal"
        elif abbr == "BHCH":
            return "Bath Chronicle"
        elif abbr == "LSIR":
            return "Leeds Intelligencer"
        elif abbr == "AGER":
            return "Lancaster Gazetter, And General Advertiser For Lancashire West"

        return abbr

    print("TITLE NOT FOUND")
    exit()


def clear_cache(dir):
    y = input(
        f"Do you want to erase the cache path now that the files have been generated ({Path(dir).absolute()})? [y/N]"
    )
    if y.lower() == "y":
        print("Clearing up the cache directory")
        [x.unlink() for x in Path(dir).glob("*.json")]
