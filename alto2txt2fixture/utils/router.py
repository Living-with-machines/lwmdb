from pathlib import Path
from tqdm import tqdm
from xml.etree import ElementTree as ET

import pandas as pd

import json
import uuid
import zipfile

from utils import (
    dotdict,
    get_jisc_title,
    get_now,
    get_size_from_path,
    write_json,
    PUBLICATION_CODE,
    setup_jisc_papers,
)


class Cache:
    def __init__(self):
        pass

    def as_dict(self):
        pass

    def __str__(self):
        return str(self.as_dict())

    def get_cache_path(self):
        return Path(f"{CACHE_HOME}/{self.collection}/{self.kind}/{self.id}.json")

    def write_to_cache(self):
        try:
            if self.get_cache_path().exists():
                return True
        except AttributeError:
            print(
                f"Error occurred when getting cache path for {self.kind}. It was not of expected type Path but of type {type(self.get_cache_path())}:"
            )
            print(self.get_cache_path())
            raise RuntimeError() from None

        self.get_cache_path().parent.mkdir(parents=True, exist_ok=True)

        with open(self.get_cache_path(), "w+") as f:
            f.write(json.dumps(self.as_dict()))

        return True


class Newspaper(Cache):
    kind = "newspaper"

    def __init__(self, root="", collection="", meta=None, jisc_papers=None):
        self.publication = root.find("./publication")
        self.input_sub_path = root.find("./process/input_sub_path").text
        self.issue_date = self.publication.find("./issue/date").text
        self.collection = collection
        self.meta = meta
        self.jisc_papers = jisc_papers

        self._newspaper = None
        self._title = None
        self._publication_code = None

        path = str(self.get_cache_path())
        if not self.meta.newspaper_paths:
            self.meta.newspaper_paths = []
        elif not path in self.meta.newspaper_paths:
            self.meta.newspaper_paths.append(path)

        if not self.meta.publication_codes:
            self.meta.publication_codes = [self.publication_code]
        elif not self.publication_code in self.meta.publication_codes:
            self.meta.publication_codes.append(self.publication_code)

        self.zip_file = Path(meta.path).name

    @property
    def title(self):
        if not self._title:
            try:
                self._title = (
                    self.publication.find("./title")
                    .text.rstrip(".")
                    .strip()
                    .rstrip(":")
                    .strip()
                )
            except AttributeError:
                self._title = ""

            if self._title:
                return self._title

            # we probably have a JISC title so we will go ahead and pick from filename following alto2txt convention
            if not self.zip_file:
                self._title = ""
                print(
                    "Warning: JISC title found but zip file name was not passed so title cannot be correctly processed."
                )
                return ""

            if not isinstance(self.jisc_papers, pd.DataFrame):
                self._title = ""
                print(
                    "Warning: JISC title found but zip file name was not passed so title cannot be correctly processed."
                )
                return ""

            abbr = self.zip_file.split("_")[0]
            self._title = get_jisc_title(
                self._title,
                self.issue_date,
                self.jisc_papers,
                self.input_sub_path,
                self.publication_code,
                abbr,
            )

        return self._title

    def as_dict(self):
        if not self._newspaper:
            self._newspaper = dict(
                **dict(publication_code=self.publication_code, title=self.title),
                **{
                    x.tag: x.text or ""
                    for x in self.publication.findall("*")
                    if x.tag in ["location"]
                },
            )
        return self._newspaper

    def publication_code_from_input_sub_path(self):
        g = PUBLICATION_CODE.findall(self.input_sub_path)
        if len(g) == 1:
            return g[0]
        return None

    @property
    def publication_code(self):
        if not self._publication_code:
            self._publication_code = self.publication.attrib.get("id")
            if len(self._publication_code) != 7:
                if self._publication_code == "NCBL1001":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000499"
                elif self._publication_code == "NCBL1002":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000499"
                elif self._publication_code == "NCBL1023":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000152"
                elif self._publication_code == "NCBL1024":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000171"
                elif self._publication_code == "NCBL1029":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000165"
                elif self._publication_code == "NCBL1034":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000160"
                elif self._publication_code == "NCBL1035":
                    self._publication_code = self.publication_code_from_input_sub_path()
                    if not self._publication_code:
                        # fallback option
                        self._publication_code = "0000185"
                elif (
                    len(self._publication_code) == 4 or "NCBL" in self._publication_code
                ):
                    g = PUBLICATION_CODE.findall(self.input_sub_path)
                    if len(g) == 1:
                        self._publication_code = g[0]
                    else:
                        raise RuntimeError("Publication code look-up failed.")

            if not self._publication_code:
                g = PUBLICATION_CODE.findall(self.input_sub_path)
                if len(g) == 1:
                    self._publication_code = g[0]
                else:
                    raise RuntimeError("Backup failed.")

            if not len(self._publication_code) == 7:
                self._publication_code = f"{self._publication_code}".zfill(7)

            if not self._publication_code:
                raise RuntimeError(f"Publication code is non-existent.")

            if not len(self._publication_code) == 7:
                raise RuntimeError(
                    f"Publication code is of wrong length: {len(self._publication_code)} ({self._publication_code})."
                )

        return self._publication_code

    @property
    def number_paths(self):
        number_paths = [x for x in self.publication_code.lstrip("0")[:2]]
        if len(number_paths) == 1:
            number_paths = ["0"] + number_paths

        return number_paths

    def get_cache_path(self):
        return Path(
            f"{CACHE_HOME}/{self.collection}/"
            + "/".join(self.number_paths)
            + f"/{self.publication_code}/{self.publication_code}.json"
        )


