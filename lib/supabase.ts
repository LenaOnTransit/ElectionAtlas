import { createClient } from '@supabase/supabase-js';

// Publishable connection details are public by design. RLS protects private data.
const url = import.meta.env.VITE_SUPABASE_URL || 'https://qurdolyenxynuqdmcxbr.supabase.co';
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_rT5dROWZs9m_kQXZmagesQ_fbZKtEfu';
export const supabase = createClient(url, key, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: 'pkce', storageKey: 'electionatlas-auth' },
});
