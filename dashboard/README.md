# Clinic dashboard

Doctor dashboard (Next.js) for the clinic assistant API. It shows the patient list with
red flags, each child's seizure chart and timeline, medicines with adherence and the
dose-change form, and the pre-visit summary. The doctor key stays on the server; the
browser never sees it.

## Run it

1. Start the backend first (in its own terminal) and keep it running:
   `uvicorn app.main:app --reload` inside `backend`.
2. In a new terminal, inside this folder:

```
npm install
copy .env.local.example .env.local
npm run dev
```

3. Open http://localhost:3000

`DOCTOR_API_KEY` in `.env.local` must match the backend's key.

## Check it builds

```
npm run build
```

This also type-checks the code.

## Pages

| Page | What it shows |
|---|---|
| `/` | Patients, those with unseen red flags first |
| `/patients/[id]` | Red flags (mark as seen), 4-week numbers, 12-week seizure chart with medicine changes, full timeline with Verify buttons |
| `/patients/[id]/medicines` | Current medicines with adherence and a change form, stopped medicines, change history, drips |
| `/patients/[id]/previsit` | Pre-visit summary since a chosen date; Ctrl+P prints it |

## Not here yet

- Adding patients, guardians and medicines from the dashboard (use the API docs page for now).
- The prescription slip review screen. The API can approve or reject slips, but it has no
  endpoint yet that lists the slips waiting for review.
- Doctor login. Anyone who can open this site can see the data, so run it only on your own
  computer until logins are added.
