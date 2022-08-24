import json

# TODO: turned off garbage collection but it is worth seeing if it's possible to reactivate
# import gc
from pathlib import Path
from tqdm import tqdm
from utils import NOW_str


def fixtures(filelist=[], model="", translate={}, rename={}, uniq_keys=[]):
    def uniq(filelist, keys=[]):
        seen = set()
        for item in filelist:
            key = "-".join([json.loads(item.read_text()).get(x) for x in keys])

            if key not in seen:
                seen.add(key)
                yield item
            else:
                pass  # drop it if duplicate

    filelist = sorted(filelist, key=lambda x: str(x).split("/")[:-1])
    count = len(filelist)

    # process JSONL
    if [x for x in filelist if ".jsonl" in x.name]:
        pk = 0
        # because of the size of these lists, we cannot use tqdm on a list comprehension here
        # TODO: explore whether we can add tqdm on the logic below
        for file in filelist:
            for line in file.read_text().splitlines():
                pk += 1
                line = json.loads(line)
                yield dict(
                    pk=pk,
                    model=model,
                    fields=dict(**get_fields(line, translate=translate, rename=rename)),
                )

        return
    else:
        # process JSON
        pks = [x for x in range(1, count + 1)]

        if len(uniq_keys):
            uniq_files = list(uniq(filelist, uniq_keys))
            count = len(uniq_files)
            zipped = zip(uniq_files, pks)
        else:
            zipped = zip(filelist, pks)

        for x in tqdm(
            zipped, total=count, desc=f"{model} ({count:,} objs)", leave=False
        ):
            yield dict(
                pk=x[1],
                model=model,
                fields=dict(**get_fields(x[0], translate=translate, rename=rename)),
            )

        return


def reset_fixture_dir(output) -> None:
    y = input(
        f"This command will automatically empty the fixture directory ({Path(output).absolute()}). Do you want to proceed? [y/N]"
    )
    if not y.lower() == "n":
        Path(output).mkdir(parents=True, exist_ok=True)
        return

    print("\nClearing up the fixture directory")
    Path(output).mkdir(parents=True, exist_ok=True)
    [x.unlink() for x in Path(output).glob("*.json")]


def get_translator(fields=[("", "", [])]):
    _ = dict()
    for field in fields:
        start, finish, lst = field
        part1, part2 = start.split("__")
        if not part1 in _:
            _[part1] = {}
        if not part2 in _[part1]:
            _[part1][part2] = {}
        if isinstance(finish, str):
            _[part1][part2] = {o["fields"][finish]: o["pk"] for o in lst}
        elif isinstance(finish, list):
            _[part1][part2] = {
                "-".join([o["fields"][x] for x in finish]): o["pk"] for o in lst
            }

    return _


def get_fields(file, translate={}, rename={}, allow_null=False):
    if isinstance(file, Path):
        try:
            fields = json.loads(file.read_text())
        except:
            print("here...")
            print(file)
            raise RuntimeError()
    elif isinstance(file, str):
        if "\n" in file:
            raise RuntimeError("File has new lines.")
        try:
            fields = json.loads(file)
        except json.decoder.JSONDecodeError as e:
            print(f"Cannot interpret JSON ({e}):")
            print(file)
            # try:
            #     print(file.read_text())
            # except:
            #     pass
            raise RuntimeError()
    elif isinstance(file, dict):
        fields = file
    else:
        raise RuntimeError(f"Cannot process type {type(file)}.")

    # fix relational fields for any file
    for key in [key for key in fields.keys() if "__" in key]:
        parts = key.split("__")

        try:
            before = fields[key]
            if before:
                before = before.replace("---", "/")
                loc = translate.get(parts[0], {}).get(parts[1], {})
                fields[key] = loc.get(before)
                if fields[key] == None:
                    raise RuntimeError(
                        f"Cannot translate fields.{key} from {before}: {loc}"
                    )

        except AttributeError:
            if allow_null:
                fields[key] = None
            else:
                print(
                    "Content had relational fields, but something went wrong in parsing the data:"
                )
                print("file", file)
                print("fields", fields)
                print("KEY:", key)
                raise RuntimeError()

        new_name = rename.get(parts[0], {}).get(parts[1], None)
        if new_name:
            fields[new_name] = fields[key]
            del fields[key]

    fields["created_at"] = NOW_str
    fields["updated_at"] = NOW_str
    try:
        fields["item_type"] = str(fields["item_type"]).upper()
    except KeyError:
        pass

    try:
        if fields["ocr_quality_mean"] == "":
            fields["ocr_quality_mean"] = 0
    except KeyError:
        pass

    try:
        if fields["ocr_quality_sd"] == "":
            fields["ocr_quality_sd"] = 0
    except KeyError:
        pass

    return fields


