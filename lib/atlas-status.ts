import type {WorldElection} from './world';

export type AtlasStatus = 'today' | 'upcoming';
export function localCalendarDate(now = new Date()): string {
  return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
}

// One calendar month ahead, clamped to the last day of the following month.
export function atlasElectionStatuses(elections: WorldElection[], today: string): Map<string, AtlasStatus> {
  const [year,month,day] = today.split('-').map(Number);
  const lastDay = new Date(Date.UTC(year,month+1,0)).getUTCDate();
  const cutoff = new Date(Date.UTC(year,month,Math.min(day,lastDay))).toISOString().slice(0,10);
  const statuses = new Map<string, AtlasStatus>();
  for (const e of elections) {
    if (e.publication !== 'published' || e.precision !== 'day' || e.dateStatus === 'tba' || !e.startDate || !['scheduled','held'].includes(e.status)) continue;
    const end = e.endDate || e.startDate;
    if (e.startDate <= today && end >= today) statuses.set(e.countryId,'today');
    else if (e.status === 'scheduled' && e.startDate > today && e.startDate <= cutoff && statuses.get(e.countryId) !== 'today') statuses.set(e.countryId,'upcoming');
  }
  return statuses;
}
