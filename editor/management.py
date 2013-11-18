from django.db.models.signals import post_syncdb
from django.db import connection, transaction

# WEIRD:  from myapp import models --> does not work
# post_syncdb.connect needs a reference starting from the project...
from editor import models

# Set name field to be BINARY, to force case-sensitive comparisons
def set_urlhash_to_binary(sender, **kwargs):
    cursor = connection.cursor()
    cursor.execute('ALTER TABLE editor_project MODIFY urlhash VARCHAR(50) BINARY NOT NULL')
    transaction.commit_unless_managed()

post_syncdb.connect(set_urlhash_to_binary, sender=models)