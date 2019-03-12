import os
import re
try:
    import simplejson as json
except ImportError:
    import json
import sqlite3
from cab.utils.c_log import init_log
from cab.utils.machine_info import get_machine_id, \
    get_cur_time, get_config, \
    get_machine_version
from cab.utils.utils import get_db_uuid
from cab.db.dbm import DB


log = init_log("db_verify", count=1)


def escape_algorithm(algorithm):
    return algorithm.replace("&", "&amp;").replace("<", "&lt;").\
        replace('"', "&quot;").replace("'", "&apos;")

# =============================================================================
# Class SchemaTools
# -----------------------------------------------------------------------------


SQL_DIVIDER = '--------------------'


class SchemaTools():
    '''
    Tools that help to fortify a db with a new schema
    '''

    def __init__(self, con):
        self.con = con

    def fortify(self, schema):
        schema = schema.strip(' \n')
        try:
            entity_type = self.get_entity_type(schema).upper()
        except Exception:
            entity_type = 'invalid'

        if entity_type == 'TABLE':
            return self.fortify_table(schema)
        elif entity_type == 'TRIGGER':
            return self.fortify_trigger(schema)
        elif entity_type == 'INDEX':
            return self.fortify_index(schema)
        else:
            return 'invalid'

    def fortify_table(self, schema):
        '''creates/updates a table with schema'''
        table_name = self.get_entity_name(schema)
        row = self.con.execute("SELECT sql FROM sqlite_master "
                               "WHERE type='table' AND "
                               "name='%s';" % (table_name,)).fetchone()
        if row:
            # table exists
            old_schema = row[0].strip(";")
            new_sSchema = schema.strip(";")
            if old_schema == new_sSchema:
                return 'original'
            else:
                old_fields = self.get_table_fields(old_schema)
                new_fields = self.get_table_fields(new_sSchema)
                common_fields = [field for field in new_fields
                                 if field in old_fields]

                # rename old table to temp
                sql = "ALTER TABLE %s RENAME TO temp;" % (table_name,)
                self.con.execute(sql)

                # create new table
                self.con.execute(schema)

                # copy data from common fields from old table to new table
                fieldsStr = ','.join(common_fields)
                sql = "INSERT INTO %s(%s) SELECT %s FROM temp;" \
                    % (table_name, fieldsStr, fieldsStr)
                self.con.execute(sql)

                # drop temp table
                sql = "DROP TABLE temp;"
                self.con.execute(sql)
                self.con.commit()

                return 'altered'
        else:
            # table does not exist, create new from schema
            self.con.execute(schema)
            self.con.commit()
            return 'new'

    def fortify_trigger(self, schema):
        trigger_name = self.get_entity_name(schema)
        row = self.con.execute("SELECT sql FROM sqlite_master "
                               "WHERE type='trigger' and "
                               "name='%s';" % (trigger_name,)).fetchone()
        if row:
            # trigger exists
            old_schema = row[0].strip(";")
            new_schema = schema.strip(";")
            if old_schema == new_schema:
                return 'original'
            else:
                self.con.execute('DROP TRIGGER %s;' % (trigger_name,))
                self.con.execute(schema)
                self.con.commit()
                return 'altered'
        else:
            # triggere does not exist, create new from schema
            self.con.execute(schema)
            self.con.commit()
            return 'new'

    def fortify_index(self, schema):
        index_name = self.get_entity_name(schema)
        row = self.con.execute("SELECT sql FROM sqlite_master "
                               "WHERE type='index' and "
                               "name='%s';" % (index_name,)).fetchone()
        if row:
            # index exists
            old_schema = row[0].strip(";")
            new_schema = schema.strip(";")
            if old_schema == new_schema:
                return 'original'
            else:
                self.con.execute('DROP INDEX %s;' % (index_name,))
                self.con.execute(schema)
                self.con.commit()
                return 'altered'
        else:
            # indexere does not exist, create new from schema
            self.con.execute(schema)
            self.con.commit()
            return 'new'

    def get_entity_type(self, schema):
        regex = re.compile(r"^\s*create\s+((?:table)|(?:index)|(?:trigger))",
                           re.I)
        result = regex.findall(schema)
        if len(result) > 0:
            return result[0].lower()
        else:
            return None

    def get_entity_name(self, schema):
        regex = re.compile(r"^\s*create\s+(?:(?:table)|(?:index)|"
                           r"(?:trigger))\s+[\[\']?(\w+)[\[\']?", re.I)
        result = regex.findall(schema)
        if len(result) > 0:
            return result[0].lower()
        else:
            return None

    def get_table_fields(self, schema):
        # search for fields enclosed in a pair of parenthesis
        regex = re.compile(r".*\((.*)\).*", re.I | re.S)
        result = regex.findall(schema)
        fields = []
        if len(result) > 0:
            for s in result[0].split("\n"):
                field = s.strip()
                if field:
                    fields.append(field.split()[0])
        return fields

    def fortify_many(self, sql):
        '''fortify multiple schemas'''
        schemas = sql.split(SQL_DIVIDER)
        for schema in schemas:
            if schema.strip(' \n'):
                self.fortify(schema)


