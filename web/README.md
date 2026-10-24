# Redress web app

Next.js 16 + Tailwind 4, styled after the HTML references in `../design/`.

```powershell
npm install
npm run dev   # http://localhost:3000
```

Pages so far: `/` the wall, `/call` the live call. Both are placeholders. Planned screens: wall, live call, queue, evaluation form, learning, compare and Mubit panel (root README §4 and §7). `lib/api.ts` points at the Redress API (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).
