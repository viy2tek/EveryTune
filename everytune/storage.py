import json
import os
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import median

from .models import Settings, SourcePage


def data_directory() -> Path:
    if os.getenv("EVERYTUNE_DATA_DIR"):
        return Path(os.environ["EVERYTUNE_DATA_DIR"]).expanduser().resolve()
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData/Local")) if sys.platform == "win32" else Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "EveryTune"


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "everytune.sqlite3"
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, expires REAL, value TEXT);
            CREATE TABLE IF NOT EXISTS history (query TEXT PRIMARY KEY, at REAL);
            CREATE TABLE IF NOT EXISTS logs (at REAL, source TEXT, status TEXT);
            CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS measurements (kind TEXT, at REAL, value TEXT);
        """)
        self.db.commit()
        if sys.platform != "win32":
            directory.chmod(0o700)
            self.path.chmod(0o600)

    def settings(self) -> Settings:
        row = self.db.execute("SELECT value FROM settings WHERE id=1").fetchone()
        return Settings.model_validate_json(row[0]) if row else Settings()

    def save_settings(self, settings: Settings):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (1, ?)", (settings.model_dump_json(),))

    def get(self, key: str) -> SourcePage | None:
        row = self.db.execute("SELECT value FROM cache WHERE key=? AND expires>?", (key, time.time())).fetchone()
        return SourcePage.model_validate_json(row[0]) if row else None

    def put(self, key: str, page: SourcePage, ttl: int):
        with self.db:
            self.db.execute("DELETE FROM cache WHERE expires<?", (time.time(),))
            self.db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (key, time.time() + ttl, page.model_dump_json()))
            self.db.execute("DELETE FROM cache WHERE key IN (SELECT key FROM cache ORDER BY expires DESC LIMIT -1 OFFSET 2000)")

    def clear_cache(self):
        with self.db:
            self.db.execute("DELETE FROM cache")

    def remember(self, query: str):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO history VALUES (?, ?)", (query, time.time()))
            self.db.execute("DELETE FROM history WHERE query IN (SELECT query FROM history ORDER BY at DESC LIMIT -1 OFFSET 100)")

    def history(self):
        return [r[0] for r in self.db.execute("SELECT query FROM history ORDER BY at DESC LIMIT 12")]

    def log(self, source: str, status: str):
        with self.db:
            self.db.execute("INSERT INTO logs VALUES (?, ?, ?)", (time.time(), source, status))
            self.db.execute("DELETE FROM logs WHERE rowid NOT IN (SELECT rowid FROM logs ORDER BY rowid DESC LIMIT 200)")

    def logs(self):
        return [dict(zip(("at", "source", "status"), r)) for r in self.db.execute("SELECT at, source, status FROM logs ORDER BY rowid DESC LIMIT 100")]

    def close(self):
        self.db.close()

    def measure(self, kind, value):
        with self.db:
            self.db.execute('INSERT INTO measurements VALUES (?,?,?)',(kind,time.time(),json.dumps(value)))
            self.db.execute('DELETE FROM measurements WHERE kind=? AND rowid NOT IN (SELECT rowid FROM measurements WHERE kind=? ORDER BY rowid DESC LIMIT 500)',(kind,kind))

    def clear_coverage(self):
        with self.db:self.db.execute('DELETE FROM measurements')

    def coverage(self):
        searches=[];downloads=Counter();sources={}
        def source(id):
            return sources.setdefault(id,{'source':id,'attempts':0,'with_audio':0,'cached':0,'statuses':Counter(),'diagnostics':Counter(),'downloads':Counter()})
        for kind,at,value in self.db.execute('SELECT kind,at,value FROM measurements ORDER BY rowid'):
            row=json.loads(value)
            if kind=='search':
                searches.append(row)
                for result in row['sources']:
                    item=source(result['source']);item['attempts']+=1
                    item['with_audio']+=int(result['audio_count']>0);item['cached']+=int(result['cached'])
                    item['statuses'][result['status']]+=1;item['diagnostics'].update(result.get('diagnostics',{}))
            elif kind=='download':
                downloads[row['status']]+=1;source(row['source'])['downloads'][row['status']]+=1
        initial=[r for r in searches if not r['page']]
        times=[r['first_audio_ms'] for r in searches if r.get('first_audio_ms') is not None]
        return {'searches':len(initial),'pages':len(searches)-len(initial),
            'with_audio':sum(r['with_audio'] for r in initial),'source_mode_searches':sum(r['mode']=='source' for r in initial),
            'first_audio_ms':median(times) if times else None,'downloads':dict(downloads),
            'sources':sorted(sources.values(),key=lambda r:(-r['with_audio'],-r['attempts'],r['source'])),
            'retention':500}

    def source_definitions(self):
        from .source_config import SourceDefinition
        return [SourceDefinition.model_validate_json(row[0]) for row in self.db.execute("SELECT value FROM sources ORDER BY id")]

    def save_source(self, source):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO sources VALUES (?,?)", (source.id, source.model_dump_json()))

    def delete_source(self, id):
        with self.db:
            self.db.execute("DELETE FROM sources WHERE id=?", (id,))

    def initialize_sources(self, definitions, key="source_presets_v1"):
        if self.db.execute("SELECT 1 FROM metadata WHERE key=?",(key,)).fetchone():
            return
        with self.db:
            for source in definitions:
                self.db.execute("INSERT OR IGNORE INTO sources VALUES (?,?)", (source.id,source.model_dump_json()))
            self.db.execute("INSERT INTO metadata VALUES (?,'1')",(key,))

    def replace_profile(self, settings, definitions):
        with self.db:
            self.db.execute("DELETE FROM sources")
            for source in definitions:
                self.db.execute("INSERT INTO sources VALUES (?,?)",(source.id,source.model_dump_json()))
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (1,?)",(settings.model_dump_json(),))
            self.db.execute("INSERT OR REPLACE INTO metadata VALUES ('source_presets_v1','1')")
            self.db.execute("DELETE FROM cache")
