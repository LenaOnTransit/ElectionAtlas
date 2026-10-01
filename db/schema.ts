import { sqliteTable, text, index } from 'drizzle-orm/sqlite-core';
export const records = sqliteTable('records', { id: text('id').primaryKey(), kind: text('kind').notNull(), data: text('data').notNull(), updated: text('updated').notNull() }, (table) => [index('idx_records_kind').on(table.kind)]);
export const editors = sqliteTable('editors', { id: text('id').primaryKey() });
