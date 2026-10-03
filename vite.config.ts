import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
export default defineConfig({base:process.env.VITE_BASE_PATH||'/',plugins:[react()],resolve:{alias:{'@':resolve(import.meta.dirname,'.')}},build:{outDir:'dist'},server:{allowedHosts:['terminal.local']}});
