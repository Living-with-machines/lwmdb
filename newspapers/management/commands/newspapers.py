import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from django.core.serializers import serialize
from django.db.utils import OperationalError
from numpy import append, array
from tqdm import tqdm

from newspapers.models import DataProvider, Digitisation, Ingest, Issue, Newspaper

from .fixtures import DATA_PROVIDERS, MOUNTPOINTS, Fixture

# Reverse set to True means that largest files are processed first
REVERSE = False

# If set to true, there will be a success message posted after every successful insertion into the db
WRITE_SUCCESS = False


newspaper_cache = "cache-newspaper"


class NewspapersFixture(Fixture):
    app_name = "newspapers"
    models = [Newspaper, Issue, Digitisation, Ingest, DataProvider]

    def __init__(self, force=False):
        self.force = force
        super(Fixture, self).__init__()

    def save_fixtures(self):
        for model in self.models:
            filename = f"{model._meta.label.split('.')[-1]}-fixtures.json"
            model_fields = model._meta.get_fields()
            data = serialize(
                "json",
                model.objects.all(),
                fields=[
                    x.name
                    for x in model_fields
                    if not x.name in ["created_at", "updated_at"]
                ],
            )
            path = self.get_output_dir() / filename
            with open(path, "w+") as f:
                f.write(data)

        return True

    def get_zipfiles(self, data_provider):
        zipfiles = [x for x in Path(MOUNTPOINTS[data_provider]).glob("*.zip")]
        zipfiles.sort(key=lambda x: x.stat().st_size)

        if REVERSE:
            zipfiles.reverse()

        return zipfiles

    def get_cache_path(self, data_provider, newspaper_zip, add_nlp=None):
        if data_provider == "jisc":
            if not add_nlp:
                cache_path = Path(f"./{newspaper_cache}/{data_provider}")
                self.test_parent(cache_path)
                return cache_path

            nlp = add_nlp
        else:
            nlp = newspaper_zip.name.split("_")[0]

        m = len([x for x in nlp[3:]]) - 2
        valid_path_numbers = [x for x in nlp[3:]][:m]
        cache_path = Path(
            f"./{newspaper_cache}/{data_provider}/" + "/".join(valid_path_numbers)
        )
        self.test_parent(cache_path)

        return cache_path

    @staticmethod
    def test_parent(path):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

    def build_cache(self):
        """Build a cache in a file structure of Newspapers and Issues.

        Caches follow this file structure:
        ./{newspaper_cache}/{name of data provider}/2/2/0002246.json

        Each json file contains either an object (Newspapers) or a list
        of issues (Issues).
        """
        UNNAMED = 0

        for data_provider in DATA_PROVIDERS:
            ZIPFILES = self.get_zipfiles(data_provider)

            for newspaper_zip in (bar1 := tqdm(ZIPFILES)):
                bar1.set_description(f"{data_provider} :: {newspaper_zip.name}")
                collected = array([])

                cache_path = self.get_cache_path(data_provider, newspaper_zip)

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

                        e = root.find("./publication")
                        newspaper = {"publication_code": e.attrib.get("id")}

                        if data_provider == "jisc":
                            if nlp == None:
                                nlp = newspaper["publication_code"]
                                cache_path = self.get_cache_path(
                                    data_provider, newspaper_zip, nlp
                                )

                            issue_identifier = nlp + "".join(issue_file.split("/")[1:4])
                        else:
                            issue_identifier = "".join(issue_file.split("/")[0:3])

                        newspaper_cache_file = cache_path / f"newspaper/{nlp}.json"
                        self.test_parent(newspaper_cache_file)

                        if not newspaper_cache_file.exists():
                            _newspaper = {
                                x.tag: x.text or ""
                                for x in e.findall("*")
                                if x.tag in ["title", "location"]
                            }

                            if not _newspaper.get("title"):
                                if data_provider == "jisc":
                                    newspaper["title"] = f"{paper_abbr}"
                                else:
                                    UNNAMED += 1
                                    newspaper["title"] = f"Untitled {UNNAMED}"

                            newspaper = dict(newspaper, **_newspaper)

                            newspaper_cache_file.write_text(json.dumps(newspaper))

                        issue_cache_path = cache_path / Path(
                            f"issue/{nlp}/issues.jsonl"
                        )
                        self.test_parent(issue_cache_path)

                        if not issue_identifier in collected:
                            # Create/build `current_issues``
                            try:
                                current_issues = [
                                    json.loads(line)
                                    for line in issue_cache_path.read_text().splitlines()
                                ]
                            except FileNotFoundError:
                                current_issues = []

                            # Check if already processed (i.e. in `current_issues`)
                            if any(
                                [
                                    issue.get("issue_code") == issue_identifier
                                    for issue in current_issues
                                ]
                            ):
                                collected = append(collected, issue_identifier)
                                continue

                            e = root.find("./publication/issue")
                            issue = {
                                "issue_code": issue_identifier,
                                "publication__publication_code": newspaper[
                                    "publication_code"
                                ],
                            }

                            if data_provider == "jisc":
                                pass

                            _issue = {
                                f"issue_{x.tag}": x.text or ""
                                for x in e.findall("*")
                                if x.tag in ["date"]
                            }
                            _issue["input_sub_path"] = root.find(
                                "./process/input_sub_path"
                            ).text

                            issue = dict(issue, **_issue)

                            current_issues.append(issue)

                            current_issues = list(
                                {json.dumps(issue) for issue in current_issues}
                            )

                            with open(
                                (cache_path / Path(f"issue/{nlp}/issues.jsonl")), "w+"
                            ) as f:
                                f.write("\n".join(current_issues))
                                collected = append(collected, issue_identifier)

    def ingest_cache(self):
        """Function for ingesting cache files for Newspaper and Issue items."""
        get_newspaper_files = lambda data_provider: [
            x for x in Path(f"./{newspaper_cache}/{data_provider}/").glob("**/*.json")
        ]

        get_issue_files = lambda data_provider: [
            x
            for x in Path(f"./{newspaper_cache}/{data_provider}/").glob("**/*.jsonl")
            if x.name == "issues.jsonl"
        ]

        def error_msg(kind, **kwargs):
            if kwargs.get("required"):
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Skipping {kind} in {kwargs.get('json_path')} because it has no (required) {kwargs.get('required')}."
                    )
                )
            elif kwargs.get("locked"):
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: database is locked. Cannot write {kind}."
                    )
                )

        def success_msg(kind, id):
            if WRITE_SUCCESS:
                self.stdout.write(self.style.SUCCESS(f"Wrote {kind} {id} to db."))

        total = 0

        for data_provider in DATA_PROVIDERS:
            # Start processing newspapers
            NEWSPAPER_FILES = get_newspaper_files(data_provider)

            for json_path in (bar1 := tqdm(NEWSPAPER_FILES, leave=False)):
                bar1.set_description(
                    f"newspaper cache :: {data_provider} :: {json_path.name}"
                )

                newspaper = json.loads(json_path.read_text())

                if not newspaper.get("publication_code"):
                    error_msg(
                        "newspaper", required="publication_code", json_path=json_path
                    )
                    continue

                try:
                    o, _ = Newspaper.objects.update_or_create(
                        publication_code=newspaper["publication_code"],
                        defaults=newspaper,
                    )
                    success_msg("Newspaper", o.id)

                except OperationalError as e:
                    if "database is locked" in str(e):
                        error_msg("Newspaper", locked=True)
                        continue

            # Then process issues
            ISSUE_FILES = get_issue_files(data_provider)

            for json_path in (bar1 := tqdm(ISSUE_FILES)):
                bar1.set_description(
                    f"issue cache :: {data_provider} :: {json_path.parent.name}"
                )

                issues = [
                    json.loads(line) for line in json_path.read_text().splitlines()
                ]

                for issue in (bar2 := tqdm(issues, leave=False)):
                    if not issue.get("issue_code"):
                        error_msg("issue", required="issue_code", json_path=json_path)
                        continue

                    bar2.set_description(f"{total} saved :: {issue['issue_date']}")

                    if Issue.objects.filter(issue_code=issue["issue_code"]).count():
                        # there is already an issue - we might want to overwrite, but testing for speed here.
                        continue

                    if not issue.get("publication__publication_code"):
                        error_msg(
                            "issue",
                            required="publication_code",
                            json_path=json_path,
                        )
                        continue

                    # connections
                    try:
                        issue["newspaper"] = Newspaper.objects.get(
                            publication_code=issue["publication__publication_code"]
                        )
                    except Newspaper.DoesNotExist:
                        error_msg(
                            "issue",
                            required=f"related newspaper ({issue['publication__publication_code']}) in db",
                            json_path=json_path,
                        )
                        continue

                    del issue["publication__publication_code"]

                    try:
                        o, _ = Issue.objects.update_or_create(
                            issue_code=issue["issue_code"], defaults=issue
                        )
                        total += 1
                        success_msg("Issue", o.id)
                    except OperationalError as e:
                        if "database is locked" in str(e):
                            error_msg("Newspaper", locked=True)
                            continue

    # def ingest_newspapers(self):
    #     for data_provider in DATA_PROVIDERS:
    #         self.NOW = datetime.now().strftime("%Y-%m-%d")
    #         UNNAMED = 0

    #         self.stdout.write(
    #             self.style.NOTICE(
    #                 f"Generating DataProvider, Publication, Digitisation, Ingest, Issue objects for {data_provider}"
    #             )
    #         )

    #         data_provider_dict = {
    #             "name": data_provider,
    #             "collection": "newspapers",
    #             "source_note": "",
    #         }
    #         # Get/insert data provider into/from database
    #         data_provider_o, _ = DataProvider.objects.get_or_create(
    #             name=data_provider, defaults=data_provider_dict
    #         )

    #         # Create list of all zip files in metadata directory for the data_provider sorted from larger to smaller
    #         ZIPFILES = self.get_zipfiles(data_provider)

    #         if not len(ZIPFILES):
    #             self.stdout.write(
    #                 self.style.WARNING(
    #                     f"Warning: Cannot find any mounted zip files for data provider {data_provider}."
    #                 )
    #             )
    #             self.stdout.write(
    #                 self.style.WARNING(
    #                     f"Is the directory {MOUNTPOINTS[data_provider]} mounted correctly?"
    #                 )
    #             )
    #             self.stdout.write("")

    #             continue

    #         # Process major metadata!
    #         for newspaper_zip in (bar1 := tqdm(ZIPFILES)):  # [:LIMIT]
    #             bar1.set_description(f"{data_provider} :: {newspaper_zip.name}")

    #             with zipfile.ZipFile(newspaper_zip) as zf:
    #                 issue_xmls = [
    #                     f.filename for f in zipfile.ZipFile(newspaper_zip).filelist
    #                 ]

    #                 if not SKIP_ITEMS and len(issue_xmls) > MAX_ISSUES:
    #                     self.stdout.write(
    #                         self.style.WARNING(
    #                             f"Warning: {newspaper_zip.name} has too many issues ({len(issue_xmls)}) and will be skipped"
    #                         )
    #                     )
    #                     continue

    #                 for issue_file in (bar2 := tqdm(issue_xmls, leave=False)):
    #                     bar2.set_description(f"{Path(issue_file).parent}")

    #                     issue_identifier = "".join(issue_file.split("/")[0:3])

    #                     with zf.open(issue_file) as inner:
    #                         issue_xml = inner.read()

    #                         if not issue_xml:
    #                             continue

    #                     root = ET.fromstring(issue_xml)
    #                     ingest = {
    #                         f"lwm_tool_{x.tag}": x.text or ""
    #                         for x in root.findall("./process/lwm_tool/*")
    #                     }

    #                     digitisation = {
    #                         x.tag: x.text or ""
    #                         for x in root.findall("./process/*")
    #                         if x.tag
    #                         in [
    #                             "xml_flavour",
    #                             "software",
    #                             "mets_namespace",
    #                             "alto_namespace",
    #                         ]
    #                     }

    #                     e = root.find("./publication")
    #                     newspaper = {
    #                         x.tag: x.text or ""
    #                         for x in e.findall("*")
    #                         if x.tag in ["title", "location"]
    #                     }
    #                     newspaper["publication_code"] = e.attrib.get("id")
    #                     if not newspaper.get("title"):
    #                         UNNAMED += 1
    #                         newspaper["title"] = f"Untitled {UNNAMED}"

    #                     e = root.find("./publication/issue")
    #                     issue = {
    #                         f"issue_{x.tag}": x.text or ""
    #                         for x in e.findall("*")
    #                         if x.tag in ["date"]
    #                     }
    #                     issue["issue_code"] = issue_identifier
    #                     issue["input_sub_path"] = root.find(
    #                         "./process/input_sub_path"
    #                     ).text

    #                     newspaper_o, _ = Newspaper.objects.get_or_create(
    #                         publication_code=newspaper["publication_code"],
    #                         defaults=newspaper,
    #                     )

    #                     issue["publication"] = newspaper_o
    #                     issue_o, _ = Issue.objects.get_or_create(
    #                         issue_code=issue["issue_code"], defaults=issue
    #                     )

    #                     # Get/insert digitisation into/from database
    #                     digitisation_o, _ = Digitisation.objects.get_or_create(
    #                         software=digitisation.get("software", ""),
    #                         defaults=digitisation,
    #                     )

    #                     # Get/insert ingest into/from database
    #                     ingest_o, _ = Ingest.objects.get_or_create(
    #                         lwm_tool_name=ingest["lwm_tool_name"],
    #                         lwm_tool_version=ingest["lwm_tool_version"],
    #                         defaults=ingest,
    #                     )

    #                     if SKIP_ITEMS:
    #                         continue

    #                     # # Now do item! —> see items.py instead
    #                     # e = root.find("./publication/issue/item")

    #                     # item = {
    #                     #     f"{x.tag}": x.text or ""
    #                     #     for x in e.findall("*")
    #                     #     if x.tag
    #                     #     in [
    #                     #         "title",
    #                     #         "word_count",
    #                     #         "ocr_quality_mean",
    #                     #         "ocr_quality_sd",
    #                     #         "plain_text_file",
    #                     #         "item_type",
    #                     #     ]
    #                     # }
    #                     # item["item_code"] = issue_identifier + "-" + e.attrib.get("id")
    #                     # item["input_filename"] = item.get("plain_text_file")
    #                     # del item["plain_text_file"]

    #                     # item["ocr_quality_mean"] = (
    #                     #     item["ocr_quality_mean"] if item["ocr_quality_mean"] else 0
    #                     # )
    #                     # item["ocr_quality_sd"] = (
    #                     #     item["ocr_quality_sd"] if item["ocr_quality_sd"] else 0
    #                     # )

    #                     # issue_o = Issue.objects.get(issue_code=issue_identifier)
    #                     # ingest_o = Ingest.objects.get(
    #                     #     lwm_tool_name=ingest["lwm_tool_name"],
    #                     #     lwm_tool_version=ingest["lwm_tool_version"],
    #                     # )
    #                     # digitisation_o = Digitisation.objects.get(
    #                     #     software=digitisation["software"]
    #                     # )

    #                     # # Get/insert ingest into/from database
    #                     # item["data_provider"] = data_provider_o
    #                     # item["digitisation"] = digitisation_o
    #                     # item["issue"] = issue_o
    #                     # item["ingest"] = ingest_o
    #                     # item_o, _ = Item.objects.get_or_create(
    #                     #     item_code=item["item_code"],
    #                     #     defaults=item,
    #                     # )

    #             self.write_models(self.models)
    #             self.stdout.write(
    #                 self.style.SUCCESS(
    #                     f"\nWrote {len(self.models)} models to fixture files ({self.get_output_dir()})."
    #                 )
    #             )
