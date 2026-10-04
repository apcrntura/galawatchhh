-- GalaWatch v2: make your first System Administrator.
-- 1) In Supabase: Authentication -> Users -> Add user -> Create new user.
--    Email:    admin@galawatch.app      (any address; no email is sent)
--    Password: choose a strong password
--    Tick "Auto Confirm User".
-- 2) Run this script. It links that login to an admin profile.
-- Signing in on the website: type the part before the @ (admin) as the username.

insert into public.profiles (id, full_name, username, role)
select id, 'System Admin', split_part(email, '@', 1), 'admin'
from auth.users
where email = 'admin@galawatch.app'
on conflict (id) do update set role = 'admin', active = true;

select p.username, p.role, p.active from public.profiles p;
