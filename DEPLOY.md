# GalaWatch v2: Deployment Guide

Order matters: Supabase first, then the API, then the website, then the camera.

What was and was not tested before you got this (so you know where to look first if something fails):
- Tested: the report/date logic in `backend/app/summary.py` (9 tests pass) and Python syntax of the backend and camera files. All frontend scripts parse and all templates have balanced tags.
- NOT tested: `npm run build` (the package registry was blocked in the workspace where this was written), the FastAPI server, the Excel/PDF files, the SQL against a real Supabase project, and the website against real data. Expect to fix small errors on the first run. Section 9 lists the likely ones.

## 0. What you need
Accounts: GitHub, Supabase (existing project), Vercel (existing), Render (free, new). On your computer: Node.js 20 or newer, Python 3.10 or newer, Git.

## 1. Supabase (database, logins, security)
1. Open your project, then SQL Editor, New query.
2. Paste all of `sql/01_schema.sql` and click Run. It creates the tables, loads the nine destinations (APC is live) and adds the alert trigger. You should see "Success. No rows returned".
3. Create the first administrator login: Authentication, Users, Add user, Create new user.
   - Email: `admin@galawatch.app` (no email is sent)
   - Password: a strong one. Tick Auto Confirm User.
4. Run `sql/03_first_admin.sql`. The result table must show one row: username `admin`, role `admin`, active `true`.
5. Run `sql/02_security.sql`. This switches on Row Level Security. After this only signed-in active users can read data. The old public read policies are removed.
6. Authentication, Sign In / Providers, Email: turn OFF "Allow new users to sign up". Only the administrator creates accounts.
7. Project Settings, API: copy the Project URL, the anon key (public) and the service_role key (secret). Keep the secret one out of chat, GitHub and the website.

Check: Table Editor shows `destinations` (9 rows), `profiles` (1 row), `cameras`, `app_settings`, `alerts`.

