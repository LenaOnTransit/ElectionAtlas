import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
let database;
export function sqlite() {
  if (!database) {
    const path = process.env.DATABASE_PATH || './data/electionatlas.sqlite';
    if (path !== ':memory:') mkdirSync(dirname(resolve(path)), { recursive: true });
    database = new DatabaseSync(path);
    database.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
      CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,data TEXT NOT NULL,updated TEXT NOT NULL);
      CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind);
      CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT NOT NULL UNIQUE,username TEXT NOT NULL UNIQUE,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'reader' CHECK(role IN ('reader','admin')),created INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,expires INTEGER NOT NULL);
      CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires);
      CREATE TABLE IF NOT EXISTS auth_limits(key TEXT PRIMARY KEY,count INTEGER NOT NULL,expires INTEGER NOT NULL);`);
  }
  return database;
}
class Query {
  constructor(sql, values = []) { this.sql = sql; this.values = values; }
  bind(...values) { return new Query(this.sql, values); }
  async first() { return sqlite().prepare(this.sql).get(...this.values) ?? null; }
  async all() { return { results: sqlite().prepare(this.sql).all(...this.values) }; }
  execute() { const result = sqlite().prepare(this.sql).run(...this.values); return { meta: { changes: Number(result.changes) } }; }
  async run() { return this.execute(); }
}
export function storage() {
  return {
    prepare: sql => new Query(sql),
    async batch(queries) {
      const db = sqlite(); db.exec('BEGIN IMMEDIATE');
      try { const results = queries.map(q => q.execute()); db.exec('COMMIT'); return results; }
      catch (error) { db.exec('ROLLBACK'); throw error; }
    },
  };
}