def save_fixture(generator=None, prefix="") -> None:
    internal_counter = 1
    counter = 1
    lst = []
    for item in generator:
        lst.append(item)
        internal_counter += 1
        if internal_counter > MAX_ELEMENTS_PER_FILE:
            Path(f"{OUTPUT}/{prefix}-{counter}.json").write_text(json.dumps(lst))

            # Save up some memory
            # del lst
            # gc.collect()

            # Re-instantiate
            lst = []
            internal_counter = 1
            counter += 1
    else:
        Path(f"{OUTPUT}/{prefix}-{counter}.json").write_text(json.dumps(lst))


def parse(collections, cache_home, output, max_elements_per_file):
    global CACHE_HOME
    global OUTPUT
    global MAX_ELEMENTS_PER_FILE

    CACHE_HOME = cache_home
    OUTPUT = output
    MAX_ELEMENTS_PER_FILE = max_elements_per_file

    # Set up output directory
    reset_fixture_dir(OUTPUT)

    # Get file lists
    print("\nGetting file lists...")
    issues_in_x = lambda x: "issues" in str(x.parent).split("/")
    newspapers_in_x = lambda x: not any(
        [
            condition
            for y in str(x.parent).split("/")
            for condition in [
                "issues" in y,
                "ingest" in y,
                "digitisation" in y,
                "data-provider" in y,
            ]
        ]
    )

    all_json = [
        x for y in collections for x in (Path(CACHE_HOME) / y).glob("**/*.json")
    ]
    all_jsonl = [
        x for y in collections for x in (Path(CACHE_HOME) / y).glob("**/*.jsonl")
    ]
    print(f"--> {len(all_json):,} JSON files altogether")
    print(f"--> {len(all_jsonl):,} JSONL files altogether")

    print("\nSetting up fixtures...")

    # Process data providers
    data_provider_in_x = lambda x: "data-provider" in str(x.parent).split("/")
    data_provider_json = list(
        fixtures(
            model="newspapers.dataprovider",
            filelist=[x for x in all_json if data_provider_in_x(x)],
            uniq_keys=["name"],
        )
    )
    print(f"--> {len(data_provider_json):,} DataProvider fixtures")

    # Process ingest
    ingest_in_x = lambda x: "ingest" in str(x.parent).split("/")
    ingest_json = list(
        fixtures(
            model="newspapers.ingest",
            filelist=[x for x in all_json if ingest_in_x(x)],
            uniq_keys=["lwm_tool_name", "lwm_tool_version"],
        )
    )
    print(f"--> {len(ingest_json):,} Ingest fixtures")

    # Process digitisation
    digitisation_in_x = lambda x: "digitisation" in str(x.parent).split("/")
    digitisation_json = list(
        fixtures(
            model="newspapers.digitisation",
            filelist=[x for x in all_json if digitisation_in_x(x)],
            uniq_keys=["software"],
        )
    )
    print(f"--> {len(digitisation_json):,} Digitisation fixtures")

    # Process newspapers
    newspaper_json = list(
        fixtures(
            model="newspapers.newspaper",
            filelist=[file for file in all_json if newspapers_in_x(file)],
        )
    )
    print(f"--> {len(newspaper_json):,} Newspaper fixtures")

    # Process issue
    translate = get_translator(
        [("publication__publication_code", "publication_code", newspaper_json)]
    )
    rename = {"publication": {"publication_code": "newspaper_id"}}

    issue_json = list(
        fixtures(
            model="newspapers.issue",
            filelist=[file for file in all_json if issues_in_x(file)],
            translate=translate,
            rename=rename,
        )
    )
    print(f"--> {len(issue_json):,} Issue fixtures")

    # Create translator/clear up memory before processing items
    translate = get_translator(
        [
            ("issue__issue_identifier", "issue_code", issue_json),
            ("digitisation__software", "software", digitisation_json),
            ("data_provider__name", "name", data_provider_json),
            (
                "ingest__lwm_tool_identifier",
                ["lwm_tool_name", "lwm_tool_version"],
                ingest_json,
            ),
        ]
    )

    rename = {
        "issue": {"issue_identifier": "issue_id"},
        "digitisation": {"software": "digitisation_id"},
        "data_provider": {"name": "data_provider_id"},
        "ingest": {"lwm_tool_identifier": "ingest_id"},
    }

    save_fixture(newspaper_json, "Newspaper")
    save_fixture(issue_json, "Issue")

    # del newspaper_json
    # del issue_json
    # gc.collect()

    print("\nSaving...")

    save_fixture(digitisation_json, "Digitisation")
    save_fixture(ingest_json, "Ingest")
    save_fixture(data_provider_json, "DataProvider")

    # Process items
    item_json = fixtures(
        model="newspapers.item",
        filelist=all_jsonl,
        translate=translate,
        rename=rename,
    )
    save_fixture(item_json, "Item")