## 2. Put the project on GitHub
Use ONE repository. Your Vercel project is connected to `galawatchhh` (three h's); use that one.
1. In your repository, move the old files (index.html, login.html, admin.html, admin-login.html, shared.js, style.css) into a folder called `legacy/`, or delete them.
2. Copy the contents of this `galawatch-v2` folder into the repository root so you have `frontend/`, `backend/`, `camera/`, `sql/`, `render.yaml` and `DEPLOY.md`.
3. Make sure `.env` files and `queue.db` are not committed (the included `.gitignore` handles this).
4. Commit and push to `main`.

## 3. Deploy the API on Render
1. render.com, New, Blueprint, choose your repository. Render reads `render.yaml`.
2. When asked, enter the three values:
   - `SUPABASE_URL`: your Project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: the secret key
   - `FRONTEND_URL`: for now `http://localhost:5173`; you change it in step 5
3. Deploy. When it is live, open `https://YOUR-API.onrender.com/health`. It must show `{"ok":true}`.
4. Free plans sleep when idle, so the first request after a break can take about a minute. The live dashboard does not need the API. Only user management and reports do.
Manual setup instead of the Blueprint: New, Web Service, Root Directory `backend`, Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## 4. Deploy the website on Vercel
1. Open your existing Vercel project, Settings, General, and set Root Directory to `frontend`. Framework Preset: Vite. Leave Build Command and Output Directory on their defaults (`npm run build`, `dist`).
2. Settings, Environment Variables, add for Production (and Preview if you use it):
   - `VITE_SUPABASE_URL` = your Project URL
   - `VITE_SUPABASE_ANON_KEY` = the anon key
   - `VITE_API_URL` = `https://YOUR-API.onrender.com` (no slash at the end)
3. Deployments, Redeploy (or push a commit). Wait for Ready.
4. Open `https://galawatchh.vercel.app/admin-login` and sign in with username `admin` and your password.

## 5. Connect the API and the website
1. Render, your service, Environment: set `FRONTEND_URL` to your Vercel address, for example `https://galawatchh.vercel.app`. Several addresses can be comma separated. Save (Render restarts it).
2. Test: Admin Panel, User Accounts, Add user (a Tourism Officer). Then log out, and sign in at `/login` with that user.

## 6. Start the camera
1. On the computer at the location: `cd camera`, `pip install -r requirements.txt`.
2. Set the secret key for this window only: PowerShell `$env:SUPABASE_KEY="paste-service-role-key"`.
3. `python main.py`. The terminal should print "Supabase updated" lines.
4. Open the dashboard. Cross the red line right to left (IN) and left to right (OUT). The APC panel changes within about a second.
5. In Admin Panel, Destinations and Cameras, set APC's Capacity and "Alert at" to the real numbers (they start at 30).

## 7. Smoke test (about 10 minutes)
| Check | Expected |
|---|---|
| Admin signs in at /admin-login | Admin Panel opens |
| Tourism user signs in at /admin-login | Refused: page is for the System Admin only |
| Admin signs in at /login | Refused: must use the admin login page |
| Not signed in, open /admin | Redirected to /admin-login |
| Dashboard | Map with 9 pins, APC selected, Realtime status: SUBSCRIBED in the browser console |
| Camera crossing | IN/OUT/Inside change on the APC panel |
| Inside reaches the Alert at number | Pin red and pulsing, bell badge, pop-up, a row in the alert log |
| Acknowledge in the Alerts menu | Status changes to Acknowledged |
| Disable a user, then try to sign in | Refused |
| Export Report, Excel and PDF | A file downloads |
| Admin changes the thresholds | Map colors and legend change after reload |
| Leave the page idle for 15 minutes | Signed out automatically |

## 8. Security checklist
- The service_role key exists only in Render's environment variables and on the camera computer. Not in GitHub, Vercel or the browser.
- Sign-ups are off (step 1.6). RLS is on (step 1.5). Keep the `.env` files out of Git.
- Change the first admin password if it was ever shared, and create one personal account per person.
- If a secret key was ever pasted in a chat or committed, rotate it: Supabase, Project Settings, API, then reset the key and update Render and the camera computer.

## 9. If something fails
| Symptom | Likely cause and fix |
|---|---|
| Vercel build fails | Open the build log. Check Root Directory is `frontend` and the three VITE variables exist. Variables are only read at build time, so redeploy after changing them. |
| Page loads but nothing sign-in works, console says invalid API key | Wrong `VITE_SUPABASE_ANON_KEY`, or you used the secret key. Fix and redeploy. |
| "Invalid username or password" for the admin | Step 1.3 email must be exactly `admin@galawatch.app`, and step 1.4 must have returned the row. |
| Sign in works, then "disabled or has no profile" | Run step 1.4 again. |
| Dashboard empty, console shows permission denied | Run `02_security.sql` after `01_schema.sql`, and sign in again. |
| Realtime status is not SUBSCRIBED | Re-run `02_security.sql` (it adds the tables to the realtime list). The page also refreshes every 10 seconds as a backup. |
| Adding a user says "Failed to fetch" | `VITE_API_URL` is wrong, the API is asleep (wait a minute), or `FRONTEND_URL` on Render does not match your Vercel address exactly. |
| Reports fail | Open `/health` on the API. Check the Render logs for the error and send it to your developer. |
| Camera prints "no row was updated" or nothing changes | The `apc` row is missing in `camera_counts` (re-run `01_schema.sql`) or you used the anon key instead of service_role. |
| Alert never fires | Inside must reach "Alert at". Inside is IN minus OUT and never goes below zero. Check the numbers in `camera_counts`. |
| Page refresh gives 404 on Vercel | `frontend/vercel.json` is missing from the deployed folder. |

## 10. Not built yet
Forecasting (SARIMA-LSTM), QR registration, Waze/Google traffic layers, Google Maps search for destinations, login lockout after failed attempts, and the camera posting through the API instead of straight to Supabase. The history needed for forecasting is already being recorded.
