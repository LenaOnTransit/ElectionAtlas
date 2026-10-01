import { scrypt as scryptCallback, randomBytes, randomUUID, createHash, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';
import { sqlite } from '../db/storage.mjs';
const scrypt = promisify(scryptCallback);
const options = { N: 32768, r: 8, p: 1, maxmem: 64 * 1024 * 1024 };
export const SESSION_AGE = 60 * 60 * 24 * 7;
export function digest(value) { return createHash('sha256').update(value).digest('hex'); }
export function normalizeEmail(value) { return typeof value === 'string' ? value.trim().toLowerCase() : ''; }
export function validateRegistration({ email, username, password }) {
  if (typeof email !== 'string' || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw Error('Enter a valid email address.');
  if (typeof username !== 'string' || !/^[a-zA-Z0-9_]{3,30}$/.test(username)) throw Error('Username must be 3–30 letters, numbers, or underscores.');
  if (typeof password !== 'string' || password.length < 12 || password.length > 128) throw Error('Password must be 12–128 characters.');
}
export async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const key = await scrypt(password, salt, 64, options);
  return `scrypt:${salt}:${key.toString('hex')}`;
}
export async function verifyPassword(password, stored) {
  if (typeof password !== 'string' || password.length > 128) return false;
  const [,salt,key] = stored.split(':');
  const result = await scrypt(password, salt, 64, options);
  const expected = Buffer.from(key, 'hex');
  return expected.length === result.length && timingSafeEqual(result, expected);
}
export async function register(input) {
  const email = normalizeEmail(input.email);
  const username = typeof input.username === 'string' ? input.username.trim().toLowerCase() : '';
  validateRegistration({ ...input, email, username });
  const password = await hashPassword(input.password);
  const userId = randomUUID();
  try { sqlite().prepare("INSERT INTO users(id,email,username,password,role,created) VALUES(?,?,?,?,'reader',?)").run(userId,email,username,password,Date.now()); }
  catch (error) { if (String(error).includes('UNIQUE constraint')) throw Error('That email or username is unavailable.'); throw error; }
  return { userId, displayName: username, email, role: 'reader' };
}
// The dummy hash gives unknown accounts the same expensive password check.
let dummyHash;
export async function login(email, password) {
  dummyHash ??= hashPassword('dummy-account-password');
  const user = sqlite().prepare('SELECT * FROM users WHERE email=?').get(normalizeEmail(email));
  const valid = await verifyPassword(password, user?.password || await dummyHash);
  if (!user || !valid) throw Error('Email or password is incorrect.');
  return { userId: user.id, displayName: user.username, email: user.email, role: user.role };
}
export function createSession(userId) {
  const token = randomBytes(32).toString('hex');
  sqlite().prepare('DELETE FROM sessions WHERE expires<=?').run(Date.now());
  sqlite().prepare('INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)').run(digest(token),userId,Date.now()+SESSION_AGE*1000);
  return token;
}
export function sessionUser(token) {
  if (typeof token !== 'string' || !/^[a-f0-9]{64}$/.test(token)) return null;
  const user = sqlite().prepare('SELECT users.id,users.username,users.email,users.role FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.token=? AND sessions.expires>?').get(digest(token),Date.now());
  return user ? { userId:user.id, displayName:user.username, email:user.email, role:user.role } : null;
}
export function deleteSession(token) { if (token) sqlite().prepare('DELETE FROM sessions WHERE token=?').run(digest(token)); }
export function limit(key, maximum, windowMs = 15*60*1000) {
  const now = Date.now();
  sqlite().prepare('DELETE FROM auth_limits WHERE expires<=?').run(now);
  const row = sqlite().prepare('INSERT INTO auth_limits(key,count,expires) VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count').get(digest(key),now+windowMs);
  return row.count <= maximum;
}
