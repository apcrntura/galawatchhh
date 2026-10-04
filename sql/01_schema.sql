-- GalaWatch v2: tables, seed data, alert trigger.
-- Run in Supabase: SQL Editor -> New query -> paste -> Run.
-- Safe to run more than once.
-- Assumes you already have camera_counts and camera_count_history from earlier steps.

create table if not exists public.destinations (
  id              text primary key,
  name            text not null,
  region          text not null,
  lat             numeric(9,6) not null check (lat between -90 and 90),
  lng             numeric(9,6) not null check (lng between -180 and 180),
  capacity        int check (capacity > 0),     -- people that count as 100% load (live destinations)
  alert_at        int check (alert_at > 0),     -- overcrowding alert when people inside reaches this
  is_live         boolean not null default false,
  sample_visitors int not null default 0,
  sample_cap      int not null default 0 check (sample_cap between 0 and 100),
  sample_trend    int[] not null default '{0,0,0,0,0,0,0}',
  sample_note     text not null default 'Sample data for demonstration.'
);

create table if not exists public.cameras (
  id             uuid primary key default gen_random_uuid(),
  destination_id text not null references public.destinations(id) on delete cascade,
  name           text not null,
  status         text not null default 'Active' check (status in ('Active','Offline','Maintenance'))
);

create table if not exists public.app_settings (
  id     int primary key default 1 check (id = 1),
  medium int not null default 40,
  high   int not null default 70,
  check (medium > 0 and medium < high and high <= 100)
);
insert into public.app_settings (id) values (1) on conflict (id) do nothing;

create table if not exists public.profiles (
  id        uuid primary key references auth.users(id) on delete cascade,
  full_name text not null,
  username  text not null unique,
  role      text not null check (role in ('tourism','lgu','admin')),
  active    boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.alerts (
  id              bigint generated always as identity primary key,
  destination_id  text not null references public.destinations(id) on delete cascade,
  people_inside   int,
  limit_value     int,
  status          text not null default 'Unacknowledged' check (status in ('Unacknowledged','Acknowledged','Resolved')),
  triggered_at    timestamptz not null default now(),
  acknowledged_by uuid references auth.users(id) on delete set null,
  acknowledged_at timestamptz
);
create index if not exists alerts_time_idx on public.alerts (triggered_at desc);

-- Destinations. APC is the live camera. The other eight use sample data.
insert into public.destinations
 (id, name, region, lat, lng, capacity, alert_at, is_live, sample_visitors, sample_cap, sample_trend, sample_note)
values
 ('apc','Asia Pacific College','Magallanes, Makati City',14.531777,121.023877,30,30,true,0,0,'{0,0,0,0,0,0,0}','Live AI camera.'),
 ('baguio','Baguio City','Benguet, CAR',16.4023,120.5960,null,null,false,42800,87,'{18000,24000,31000,38000,42000,41000,42800}','Approaching capacity. LGU entry management recommended.'),
 ('sagada','Sagada','Mountain Province, CAR',17.0848,120.9013,null,null,false,8400,62,'{4000,5200,6800,7500,8100,8200,8400}','Within normal range. Stable conditions.'),
 ('vigan','Vigan City','Ilocos Sur',17.5747,120.3869,null,null,false,21000,55,'{14000,16000,17500,19000,20000,20800,21000}','Stable. Good opportunity for targeted promotion.'),
 ('laoag','Laoag City','Ilocos Norte',18.1978,120.5936,null,null,false,14500,44,'{9000,10500,11000,12500,13800,14200,14500}','Well within capacity. Growth opportunity.'),
 ('banaue','Banaue','Ifugao, CAR',16.9178,121.0589,null,null,false,5200,71,'{2800,3400,4000,4600,4900,5100,5200}','Rising density detected. Monitor closely.'),
 ('tug','Tuguegarao City','Cagayan Valley',17.6132,121.7270,null,null,false,9800,33,'{6000,6800,7200,8000,8800,9400,9800}','Low congestion. Strong promotion opportunity.'),
 ('bolinao','Bolinao','Pangasinan, Region I',16.3833,119.9000,null,null,false,18500,48,'{11000,12500,14000,15500,16800,17500,18500}','Rising trend. Plan infrastructure ahead of peak.'),
 ('angeles','Angeles City','Pampanga, Central Luzon',15.1450,120.5887,null,null,false,28500,59,'{18000,20000,22000,24000,26000,27500,28500}','Steady growth. Conditions remain stable.')
on conflict (id) do nothing;

insert into public.cameras (destination_id, name)
select 'apc', 'APC Camera 1'
where not exists (select 1 from public.cameras where destination_id = 'apc');

-- Make sure the live row exists (the camera script updates it).
insert into public.camera_counts (destination_id, people_in, people_out, current_inside)
select 'apc', 0, 0, 0
where not exists (select 1 from public.camera_counts where destination_id = 'apc');

-- Alert service: one alert row each time a camera count first reaches the limit.
create or replace function public.raise_alert() returns trigger
language plpgsql security definer set search_path = public as $$
declare lim int;
begin
  select alert_at into lim from public.destinations where id = new.destination_id;
  if lim is not null and new.current_inside >= lim
     and (tg_op = 'INSERT' or old.current_inside < lim) then
    insert into public.alerts (destination_id, people_inside, limit_value)
    values (new.destination_id, new.current_inside, lim);
  end if;
  return new;
end $$;

drop trigger if exists camera_counts_alert on public.camera_counts;
create trigger camera_counts_alert after insert or update on public.camera_counts
for each row execute function public.raise_alert();
