import { sqlite } from '../db/storage.mjs';
const username=process.argv[2]?.trim().toLowerCase();
if (!username) { console.error('Usage: npm run admin -- username (register the account first)');process.exit(1); }
const result=sqlite().prepare("UPDATE users SET role='admin' WHERE username=?").run(username);
if (!result.changes) {console.error('Account not found. Register first, then run this command against the same database.');process.exit(1);}
console.log(`Editorial access granted to ${username}.`);
