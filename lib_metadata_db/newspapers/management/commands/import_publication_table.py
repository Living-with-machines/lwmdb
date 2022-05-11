from lib_metadata_db.press_directories.models.mitchells import Mitchells
from django.core.management import BaseCommand
import pandas as pd
import numpy as np

# Import the model


ALREDY_LOADED_ERROR_MESSAGE = """
If you need to reload the child data from the CSV file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""




class Command(BaseCommand):
    # Show this when the user types help
    help = "Loads data from Mitchells press directories"

    def add_arguments(self, parser):
        parser.add_argument("file_location", type=str, help="Indicates the location of the file to upload.")

    def handle(self, *args, **kwargs):

        # Show this if the data already exist in the database
        if MitchellsPublication.objects.exists():
            print('Mitchell record already loaded...exiting.')
            print(ALREDY_LOADED_ERROR_MESSAGE)
            return

        # Show this before loading the data into the database
        print("Loading Mitchells press directories.")

        #data = pd.read_csv('../data/mitchells_db.csv')
        data = pd.read_csv(kwargs["file_location"])
        data.replace({np.nan: None},inplace=True)
        #data.fillna('',inplace=True)
        #Code to load the data into database
        for i,row in data.iterrows():
            record=MitchellsPublication(year=row['AcquiredYears'], mitchells=row['link_to_mpd'],
                            #place_of_publication_id=row['place_of_publication_id']
            				)
            record.save()