class Item(Cache):
    kind = "item"

    def __init__(
        self,
        root="",
        issue_code="",
        digitisation={},
        ingest={},
        collection="",
        newspaper=None,
        meta=None,
    ):
        self.root = root
        self.issue_code = issue_code
        self.digitisation = digitisation
        self.ingest = ingest
        self.collection = collection
        self.newspaper = newspaper
        self.meta = meta

        self._item_elem = None
        self._item_code = None
        self._item = None

        path = str(self.get_cache_path())
        if not self.meta.item_paths:
            self.meta.item_paths = [path]
        elif not path in self.meta.item_paths:
            self.meta.item_paths.append(path)

    @property
    def item_elem(self):
        if not self._item_elem:
            self._item_elem = self.root.find("./publication/issue/item")
        return self._item_elem

    def as_dict(self):
        if not self._item:
            self._item = {
                f"{x.tag}": x.text or ""
                for x in self.item_elem.findall("*")
                if x.tag
                in [
                    "title",
                    "word_count",
                    "ocr_quality_mean",
                    "ocr_quality_sd",
                    "plain_text_file",
                    "item_type",
                ]
            }

            self._item["title"] = self._item.get("title", "")[:2097151]

            self._item = {
                "item_code": self.item_code,
                "word_count": self._item.get("word_count", 0),
                "title": self._item.get("title"),
                "item_type": self._item.get("item_type"),
                "input_filename": self._item.get("plain_text_file", ""),
                "ocr_quality_mean": self._item.get("ocr_quality_mean", 0),
                "ocr_quality_sd": self._item.get("ocr_quality_sd", 0),
                "digitisation__software": self.digitisation.id,
                "ingest__lwm_tool_identifier": self.ingest.id,
                "issue__issue_identifier": self.issue_code,
                "data_provider__name": self.collection,
            }

        return self._item

    @property
    def item_code(self):
        if not self._item_code:
            self._item_code = self.issue_code + "-" + self.item_elem.attrib.get("id")

        return self._item_code

    def get_cache_path(self):
        return Path(
            f"{CACHE_HOME}/{self.collection}/"
            + "/".join(self.newspaper.number_paths)
            + f"/{self.newspaper.publication_code}/items.jsonl"
        )

    def write_to_cache(self):
        self.get_cache_path().parent.mkdir(parents=True, exist_ok=True)

        with open(self.get_cache_path(), "a+") as f:
            f.write(json.dumps(self.as_dict()) + "\n")


class Issue(Cache):
    kind = "issue"

    def __init__(
        self, publication, newspaper=None, collection="", input_sub_path="", meta=None
    ):
        self.publication = publication
        self.newspaper = newspaper
        self.collection = collection
        self.input_sub_path = input_sub_path
        self.meta = meta

        self._issue = None
        self._issue_date = None

        path = str(self.get_cache_path())
        if not self.meta.issue_paths:
            self.meta.issue_paths = [path]
        elif not path in self.meta.issue_paths:
            self.meta.issue_paths.append(path)

    @property
    def issue_date(self):
        if not self._issue_date:
            self._issue_date = self.publication.find("./issue/date").text
        return self._issue_date

    @property
    def issue_code(self):
        return (
            self.newspaper.publication_code.replace("-", "")
            + "-"
            + self.issue_date.replace("-", "")
        )

    def as_dict(self):
        if not self._issue:
            self._issue = {
                "issue_code": self.issue_code,
                "issue_date": self.issue_date,
                "publication__publication_code": self.newspaper.publication_code,
                "input_sub_path": self.input_sub_path,
            }

        return self._issue

    def get_cache_path(self):
        return Path(
            f"{CACHE_HOME}/{self.collection}/"
            + "/".join(self.newspaper.number_paths)
            + f"/{self.newspaper.publication_code}/issues/{self.issue_code}.json"
        )


