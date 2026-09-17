# AI Delivery Dashboard frontend

React + TypeScript + Vite + Tailwind CSS + shadcn/ui application shell.

The classic dashboard remains at `/`. This app is served at `/app` after `npm run build`.

## Local development

Run the FastAPI API from `backend`:

```bash
uvicorn app.main:app --reload --port 8000
```

Then from `frontend`:

```bash
npm install
npm run dev
```

Open `http://localhost:5173/app/`. Vite proxies `/metrics`, `/sources`, `/projects`, and `/health` to the API.

## Production build

```bash
npm run build
```

FastAPI serves `frontend/dist` at `/app` when that directory exists.
