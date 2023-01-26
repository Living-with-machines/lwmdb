import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from django.db.utils import OperationalError
from tqdm import tqdm

from newspapers.models import DataProvider, Digitisation, Ingest, Issue, Item

from .fixtures import DATA_PROVIDERS
from .newspapers import MOUNTPOINTS, REVERSE, NewspapersFixture

item_cache = "cache-item"


class ItemFixture(NewspapersFixture):
    models = [Item]

    def __init__(self, force=False):
        self.force = force
        super(NewspapersFixture, self).__init__()

    def get_zipfiles(self, data_provider):
        zipfiles = [x for x in Path(MOUNTPOINTS[data_provider]).glob("*.zip")]
        zipfiles.sort(key=lambda x: x.stat().st_size)
        if REVERSE:
            zipfiles.reverse()

        return zipfiles

    def get_cache_path(self, data_provider, newspaper_zip, add_nlp=None):
        if data_provider == "jisc":
            if not add_nlp:
                self.test_parent(cache_path)
                cache_path = Path(f"./{item_cache}/{data_provider}")
                return cache_path

            nlp = add_nlp
        else:
            nlp = newspaper_zip.name.split("_")[0]

        m = len([x for x in nlp[3:]]) - 2
        valid_path_numbers = [x for x in nlp[3:]][:m]
        cache_path = Path(
            f"./{item_cache}/{data_provider}/" + "/".join(valid_path_numbers)
        )
        self.test_parent(cache_path)

        return cache_path

    @staticmethod
    def test_parent(path):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

    def build_cache(self):
        """
        Builds a cache in a file structure:
        ./{item_cache}/{name of data provider}/2/2/0002246.jsonl

        Each jsonl file contains a list of Items.
        """

        for data_provider in DATA_PROVIDERS:
            ZIPFILES = self.get_zipfiles(data_provider)

            for newspaper_zip in (bar1 := tqdm(ZIPFILES, leave=False)):
                bar1.set_description(f"{data_provider} :: {newspaper_zip.name}")

                cache_path = self.get_cache_path(data_provider, newspaper_zip)

                if data_provider != "jisc":
                    nlp = newspaper_zip.name.split("_")[0]
                    cache_file = cache_path / f"{nlp}.jsonl"

                    if cache_file.exists():
                        continue

                issue_xmls = [
                    f.filename for f in zipfile.ZipFile(newspaper_zip).filelist
                ]

                with zipfile.ZipFile(newspaper_zip) as zf:
                    for issue_file in (bar2 := tqdm(issue_xmls, leave=False)):
                        bar2.set_description(f"{Path(issue_file).parent}")

                        if data_provider == "jisc":
                            nlp = None
                            paper_abbr = newspaper_zip.name.split("_")[0]

                        with zf.open(issue_file) as inner:
                            issue_xml = inner.read()

                            if not issue_xml:
                                continue

                        root = ET.fromstring(issue_xml)

                        if data_provider == "jisc":
                            e = root.find("./publication")
                            nlp = e.attrib.get("id")
                            cache_path = self.get_cache_path(
                                data_provider, newspaper_zip, nlp
                            )
                            cache_file = cache_path / f"{nlp}.jsonl"
                            self.test_parent(cache_file)

                            issue_identifier = nlp + "".join(issue_file.split("/")[1:4])
                        else:
                            issue_identifier = "".join(issue_file.split("/")[0:3])

                        ingest = {
                            f"lwm_tool_{x.tag}": x.text or ""
                            for x in root.findall("./process/lwm_tool/*")
                        }

                        digitisation = {
                            x.tag: x.text or ""
                            for x in root.findall("./process/*")
                            if x.tag
                            in [
                                "xml_flavour",
                                "software",
                                "mets_namespace",
                                "alto_namespace",
                            ]
                        }
                        e = root.find("./publication/issue/item")

                        item = {
                            f"{x.tag}": x.text or ""
                            for x in e.findall("*")
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
                        item["item_code"] = issue_identifier + "-" + e.attrib.get("id")
                        item["input_filename"] = item.get("plain_text_file", "")
                        del item["plain_text_file"]

                        item["ocr_quality_mean"] = item.get("ocr_quality_mean", 0)
                        item["ocr_quality_sd"] = item.get("ocr_quality_sd", 0)

                        # relations
                        item["digitisation__software"] = digitisation.get(
                            "software", ""
                        )
                        item["ingest__lwm_tool_name"] = ingest.get("lwm_tool_name", "")
                        item["ingest__lwm_tool_version"] = ingest.get(
                            "lwm_tool_version", ""
                        )
                        item["issue__issue_identifier"] = issue_identifier
                        item["data_provider"] = data_provider

                        # ensure length is right
                        # -> title needs to follow JSON's max limit
                        item["title"] = item.get("title", "")[:2097152]
                        # -> item_code needs to follow db limit (set in newspapers.models)
                        item["item_code"] = item.get("item_code", "")[:600]

                        with open(cache_file, "a+") as f:
                            f.write(f"{json.dumps(item)}\n")

    def ingest_cache(self):
        total = 0

        for data_provider in DATA_PROVIDERS:
            JSONL_FILES = list(
                Path(f"./{item_cache}/{data_provider}/").glob("**/*.jsonl")
            )

            for jsonl_path in (bar1 := tqdm(JSONL_FILES)):
                bar1.set_description(f"{data_provider} :: {jsonl_path.name}")

                lines = jsonl_path.read_text().splitlines()

                for line in (bar2 := tqdm(lines, leave=False)):
                    item = json.loads(line)

                    if not item.get("item_code"):
                        self.stdout.write(
                            self.style.WARNING(
                                f"Warning: skipping one item in {jsonl_path.name} because it has no (required) item_code assigned."
                            )
                        )
                        continue

                    bar2.set_description(f"{total} saved :: {item['item_code']}")

                    # relations
                    digitisation_o = Digitisation.objects.get(
                        software=item.get("digitisation__software")
                    )
                    ingest_o = Ingest.objects.get(
                        lwm_tool_name=item.get("ingest__lwm_tool_name"),
                        lwm_tool_version=item.get("ingest__lwm_tool_version"),
                    )
                    data_provider_o = DataProvider.objects.get(
                        name=item.get("data_provider")
                    )
                    issue_o = Issue.objects.get(
                        issue_code=item.get("issue__issue_identifier")
                    )

                    del item["digitisation__software"]
                    del item["ingest__lwm_tool_name"]
                    del item["ingest__lwm_tool_version"]
                    del item["data_provider"]
                    del item["issue__issue_identifier"]

                    item["digitisation"] = digitisation_o
                    item["ingest"] = ingest_o
                    item["data_provider"] = data_provider_o
                    item["issue"] = issue_o

                    if not item["ocr_quality_mean"] or item["ocr_quality_mean"] == "":
                        item["ocr_quality_mean"] = 0

                    if not item["ocr_quality_sd"] or item["ocr_quality_sd"] == "":
                        item["ocr_quality_sd"] = 0

                    if Item.objects.filter(**item):
                        # improving speed
                        continue

                    # write to db
                    try:
                        item_o, _ = Item.objects.update_or_create(
                            item_code=item["item_code"], defaults=item
                        )
                        total += 1
                        # self.stdout.write(
                        #     self.style.SUCCESS(f"Item {item_o.id} written to db")
                        # )
                    except OperationalError as e:
                        if "database is locked" in str(e):
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Warning: database is locked. Cannot write Item."
                                )
                            )