class Ingest(Cache):
    kind = "ingest"

    def __init__(self, root=None, collection=None):
        self.root = root
        self.collection = collection

    def as_dict(self):
        return {
            f"lwm_tool_{x.tag}": x.text or ""
            for x in self.root.findall("./process/lwm_tool/*")
        }

    @property
    def id(self):
        return (
            self.as_dict().get("lwm_tool_name")
            + "-"
            + self.as_dict().get("lwm_tool_version")
        )


class Digitisation(Cache):
    kind = "digitisation"

    def __init__(self, root=None, collection=None):
        self.root = root
        self.collection = collection

    def as_dict(self):
        dic = {
            x.tag: x.text or ""
            for x in self.root.findall("./process/*")
            if x.tag
            in [
                "xml_flavour",
                "software",
                "mets_namespace",
                "alto_namespace",
            ]
        }
        if not dic.get("software"):
            return {}

        return dic

    @property
    def id(self):
        return (
            self.as_dict().get("software").replace("/", "---")
            if self.as_dict().get("software")
            else None
        )


class DataProvider(Cache):
    kind = "data-provider"

    def __init__(self, collection=None):
        self.collection = collection

    def as_dict(self):
        return {"name": self.collection, "collection": "newspapers", "source_note": ""}

    @property
    def id(self):
        return self.as_dict().get("name")


class Document:
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.get("collection")
        if not self.collection or not isinstance(self.collection, str):
            raise RuntimeError("A valid collection must be passed")

        self.root = kwargs.get("root")
        if not self.root or not isinstance(self.root, ET.Element):
            raise RuntimeError("A valid XML root must be passed")

        self.zip_file = kwargs.get("zip_file")
        if self.zip_file and not isinstance(self.zip_file, str):
            raise RuntimeError("A valid zip file must be passed")

        self.jisc_papers = kwargs.get("jisc_papers")
        if not isinstance(self.jisc_papers, pd.DataFrame):
            raise RuntimeError(
                "A valid DataFrame containing JISC papers must be passed"
            )

        self.meta = kwargs.get("meta")

        self._publication_elem = None
        self._input_sub_path = None
        self._ingest = None
        self._digitisation = None
        self._item = None
        self._issue = None
        self._newspaper = None
        self._data_provider = None

    @property
    def publication(self):
        if not self._publication_elem:
            self._publication_elem = self.root.find("./publication")
        return self._publication_elem

    @property
    def issue(self):
        if not self._issue:
            self._issue = Issue(
                publication=self.publication,
                newspaper=self.newspaper,
                collection=self.collection,
                input_sub_path=self.input_sub_path,
                meta=self.meta,
            )
        return self._issue

    @property
    def input_sub_path(self):
        if not self._input_sub_path:
            self._input_sub_path = self.root.find("./process/input_sub_path").text
        return self._input_sub_path

    @property
    def data_provider(self):
        if not self._data_provider:
            self._data_provider = DataProvider(collection=self.collection)

        return self._data_provider

    @property
    def ingest(self):
        if not self._ingest:
            self._ingest = Ingest(root=self.root, collection=self.collection)

        return self._ingest

    @property
    def digitisation(self):
        if not self._digitisation:
            self._digitisation = Digitisation(
                root=self.root, collection=self.collection
            )

        return self._digitisation

    @property
    def item(self):
        if not self._item:
            self._item = Item(
                root=self.root,
                issue_code=self.issue.issue_code,
                digitisation=self.digitisation,
                ingest=self.ingest,
                collection=self.collection,
                newspaper=self.newspaper,
                meta=self.meta,
            )

        return self._item

    @property
    def newspaper(self):
        if not self._newspaper:
            self._newspaper = Newspaper(
                root=self.root,
                collection=self.collection,
                meta=self.meta,
                jisc_papers=self.jisc_papers,
            )
        return self._newspaper


