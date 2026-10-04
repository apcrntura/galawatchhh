# Camera counter (runs on the computer at the location)

1. Install Python 3.10 or newer, then: `pip install -r requirements.txt`
2. Set the secret key (Supabase -> Project Settings -> API -> service_role). It must never be in GitHub or the website.
   - PowerShell: `$env:SUPABASE_KEY="paste-service-role-key"`
   - Command Prompt: `set SUPABASE_KEY=paste-service-role-key`
3. Run: `python main.py` (press Q in the camera window to stop).

Walk across the red line from right to left to count IN, left to right to count OUT.
The script resumes today's totals if it restarts, and starts again at zero every midnight (Philippine time).
