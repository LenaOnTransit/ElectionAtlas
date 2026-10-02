-- Publication time is separate from the immutable generated visibility flag.
-- Read access uses the database clock, so no cron or open browser is needed.
alter table public.ea_records add column publication_at timestamptz;

create function electionatlas_private.sync_article_publication() returns trigger
language plpgsql security invoker set search_path='' as $$
declare instant text;
begin
 new.publication_at:=null;
 if new.kind='article' and new.data->>'status'='published' then
  instant:=nullif(new.data->>'publishAt','');
  if instant is not null then
   if instant !~ '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?(Z|[+-]\d{2}:\d{2})$' then
    raise exception 'Publication time must be an ISO timestamp with a time zone' using errcode='22007';
   end if;
   new.publication_at:=instant::timestamptz;
   if not pg_catalog.isfinite(new.publication_at) then raise exception 'Invalid publication time' using errcode='22007'; end if;
  end if;
 end if;
 return new;
end;
$$;
revoke all on function electionatlas_private.sync_article_publication() from public,anon,authenticated;
create trigger ea_article_publication before insert or update on public.ea_records
for each row execute function electionatlas_private.sync_article_publication();

-- Preserve all existing content; initialize the timestamp from any supplied schedule.
update public.ea_records set data=data where kind='article';

alter policy records_public_read on public.ea_records
using (is_public and (publication_at is null or publication_at <= (select now()))
 and (kind <> 'article' or coalesce(data->>'archived','false') <> 'true'));

-- Editors retain private newsroom access, but public pages use this function too.
-- SECURITY INVOKER preserves RLS and never exposes drafts or future articles.
create function public.ea_public_records(record_kinds text[])
returns setof public.ea_records language sql stable security invoker set search_path='' as $$
 select * from public.ea_records
 where kind=any(record_kinds) and is_public
 and (publication_at is null or publication_at <= now())
 and (kind <> 'article' or coalesce(data->>'archived','false') <> 'true')
 order by coalesce(publication_at,updated) desc,id;
$$;
revoke all on function public.ea_public_records(text[]) from public,anon,authenticated;
grant execute on function public.ea_public_records(text[]) to anon,authenticated;
