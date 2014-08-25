#populatedb.py

import codecs
from collections import namedtuple

from django.db import transaction
from django.core.management.base import BaseCommand

from psycopg2 import connect


from plib.models import Process

from ._utils import cache, CONNECT_STRING

_FIELDS = 'id name long_name description is_primary danger author application'

_Row = namedtuple('_Row', _FIELDS)

_QUERY = """
select
    pl.pl.plid as %s,
    pl.pl.filename as %s,
    pl.pl.processname as %s,
    pl.pl.description as %s,
    pl.pl.isprimary as %s,
    pl.pl.securityrisk as %s,
    pl.author.authorname as %s,
    pl.partof.suitename as %s

from
    pl.pl,
    pl.author,
    pl.partof

where
    pl.pl.authorid = pl.author.authorid and
    pl.pl.partofid = pl.partof.partofid
;
""" % _Row._fields


@cache
def _get_or_create(cls, **kwargs):
    return cls.objects.get_or_create(**kwargs)[0]

_EXT_PRIORITIES = 'rll dll exe'.split()
def _ext_priority(ext):
    try:
        return _EXT_PRIORITIES.index(ext)
    except ValueError:
        return -1

class Command(BaseCommand):
    """
    Perform initial import of old pl data.

    Important things it *doesn't* do include:

      * render descriptions (use render_descriptions)
      * set common locations (use get_locations)
      * do anything with keywords (use get_keywords)
    """
   
    @transaction.commit_on_success
    def handle(self, **_):
        conn = connect(CONNECT_STRING)
        cursor = conn.cursor()
        cursor.execute(_QUERY)
        total = cursor.rowcount
        print 'reading %s records...' % total
       
        best_names = {}
        i = 0
        while True:
            result = cursor.fetchone()
            if result is None:
                break

            i += 1
            row = _Row(*result)
            process = Process.objects.create(
                id=row.id,
                name=row.name,
                danger=row.danger,
                long_name=row.long_name,
                description=row.description,
                author=row.author,
                application=row.application,
            )
            if row.is_primary:
                best_names[process.name] = process.id
           
            if not i % 100:
                print 'imported %s records (of %s)' % (i, total)

        print 'determining primary process by namebase...'
        best_namebases = {}
        for name, id_ in best_names.items():
            if '.' in name:
                namebase, extension = name.rsplit('.', 1)
                priority = _ext_priority(extension)
            else:
                namebase, priority = name, -1

            old_best = best_namebases.get(namebase, (-2, -1))
            best_namebases[namebase] = max((priority, id_), old_best)
           
        print 'writing %s primary processes' % len(best_namebases)
        with codecs.open('namebases.txt', 'w', 'utf-8') as f:
            for namebase, (_, id_) in best_namebases.items():
                f.write('%s||%s\n' % (namebase, id_))

        print 'finished!'


