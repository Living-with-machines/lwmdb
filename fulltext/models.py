from django.db import models


class Fulltext(models.Model):
    """Optical Charater Recognition newspaper `Item` body text.

    Attributes:
        text:
            plain text from an article
        compressed_path:
            path to zip file  (if used).
        path:
            path to `plaintext` (`txt`) source file (if used). If
            `self.compressed_path` is set, then `path` is to relevant
            `txt` file when `self.compressed_path` is uncompressed
        created_at:
            date and time the record is created. This can also be
            provided by a fixture, for example via `alto2txt2fixture`
        updated_at:
            date and time the record is last updated. This can also
            be provided by a fixture, example via `alto2txt2fixture`.
            This can help keep track of the timing of any changes
            after, for example, an import from an `alto2txt2fixture`
            `json` fixture file.
        errors:
            `str` records of any logged errors generating this `Fulltext`.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> item_fulltext = Fulltext(
        ...     compressed_path='0003548_plaintext.zip',
        ...     path='0003548/1904/0707/0003548_19040707_art0037.txt',
        ...     fixture_path='fulltext/fixtures/plaintext_fixture-38884.json',
        ... )
        >>> item_fulltext.save()
        >>> from newspapers.models import Item
        >>> new_tredegar_item: Item = getfixture("new_tredegar_last_issue_first_item")
        Installed 5 object(s) from 1 fixture(s)
        >>> new_tredegar_item.fulltext = item_fulltext
        >>> new_tredegar_item.save()

        ```
    """

    text = models.TextField()
    path = models.CharField(max_length=200, blank=True, null=True)
    compressed_path = models.CharField(max_length=200, blank=True, null=True)
    errors = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
