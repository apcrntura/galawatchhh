-- GalaWatch v2: Row Level Security. Run AFTER 01_schema.sql.
-- Result: only signed-in, active users can read data. Only admins can change settings.
-- The camera script and the API use the secret (service_role) key and bypass these rules.

create or replace function public.is_active() returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and active)
$$;

create or replace function public.is_admin() returns boolean
language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'admin' and active)
$$;

-- profiles
alter table public.profiles enable row level security;
drop policy if exists "own or admin read" on public.profiles;
drop policy if exists "admin manage" on public.profiles;
create policy "own or admin read" on public.profiles for select to authenticated
  using (id = auth.uid() or public.is_admin());
create policy "admin manage" on public.profiles for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- destinations, cameras, app_settings: active users read, admins write
do $$
declare t text;
begin
  foreach t in array array['destinations','cameras','app_settings'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "active read" on public.%I', t);
    execute format('drop policy if exists "admin write" on public.%I', t);
    execute format('create policy "active read" on public.%I for select to authenticated using (public.is_active())', t);
    execute format('create policy "admin write" on public.%I for all to authenticated using (public.is_admin()) with check (public.is_admin())', t);
  end loop;
end $$;

-- alerts: active users read. Acknowledging goes through a function.
alter table public.alerts enable row level security;
drop policy if exists "active read" on public.alerts;
create policy "active read" on public.alerts for select to authenticated using (public.is_active());

create or replace function public.acknowledge_alert(p_id bigint) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_active() then raise exception 'not allowed'; end if;
  update public.alerts
     set status = 'Acknowledged', acknowledged_by = auth.uid(), acknowledged_at = now()
   where id = p_id and status = 'Unacknowledged';
end $$;
revoke execute on function public.acknowledge_alert(bigint) from public, anon;
grant execute on function public.acknowledge_alert(bigint) to authenticated;

-- live counts and history: replace the earlier public (anon) read policies
alter table public.camera_counts enable row level security;
drop policy if exists "public read camera_counts" on public.camera_counts;
drop policy if exists "active read" on public.camera_counts;
create policy "active read" on public.camera_counts for select to authenticated using (public.is_active());

alter table public.camera_count_history enable row level security;
drop policy if exists "read history" on public.camera_count_history;
drop policy if exists "active read" on public.camera_count_history;
create policy "active read" on public.camera_count_history for select to authenticated using (public.is_active());

-- daily summary view must obey the caller's permissions (otherwise it would bypass the rules above)
drop view if exists public.camera_daily_summary;
create view public.camera_daily_summary with (security_invoker = true) as
select destination_id,
       (recorded_at at time zone 'Asia/Manila')::date as day,
       max(current_inside) as peak_inside,
       max(people_in)      as total_in,
       max(people_out)     as total_out
from public.camera_count_history
group by 1, 2;
revoke all on public.camera_daily_summary from anon;
grant select on public.camera_daily_summary to authenticated;

-- live updates for the dashboard
do $$
begin
  begin alter publication supabase_realtime add table public.camera_counts; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.alerts;        exception when duplicate_object then null; end;
end $$;
