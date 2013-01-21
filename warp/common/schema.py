from warp.runtime import avatar_store, config

from schemup.orms import storm
from schemup import commands, validator

# NTA TODO: Maybe load once?

stormSchema = storm.StormSchema()

def getWarpMigrationsDir(store=avatar_store):
    return config["warpDir"].child("migrations").child({
        "PostgresConnection": "postgres",
        # NTA FIX XXX: schemup does not support sqlite yet
        "SQLiteConnection": "sqlite",
        "MySQLConnection": "mysql"
    }[store._connection.__class__.__name__])

def getClass(store=avatar_store):
    name = store._connection.__class__.__name__
    if name == "PostgresConnection":
        from schemup.dbs.postgres import PostgresSchema
        return PostgresSchema
    elif name == "MySQLConnection":
        from schemup.dbs.mysql import MysqlSchema
        return MysqlSchema
    else:
        raise Exception("Unsupported DB")

def makeSchema(store=avatar_store, dryRun=False):
    schemaClass = getClass()
    # return schemaClass(store._connection._raw_connection, dryRun=dryRun)
    return schemaClass(store.get_database().raw_connect(), dryRun=dryRun)

# NTA TODO: All DB-related config should be grouped together
def getConfig(config=config):
    schemaConfig = {
        # Directory storing site's DB migrations
        # (twisted.python.filepath.FilePath)
        "migrations_dir": config["siteDir"].child("migrations"),
        # Whether to check schema on startup
        "check": True,
    }
    schemaConfig.update(config.get("schema", {}))
    return schemaConfig



def loadWarpMigrations(store=avatar_store):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "Loading warp migrations"
    warpMigrationsDir = getWarpMigrationsDir(store)
    if not warpMigrationsDir.isdir():
        raise Exception("Warp migrations dir not found")
    commands.load(warpMigrationsDir.path)

def loadSiteMigrations(config=config):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "Loading site migrations"
    schemaConfig = getConfig(config)
    siteMigrationsDir = schemaConfig["migrations_dir"]
    # NTA TODO: Blow up otherwise?
    if siteMigrationsDir.isdir():
        commands.load(siteMigrationsDir.path)

def loadMigrations(store=avatar_store, config=config):
    loadWarpMigrations(avatar_store)
    loadSiteMigrations(config)



def snapshot(store=avatar_store, config=config, dryRun=False):
    schema = makeSchema(store, dryRun)
    loadMigrations(store, config)

    schema.ensureSchemaTable()
    commands.snapshot(schema, stormSchema)

def migrate(store=avatar_store, config=config, dryRun=False):
    schema = makeSchema(store, dryRun)
    schema.ensureSchemaTable()

    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "Checking schema integrity"
    # Make sure the real schema is what schemup_tables says it is
    mismatches = validator.findSchemaMismatches(schema)
    # NTA TODO: Pretty print
    if mismatches:
        print "Real schema & 'schemup_tables' are out of sync (did you change the schema outside of schemup?):"
        for mismatch in mismatches:
            print mismatch, "\n"
        raise Exception("Schema mismatches")

    loadMigrations(store, config)

    sqls = commands.upgrade(schema, stormSchema)
    if dryRun and sqls:
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        for sql in sqls: print sql
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

    # Sanity checking
    commands.validate(schema, stormSchema)

    if not dryRun:
        if sqls:
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "Migrated successfully"
        else:
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "Schema up-to-date"
