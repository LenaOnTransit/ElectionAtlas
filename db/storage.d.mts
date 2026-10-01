import type { DatabaseSync } from 'node:sqlite';
export function sqlite(): DatabaseSync;
interface Query {
  bind(...values: (string | number | null)[]): Query;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  all<T = Record<string, unknown>>(): Promise<{results: T[]}>;
  run(): Promise<{meta:{changes:number}}>;
}
export function storage(): {prepare(sql:string):Query;batch(queries:Query[]):Promise<{meta:{changes:number}}[]>};