class Archive:
    def __init__(self, path="", collection="", report_id=None, jisc_papers=None):
        self.path = Path(path)

        if not self.path.exists():
            raise RuntimeError("Path does not exist.")

        self.size = get_size_from_path(self.path)
        self.size_raw = get_size_from_path(self.path, raw=True)
        self.zip_file = zipfile.ZipFile(self.path)
        self.collection = collection

        self.roots = self.get_roots()
        self.meta = dotdict(
            path=str(self.path),
            bytes=self.size_raw,
            size=self.size,
            contents=len(self.filelist),
        )

        if not report_id:
            self.report_id = str(uuid.uuid4())
        else:
            self.report_id = report_id

        self.jisc_papers = jisc_papers

        self.report_parent = Path(f"{REPORT_DIR}/{self.report_id}")
        self.report = (
            self.report_parent / f"{self.path.stem.replace('_metadata', '')}.json"
        )

    def __len__(self):
        return len(self.filelist)

    def __str__(self):
        return f"{self.path} ({self.size})"

    def __repr__(self):
        return f'Archive <"{self.__str__()}", {self.size}>'

    def __enter__(self):
        self.meta.start = get_now()
        # print(f"Processing {self.path.name}...")

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.meta.end = get_now()
        self.meta.seconds = (self.meta.end - self.meta.start).seconds
        self.meta.microseconds = (self.meta.end - self.meta.start).microseconds
        self.meta.start = str(self.meta.start)
        self.meta.end = str(self.meta.end)
        write_json(self.report, self.meta, add_created=False)
        # print(f"Report created: {self.report}...")
        # TODO: Handle exceptions: (exc_type, exc_value, exc_tb)

        if self.meta.item_paths:
            for item_doc in self.meta.item_paths:
                Path(item_doc).write_text(
                    "\n".join(
                        [
                            json.dumps(x)
                            for x in [
                                json.loads(x)
                                for x in {
                                    line
                                    for line in Path(item_doc).read_text().splitlines()
                                }
                                if x
                            ]
                        ]
                    )
                    + "\n"
                )

    @property
    def filelist(self):
        return self.zip_file.filelist

    @property
    def documents(self):
        return self.get_documents()

    def get_roots(self):
        for xml_file in tqdm(self.filelist, leave=False):
            with self.zip_file.open(xml_file) as f:
                xml = f.read()
                if xml:
                    yield ET.fromstring(xml)

    def get_documents(self):
        for xml_file in tqdm(
            self.filelist,
            desc=f"{Path(self.zip_file.filename).stem} ({self.meta.size})",
            leave=False,
        ):
            with self.zip_file.open(xml_file) as f:
                xml = f.read()
                if xml:
                    yield Document(
                        root=ET.fromstring(xml),
                        collection=self.collection,
                        meta=self.meta,
                        jisc_papers=self.jisc_papers,
                    )


class Collection:
    def __init__(self, name="hmd", jisc_papers=None):
        self.name = name
        self.jisc_papers = jisc_papers
        self.dir = Path(f"{MNT}/{self.name}-alto2txt/metadata")
        self.zip_files = sorted(
            list(self.dir.glob("*.zip")), key=lambda x: x.stat().st_size
        )
        self.zip_file_count = sum([1 for _ in self.dir.glob("*.zip")])
        self.report_id = str(uuid.uuid4())

    @property
    def archives(self):
        for zip_file in tqdm(self.zip_files, total=self.zip_file_count, leave=False):
            yield Archive(
                zip_file,
                collection=self.name,
                report_id=self.report_id,
                jisc_papers=self.jisc_papers,
            )


def route(collections, cache_home, mountpoint, jisc_papers_path, report_dir):
    global CACHE_HOME
    global MNT
    global REPORT_DIR

    CACHE_HOME = cache_home
    REPORT_DIR = report_dir

    MNT = Path(mountpoint) if isinstance(mountpoint, str) else mountpoint
    if not MNT.exists():
        raise RuntimeError(
            f"No mountpoint for alto2txt exists. Either create a local copy or blobfuse it to {MNT.absolute()}"
        ) from None

    jisc_papers = setup_jisc_papers(path=jisc_papers_path)

    for collection_name in collections:
        collection = Collection(name=collection_name, jisc_papers=jisc_papers)

        if not sum(1 for _ in collection.archives):
            raise RuntimeError(
                f"It looks like {collection_name} is empty in the alto2txt mountpoint: {collection.dir.absolute()}"
            ) from None

        for archive in collection.archives:
            with archive as a:
                [
                    (
                        doc.item.write_to_cache(),
                        doc.newspaper.write_to_cache(),
                        doc.issue.write_to_cache(),
                        doc.data_provider.write_to_cache(),
                        doc.ingest.write_to_cache(),
                        doc.digitisation.write_to_cache(),
                    )
                    for doc in archive.documents
                ]
