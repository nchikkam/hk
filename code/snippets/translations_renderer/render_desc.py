#render_desc.py


from operator import attrgetter
import re

from django.db import transaction
from django.core.management.base import BaseCommand

from psycopg2 import connect


from plib.models import Process

from ._utils import CONNECT_STRING
 
_BLOCK_RE = re.compile('\[%(.*?)%\]')
_FIELD_RE = re.compile('\[([^\[]*?)\]')


def _transform_values(f, d):
    for k, v in d.items():
        d[k] = f(v)

def _strip_r(s):
    return s.replace('\\r', ' ')

def _process_type(p):
    if p.name.endswith('.dll'):
        return 'module'
    return 'process'


_FIELDS = {
    # actual fields
    'filename':                     attrgetter('name'),
    'author.authorname':            attrgetter('author'),
    'processname':                  attrgetter('long_name'),
    'partof.suitename':             attrgetter('application'),
    'processtype.processtypename':  _process_type,
}


class DescriptionRenderer(object):

    _QUERY = """
    select
        templatename,
        templatetext
    from
        processlibrary.inputtemplate
    ;
    """

    def __init__(self):
        self._insert_blocks = self._get_insert_blocks()
        self.bad_fields = set()

    def render(self, process):
        intermediate = self._insert_blocks(process.description)
       
        def _insert_field(match):
            key = match.group(1).strip()
            if key in _FIELDS:
                return _FIELDS[key](process)
            self.bad_fields.add(key)
            return '[%s]' % key


        return _FIELD_RE.sub(_insert_field, intermediate)

    def _get_insert_blocks(self):
        conn = connect(CONNECT_STRING)
        cursor = conn.cursor()
        cursor.execute(self._QUERY)
        templates = dict(cursor.fetchall())
        _transform_values(_strip_r, templates)

        def _insert_block(match):
            return templates[match.group(1).strip()]

        def _insert_blocks(s):
            while True:
                s_ = _BLOCK_RE.sub(_insert_block, s)
                if s == s_:
                    return s
                s = s_

        _transform_values(_insert_blocks, templates)
        return _insert_blocks


class Command(BaseCommand):
    """
    Render decription from old db template
    """
   
    @transaction.commit_on_success
    def handle(self, **_):
        renderer = DescriptionRenderer()
        render = renderer.render
        print 'loaded templates'

        processes = Process.objects.all()
        total = len(processes)
        print 'rendering %s descriptions...' % total
       
        i = 0
        for process in processes:
            i += 1
            process.description = render(process)
            process.save()

            if not i % 100:
                print 'transformed %s records (of %s)' % (i, total)

        print 'finished!'
        print 'ignored not-really-fields:'
        for k in sorted(renderer.bad_fields):
            print repr(k)


