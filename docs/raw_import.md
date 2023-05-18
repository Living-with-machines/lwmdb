# 


## Order of import


### Newspapers

### Post Newspapers

!!! note

    It may be possible to run some alongside each other like:

    ```console
    python manage.py createfixtures gazetteer mitchells
    ```

General workflow -> process data to `json`, then import as fixtures

Output path for fixture loading

```python
settings.BASE_DIR / Path(f"{app_name}/fixtures")
```

#### Gazzetteers

Generates `.json files`

```console
python manage.py createfixtures gazetteer
```

Result from gazetteer `createfixtures` script: 

- `HistoricCounty-fixtures.json`
- `AdminCounty-fixtures.json`
- `Place-fixtures.json`

#### Mitchells

- `EntryPoliticalLeanings-fixtures.json`
- `EntryPrices-fixtures.json`
- `Issue-fixtures.json`
- `PoliticalLeaning-fixtures.json`
- `Price-fixtures.json`
- `Entry-fixtures.json`

#### Census

Connects to gazetteer records

Is more of a script, it *doesn't* address process of `json` exports.

- NOT public
- WGS84: https://gisgeography.com/wgs84-world-geodetic-system/
- Wikidata coordinate system
- Ask Mariona
