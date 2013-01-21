from twisted.python import log

from storm.locals import *
from storm.uri import URI
from storm.exceptions import DatabaseError

from warp.runtime import avatar_store, config, sql

def setupStore():
    avatar_store.__init__(create_database(config['db']))

    if config.get('trace'):
        import sys
        from storm.tracer import debug
        debug(True, stream=sys.stdout)

    # Only sqlite uses this now
    sqlBundle = getCreationSQL(avatar_store)
    if not sqlBundle:
        return

    tableExists = sql['tableExists'] = sqlBundle['tableExists']

    for (table, creationSQL) in sqlBundle['creations']:

        if not tableExists(avatar_store, table):

            # Unlike log.message, this works during startup
            print "~~~ Creating Warp table '%s'" % table

            if not isinstance(creationSQL, tuple): creationSQL = [creationSQL]
            for sqlCmd in creationSQL: avatar_store.execute(sqlCmd)
            avatar_store.commit()


def getCreationSQL(store):
    connType = store._connection.__class__.__name__
    return {
        'SQLiteConnection': {
            'tableExists': lambda s, t: bool(s.execute("SELECT count(*) FROM sqlite_master where name = '%s'" % t).get_one()[0]),
            'creations': [
                ('warp_avatar', """
                CREATE TABLE warp_avatar (
                    id INTEGER NOT NULL PRIMARY KEY,
                    email VARCHAR,
                    password VARCHAR,
                    UNIQUE(email))"""),
                ('warp_session', """
                CREATE TABLE warp_session (
                    uid BYTEA NOT NULL PRIMARY KEY,
                    avatar_id INTEGER REFERENCES warp_avatar(id) ON DELETE CASCADE)"""),
                ('warp_avatar_role', """
                CREATE TABLE warp_avatar_role (
                    id INTEGER NOT NULL PRIMARY KEY,
                    avatar_id INTEGER NOT NULL REFERENCES warp_avatar(id) ON DELETE CASCADE,
                    role_name BYTEA NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0)"""),
                ],
            }
    }.get(connType)