class CkcDb():

    def __init__(self, ckc_db_path, sync_db_path):
        self.con = sqlite3.connect(
            ckc_db_path, isolation_level="IMMEDIATE", timeout=5.0)
        self.cur = self.con.cursor()
        self.db = DB(ckc_db_path, sync_db_path)

    def verify_db(self):
        self._validate_db()
        self._load_config()
        self._load_info()
        self._load_slots()

    def _validate_db(self):
        '''Initializes and creates a database'''
        schema_tools = SchemaTools(self.con)

        sql = """CREATE TABLE machine_config
(
    id_ai INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    id TEXT,
    machine_id TEXT,
    key TEXT UNIQUE NOT NULL,
    value TEXT DEFAULT '',
    last_update_time TEXT
);"""
        rev = schema_tools.fortify(sql)
        log.info(rev + " machine_config")

        sql = """CREATE TABLE machine_info
(
    id_ai INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    id TEXT,
    machine_id TEXT,
    key TEXT UNIQUE NOT NULL,
    value TEXT DEFAULT '',
    last_update_time TEXT,
    inactive_reason TEXT DEFAULT ''
);"""
        rev = schema_tools.fortify(sql)
        log.info(rev + " machine_info")

        sql = '''CREATE TABLE flags (
        key           TEXT PRIMARY KEY,
        value         TEXT
        )
    '''

        rev = schema_tools.fortify(sql)
        log.info(rev + " flags")

        sql = """CREATE TABLE custom_content
(
    id_ai INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    id TEXT,
    publish_name TEXT,
    content_type INTEGER,
    position TEXT,
    content_id_zh_cn TEXT,
    content_name_zh_cn TEXT,
    file_name_zh_cn TEXT,
    content_id_en_us TEXT,
    content_name_en_us TEXT,
    file_name_en_us TEXT,
    start_time TEXT,
    end_time TEXT,
    publish_time TEXT,
    status INTEGER
);"""
        rev = schema_tools.fortify(sql)
        log.info(rev + " custom_content")

        sql = """CREATE TABLE transations
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            trans_id  TEXT,
            status  INTEGER
        );"""
        rev = schema_tools.fortify(sql)
        log.info(rev + " transations")

    def _load_info(self):
        self.cur.execute("SELECT key FROM machine_info;")
        rows = self.cur.fetchall()
        c_info = [row[0] for row in rows]    # current info

        infos = []
        infos.append(("kiosk_id", ""))
        infos.append(("external_ip", ""))
        infos.append(("internal_ip", ""))
        infos.append(("mac", ""))
        infos.append(("software", get_machine_version()))
        infos.append(("upgrade_time", ""))
        infos.append(("firmware", ""))
        infos.append(("timezone", ""))
        infos.append(("start_time", ""))
        infos.append(("printer_status", ""))
        infos.append(("inactive_reason", ""))

        # verify
        machine_id = get_machine_id()
        now = get_cur_time()
        add_list = []
        for info in infos:
            if info[0] not in c_info:
                _id = get_db_uuid()
                param = (_id, machine_id, info[0], info[1], now)
                add_list.append(param)

        if add_list:
            self.db.add_kv("machine_info", add_list)

    def _load_slots(self):
        pass

    def _load_config(self):
        self.cur.execute("SELECT key FROM machine_config;")
        rows = self.cur.fetchall()
        c_config = [row[0] for row in rows]    # current config

        configs = []
        configs.append(("general_policy", "{}"))
        # verify
        machine_id = get_machine_id()
        now = get_cur_time()
        add_list = []
        for config in configs:
            if config[0] not in c_config:
                _id = get_db_uuid()
                param = (_id, machine_id, config[0], config[1], now)
                add_list.append(param)

        if add_list:
            self.db.add_kv("machine_config", add_list)


class SyncDb:

    def __init__(self, sync_db_path):
        self.con = sqlite3.connect(
            sync_db_path, isolation_level="IMMEDIATE", timeout=5.0)
        self.cur = self.con.cursor()

    def verify_db(self):
        self._validate_db()

    def _validate_db(self):
        '''Initializes and creates a database'''
        schema_tools = SchemaTools(self.con)

        sql = """CREATE TABLE sync
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    service TEXT,
    module TEXT,
    func TEXT,
    params TEXT,
    sequence INTEGER DEFAULT 1,
    add_time TEXT,
    sync_time TEXT,
    state INTEGER DEFAULT 0
);"""
        rev = schema_tools.fortify(sql)
        log.info(rev + " db_sync")


def verify_db():
    config = get_config("ckc")
    ckc_db_path = config.get("db", "ckc_db")
    sync_db_path = config.get("db", "sync_db")

    # check the dir
    db_path = os.path.dirname(ckc_db_path)
    if not os.path.exists(db_path):
        os.makedirs(db_path)

    syncDb = SyncDb(sync_db_path)
    syncDb.verify_db()

    mkcDb = CkcDb(ckc_db_path, sync_db_path)
    mkcDb.verify_db()


if __name__ == "__main__":
    verify_db()

    print("Done")
