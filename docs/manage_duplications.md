# Managing Potential Duplicate records

There are risks in saving records to `lwmdb` that could lead to duplicates. In a variety of cases [`unique=True`](https://docs.djangoproject.com/en/4.2/ref/models/fields/#unique) is set to prevent that, raising an [`IntegrityError`](https://docs.djangoproject.com/en/4.2/ref/exceptions/#django.db.IntegrityError) error if a duplicate record save is attempted. 

However, especially when records are loaded via [`loaddata`](https://docs.djangoproject.com/en/4.2/ref/django-admin/#loaddata), it is possible for duplicates to occur.

To address this, the `dupes_to_rm` function and `DupeRemoveConfig` `class` help ease the process of finding and removing duplicate records.

```pycon
>>> from newspapers.models import Newspaper
>>> from lwmdb.utils import dupes_to_rm, filter_by_null_fk
>>> dupes_to_check = dupes_to_rm(
...    qs_or_model=Newspaper,
...    dupe_fields=("publication_code",),
...    dupe_method=filter_by_null_fk,  # This is the default method
...    dupe_method_kwargs={"null_relations": ("issue",)},
... )
>>> dupes_to_check
<DupeRemoveConfig(model=<class 'newspapers.models.Newspaper'>, len=152, valid=True)>
>>> len(dupes_to_check.records_to_delete)
72
>>> len(dupes_to_check.records_to_keep)
72
```

In this case, the `Newspaper` `model` has 152 potential duplicate `publication_code` records saved. `dupes_to_rm` can aid finding these and checking with duplicates may make the most sense deleting.

`dupes_to_rm` takes a `Model` or `QuerySet` to check duplicates in, and a `tuple` passed to `dupe_fields` specifies with attributes to check. The `dupe_method` parameter (here using default `filter_by_null_fk`) then checkes which duplicates are best to keep and which could be deleted, using any additional parameters in `dupe_method_kwargs` (in this case a tuple `('issues',)` for the `'null_relations'` parameter).

Potential duplicates are then returned via instance of a `DupeRemoveConfig` `class`, using the parameters passed to `dupes_to_rm`. Simply printing that instances provides a summary, in this case a total of 152 records of `Newpaper` instances, and basic validity checks have passed.

In this example, the configuration will passed to `dupes_to_rm` successfully generate two additional attributes `records_to_delete` and `records_to_delete`. These are the retuls of applying `dupe_method` using the `dupe_method_kwargs` and other parameters in the original `dupes_to_rm` call. These results suggeste that there are 72 records that seem to be duplicates with `null` related `issues`, and 72 other records with existing related `issues`.

``` pycon
>>> for i, newspaper in enumerate(
...     dupes_to_check.records_to_delete.order_by('publication_code')[:8]
... ):
...     print(i, newspaper, newspaper.publication_code, newspaper.issues.count())
0 The Aberdeen Journal and General Advertiser for the North of Scotland 0000031 0
1 Aberdeen Weekly Journal and General Advertiser for the North of Scotland 0000032 0
2 Birmingham Daily Post 0000033 0
3 The Bristol Mercury, etc 0000034 0
4 The Bristol Mercury and Daily Post 0000035 0
5 Blackburn Standard 0000036 0
6 Blackburn Standard 0000038 0
7 Blackburn Standard 0000039 0
```

In the example above, the first 8 `dupes_to_check.records_to_delete` records are printed, including their `issues.count()`. In all these cases those counts are 0, indicating no other `Issue` records are saved as issues of each of those `Newspaper` records.


By contrast the example below indicates the records with the same `publication_code` values stored in the `dupes_to_check.records_to_delete` records, but with counts of related `Issue` instances `> 0`, which means they were correctly filtered by the `filter_by_null_fk` function used in this case.

``` pycon
>>> for i, newspaper in enumerate(
...     dupes_to_check.records_to_keep.order_by('publication_code')[:8]
... ):
...     print(i, newspaper, newspaper.publication_code, newspaper.issues.count())
0 The Aberdeen Journal 0000031 4507
1 Aberdeen Weekly Journal 0000032 8541
2 Birmingham Daily Post 0000033 11506
3 The Bristol Mercury 0000034 3185
4 The Bristol Mercury and Daily Post 0000035 6683
5 Baner Cymru 0000036 231
6 The Belfast News-Letter 0000038 22954
7 Brighton Patriot and Lewes Free Press etc 0000039 72
```

To these potential duplicates side by side, the `all_dupe_records` attribute is ordered with that in mind, showing the pairs of `Newspaper` records with the same `publication_code` alongside each other:

```pycon
>>> for i, newspaper in enumerate(
...     all_dupe_records.records_to_keep.order_by('publication_code')[:16]
... ):
...     print(i, newspaper, newspaper.publication_code, newspaper.issues.count())
0 The Aberdeen Journal and General Advertiser for the North of Scotland 0000031 0
1 The Aberdeen Journal 0000031 4507
2 Aberdeen Weekly Journal and General Advertiser for the North of Scotland 0000032 0
3 Aberdeen Weekly Journal 0000032 8541
4 Birmingham Daily Post 0000033 0
5 Birmingham Daily Post 0000033 11506
6 The Bristol Mercury, etc 0000034 0
7 The Bristol Mercury 0000034 3185
8 The Bristol Mercury and Daily Post 0000035 0
9 The Bristol Mercury and Daily Post 0000035 6683
10 Blackburn Standard 0000036 0
11 Baner Cymru 0000036 231
12 Blackburn Standard 0000038 0
13 The Belfast News-Letter 0000038 22954
14 Blackburn Standard 0000039 0
15 Brighton Patriot and Lewes Free Press etc 0000039 72

```
