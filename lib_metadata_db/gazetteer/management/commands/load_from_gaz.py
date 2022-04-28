import pandas as pd
import json
from ast import literal_eval

from django.core.management import BaseCommand

# from lib_metadata_db.gazetteer.models.admin_county import AdminCounty
# from lib_metadata_db.gazetteer.models.country import Country
# from lib_metadata_db.gazetteer.models.historic_county import HistoricCounty
# from lib_metadata_db.gazetteer.models.place_of_publication import PlaceOfPublication

ALREDY_LOADED_ERROR_MESSAGE = """
    If you need to reload the child data from the CSV file,
    first delete the db.sqlite3 file to destroy the database.
    Then, run `python manage.py migrate` for a new empty
    database with tables
    """


# --------------------------------------
# Load historic counties manual mapping
# This dictionary manually links the `place_wikidata_id` in `place_of_publication`
# to the historic county (as a string and a wikidata ID). We should load this
# from a json.
with open("../../import_files/dict_historic_counties.json") as json_file:
    dict_historic_counties = json.load(json_file)


# --------------------------------------
# Load admin counties manual mapping
# This dictionary manually links the `place_wikidata_id` in `place_of_publication`
# to the administrative county (as a string and a wikidata ID). We should load this
# from a json.
with open("../../import_files/dict_admin_counties.json") as json_file:
    dict_admin_counties = json.load(json_file)


# --------------------------------------
# Load countries manual mapping
# This dictionary manually links the `place_wikidata_id` in `place_of_publication`
# to the curren country (as a string and a wikidata ID). We should load this
# from a json.
with open("../../import_files/dict_countries.json") as json_file:
    dict_countries = json.load(json_file)


# --------------------------------------
# Load countries manual mapping
# Load list of places of publication (Wikidata IDs) in Mitchells.
with open("../../import_files/wikidata_ids_publication_mitchells.txt") as file:
    list_mitchells_wqid = file.readlines()
list_mitchells_wqid = [wq.strip() for wq in list_mitchells_wqid if wq.startswith("Q")]

# --------------------------------------
# Load gazetteer
df = pd.read_csv(
    "../../import_files/wikidata_gazetteer.csv",
    low_memory=False,
    usecols=[
        "wikidata_id",
        "english_label",
        "latitude",
        "longitude",
        "geonamesIDs",
    ],
)


def literal_return(val):
    try:
        return literal_eval(val)
    except ValueError:
        return val


df["geonamesIDs"] = df["geonamesIDs"].apply(literal_return)


# --------------------------------------
# Filter gazetteer with accepted locations
dict_gaz_entries = dict()
for i, row in df.iterrows():
    if row["wikidata_id"] in list_mitchells_wqid:
        dict_gaz_entries[row["wikidata_id"]] = {
            "place_wikidata_id": row["wikidata_id"],
            "place_label": row["english_label"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "geonames_ids": row["geonamesIDs"],
            "historic_county": dict_historic_counties.get(row["wikidata_id"], ""),
            "admin_county": dict_admin_counties.get(row["wikidata_id"], ""),
            "country": dict_countries.get(row["wikidata_id"], ""),
        }


# End of loading data
# --------------------------------------


# --------------------------------------
# class Command(BaseCommand):
#     def handle(self, *args, **options):
#         if PlaceOfPublication.objects.exists():
#             print("child data already loaded...exiting.")
#             print(ALREDY_LOADED_ERROR_MESSAGE)
#             return

#         # Show this before loading the data into the database
#         print("Loading places data")

#         # Code to load the data into database
#         for wkqid in dict_gaz_entries:
#             historic_county = HistoricCounty(
#                 admin_county_wikidata_id = dict_gaz_entries[wkqid]["place_wikidata_id"]["hcounty_wikidata_id"][0]
#                 admin_county_label = dict_gaz_entries[wkqid]["place_wikidata_id"]["historic_county"][1]
#             )
#             historic_county.save()
#             admin_county = HistoricCounty(
#                 hcounty_wikidata_id = dict_gaz_entries[wkqid]["place_wikidata_id"]["hcounty_wikidata_id"][0]
#                 hcounty_label = dict_gaz_entries[wkqid]["place_wikidata_id"]["historic_county"][1]
#             )
#             admin_county.save()
#             country = Country(
#                 country_wikidata_id = dict_gaz_entries[wkqid]["place_wikidata_id"]["country"][0]
#                 country_label = dict_gaz_entries[wkqid]["place_wikidata_id"]["country"][1]
#             )
#             country.save()
#             place_of_publication = PlaceOfPublication(
#                 place_wikidata_id=dict_gaz_entries[wkqid]["place_wikidata_id"],
#                 place_label=dict_gaz_entries[wkqid]["place_label"],
#                 latitude=dict_gaz_entries[wkqid]["latitude"],
#                 longitude=dict_gaz_entries[wkqid]["longitude"],
#                 geonames_ids=dict_gaz_entries[wkqid]["geonames_ids"],
#                 admin_county="historic_county",
#                 admin_county="admin_county",
#                 admin_county="country",
#             )
#             place_of_publication.save()
