# Accessing full-text using `extract_fulltext` method

We are developing a fulltext table for all articles across our available newspapers. Meanwhile, @thobson88 has developed an `.extract_fulltext()` method that can be used on any `Item` objects. Here is an example:

```python
from newspapers.models import Newspaper
from newspapers.models import Item
from pathlib import Path

# Set the local download path:
Item.DOWNLOAD_DIR = Path.home() / "temp/fulltext"

# Set the SAS token:
%env FULLTEXT_SAS_TOKEN="?sv=2021-06-08&ss=bfqt&srt=sco&sp=rtf&se=2022-10-04T17:49:53Z&st=2022-10-04T09:49:53Z&sip=82.16.244.16&spr=https&sig=Kp6QEtqWw5NlJZx4r0eddSxfjqXzXEeY0pwoii%2Fz86E%3D"

item = Newspaper.objects.get(publication_code="0003040").issues.first().items.first()
item.extract_fulltext()
```

If you need help setting up a SAS token, see [instructions here](https://github.com/Living-with-machines/fulltext#sas-token-creation).

_Please note, access via Blobfuse is planned but not yet implemented._
