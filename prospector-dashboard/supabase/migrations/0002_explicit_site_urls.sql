alter table public.leads
  add column if not exists candidate_url text,
  add column if not exists live_url text,
  add column if not exists proposal_url text;

comment on column public.leads.candidate_url is 'Latest approved candidate/preview URL, nullable and independent from live_url.';
comment on column public.leads.live_url is 'Actually deployed public URL, nullable and independently verified.';
comment on column public.leads.proposal_url is 'Proposal document/site URL, independent from candidate and live URLs.';
