from warp.runtime import avatar_store, config

from schemup.orms import storm
from schemup import commands

stormSchema = storm.StormSchema()

def getWarpMigrationsDir(store=avatar_store):
    return config["warpDir"].child("migrations").child({
        "PostgresConnection": "postgres",
        # NTA FIX XXX: schemup does not support sqlite yet
        "SQLiteConnection": "sqlite",
        "MySQLConnection": "mysql"
    }[store._connection.__class__.__name__])

# NTA TODO: All DB-related config should be grouped together
def getSchemaConfig(config=config):
    schemaConfig = {
        "migrations_dir": config["siteDir"].child("migrations")
    }
    schemaConfig.update(config.get("schema", {}))
    return schemaConfig

def loadWarpMigrations(store=avatar_store):
    warpMigrationsDir = getWarpMigrationsDir(store)
    if not warpMigrationsDir.isdir():
        raise Exception("Warp migrations dir not found")
    commands.load(warpMigrationsDir.path)

def loadSiteMigrations(config=config):
    schemaConfig = getSchemaConfig(config)
    siteMigrationsDir = schemaConfig["migrations_dir"]
    # NTA TODO: Blow up otherwise?
    if siteMigrationsDir.isdir():
        commands.load(siteMigrationsDir.path)

def loadMigrations():
    loadWarpMigrations(avatar_store)
    loadSiteMigrations(config)
