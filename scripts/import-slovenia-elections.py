#!/usr/bin/env python3
"""Build reviewable Slovenia records from audited official source extracts; never writes live data."""
from pathlib import Path
import json,re,unicodedata,uuid
OUT=Path(__file__).parent/'slovenia-election-import'
source=json.loads((OUT/'source-extract.json').read_text())
def slug(s):return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def result(n,p,v,seats=None,color='#64748b'):
 return dict(id=slug(n)[:90],name=n[:200],party=p[:200],color=color,votes=v,share=None,seats=seats,previousSeats=None,electoralVotes=None,winner=False)
def record(date,office,round='General election',end=''):
 return dict(id=f'world-slovenia-{date}-{office}'+('-round-'+round[-1] if round.startswith('Round') else ''),countryId='si',title='National Assembly election' if office=='assembly' else 'Presidential election',type='parliamentary' if office=='assembly' else 'presidential',body='National Assembly (Državni zbor)' if office=='assembly' else 'President of the Republic',startDate=date,endDate=end,precision='day',dateStatus='confirmed',status='held',publication='draft',round=round,seriesId=f'slovenia-{office}-{date[:4]}',snap=False,summary='',government='',turnout=None,totalSeats=90 if office=='assembly' else None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked='2026-10-06',notes='',articleId='',version=0,electionMethod='direct',majorityThreshold=46 if office=='assembly' else None)
A={1992:('12-06',1491374,1277604),1996:('11-10',1542218,1136679),2000:('10-15',1588528,1114170),2004:('10-03',1634402,991263),2008:('09-21',1696437,1070523),2011:('12-04',1709692,1121573),2014:('07-13',1713067,886124),2018:('06-03',1712676,901512),2022:('04-24',1695796,1203522),2026:('03-22',1695302,1190932)}
P={1992:[('12-06',1491374,1280252,1278155,35797)],1997:[('11-23',1550775,1064532,1064446,22102)],2002:[('11-10',1609985,1160309,1159681,15209),('12-01',1610137,1052795,1052494,14275)],2007:[('10-21',1720481,992245,991708,5279),('11-11',1720174,1005595,1005359,9738)],2012:[('11-11',1711768,828752,828624,10852),('12-02',1711461,725768,725700,14870)],2017:[('10-22',1713762,758088,757898,5634),('11-12',1713473,721894,721801,9255)],2022:[('10-23',1694441,876687,876566,4625),('11-13',1694379,908138,908065,10224)]}
runoffs={2002:[('Janez Drnovšek',586847),('Barbara Brezigar',451372)],2007:[('Danilo Türk',677333),('Lojze Peterle',318288)],2012:[('Borut Pahor',478859),('Danilo Türk',231971)],2017:[('Borut Pahor',378307),('Marjan Šarec',334239)]}
history='https://www.dvk-rs.si/fileadmin/user_upload/VOLITVE_PREDSEDNIKA_REPUBLIKE__1992_do_2017__-_podatki_o_kandidatih__prejetih_glasovih_in_udelezbi.doc'
records=[];audit=[]
# Only period-consistent, exact organization links are proposed; never infer ideology.
profiles=[]
for name,short,color in [('GIBANJE SVOBODA','SVOBODA','#0063a6'),('SLOVENSKA DEMOKRATSKA STRANKA - SDS','SDS','#ffe53f'),('SOCIALNI DEMOKRATI','SD','#fc0010'),('LEVICA','Levica','#b30020'),('PIRATSKA STRANKA SLOVENIJE','PIRATI','#000000'),('DRŽAVLJANSKO GIBANJE RESNI.CA','Resni.ca','#7e5096')]:
 profiles.append(dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.org/parties/si/'+slug(name))),country_id='si',name=name,short_name=short,color=color,ideology_ids=[],notes='Election-era name and presentation colour from DVK national results snapshots, 2022–2026. No ideology assessment. https://www.dvk-rs.si/arhivi/dz2026/data/rezultati.json',archived=False))
for x in source:
 y=x['year'];office=x['office']
 if office=='assembly':
  md,electorate,voters=A[y];e=record(f'{y}-{md}',office);e['snap']=y in [2011,2014,2018];valid=x['valid'];e['voteBasis']=f'National list votes; {valid:,} valid general-election ballots (minority ballots excluded)'
  e['results']=[result(r['name'],r.get('party',r['name']),r['votes'],r.get('seats'),r.get('color','#64748b')) for r in x['rows']]
  e['summary']=f"{max(e['results'],key=lambda r:r['votes'])['name']} received the most national list votes. The National Assembly has 90 seats, including two seats reserved for the Italian and Hungarian national communities."
  gap=valid-sum(r['votes'] for r in e['results']);e['notes']=f'88 seats are allocated from the general list ballot. National-community elections have separate ballots and denominators. Minority candidate results have not been transcribed; coverage is partial. Turnout: {voters:,} voters / {electorate:,} eligible voters; the voter count is distinct from ballots cast. '
  e['notes']+=('General ballot: eight 11-seat constituencies, proportional representation with national allocation; the four-percent national threshold applies from 2000. Earlier elections used the earlier allocation rules. ')
  if gap:e['notes']+=f'The source national table omits {gap:,} votes, apparently local/independent lists; no invented residual row is added. '
  if y==1996:e['notes']+='Party seat allocations remain untranscribed from the source diagram; seats are null. '
  if y in [1992,2000]:e['notes']+='General-list seat allocations are transcribed from the DVK chamber composition diagram; the two national-community seats have not been entered. '
  if y==2000:e['resultStatus']='provisional';e['notes']+='The detailed source identifies these figures as unofficial and reports 99.93% of ballots counted. '
  if x.get('cast'):e['notes']+=f"General ballots cast {x['cast']:,}; invalid {x['invalid']:,}; valid {valid:,}. "
  e['sources']=[dict(label='DVK election archive and results',url=x['source'])]
  if y in [2018,2022,2026]:e['sources'].append(dict(label='DVK national results JSON snapshot',url=f'https://www.dvk-rs.si/arhivi/dz{y}/data/rezultati.json'))
  elif y in [2004,2008,2011,2014]:e['sources'].append(dict(label='DVK national list result table',url=f'https://www.dvk-rs.si/arhivi/dz{y}/'+('html/rez_si.html' if y==2004 else 'rezultati/rezultati_slo.html')))
  if y in [1992,2000]:e['sources'].append(dict(label='DVK chamber composition diagram',url='https://www.dvk-rs.si/arhivi/dz1992/files/arhivi/dz1992_sestava.gif' if y==1992 else 'https://www.dvk-rs.si/arhivi/dz2000/slika_dz/dz.gif'))
  e['turnout']=round(voters/electorate*100,6)
  if y==1992:
   e['turnout']=85.6;e['notes']=e['notes'].replace('Turnout: 1,277,604 voters / 1,491,374 eligible voters; the voter count is distinct from ballots cast.', 'Source turnout: 85.6%; eligible voters 1,491,374. The landing page reports 1,277,604 ballots cast; a separate participant count is not established.')
  if y==2000:e['notes']+='The landing-page turnout numerator is the 19:00 participant count, not a subsequently verified final count. '
  for r in e['results']:r['share']=round(r['votes']/valid*100,6)
  records.append(e);audit.append(dict(id=e['id'],validVotes=valid,recordedVotes=sum(r['votes'] for r in e['results']),voteGap=gap,recordedSeats=sum(r['seats'] or 0 for r in e['results'])))
 else:
  rounds=[x.get('round',1)] if y==2022 or len(P[y])==1 else [1,2]
  for rnd in rounds:
   md,electorate,voters,cast,invalid=P[y][rnd-1];valid=cast-invalid;e=record(f'{y}-{md}',office,'Round '+str(rnd));e['title']='Presidential election — '+('runoff' if rnd==2 else 'first round');e['totalSeats']=None
   if rnd==2 and y!=2022:
    rs=[dict(name=n,party=next(r['party'] for r in x['rows'] if r['name']==n),votes=v) for n,v in runoffs[y]]
   else:rs=x['rows']
   e['results']=[result(r['name'],r['party'] or 'Voter-nominated / proposer not assessed',r['votes']) for r in rs]
   for r in e['results']:
    r['share']=round(r['votes']/valid*100,6);r['ideologyBasis']=dict(kind='unassessed',year=y,note='No election-era ideological assessment has been made; proposer labels are not ideological classifications.',sources=[])
   if rnd==2 or len(P[y])==1:max(e['results'],key=lambda r:r['votes'])['winner']=True
   else:
    for r in sorted(e['results'],key=lambda r:r['votes'],reverse=True)[:2]:r['advanced']=True
   e['turnout']=round(voters/electorate*100,6);e['voteBasis']=f'Candidate votes / {valid:,} valid ballots in this round';gap=valid-sum(r['votes'] for r in e['results']);e['resultCoverage']='complete' if gap==0 else 'partial'
   leader=max(e['results'],key=lambda r:r['votes']);e['summary']=f"{leader['name']} {'was elected president' if leader['winner'] else 'led the first round; the two highest-polling candidates advanced to the runoff'}."
   e['notes']=f'Direct election by absolute majority of valid votes; if no candidate wins a majority, the two leading candidates contest a separate runoff. Five-year term. Turnout: {voters:,} voters / {electorate:,} eligible voters. Ballots cast {cast:,}; invalid {invalid:,}; valid {valid:,}. Candidate shares use only this round. Proposer labels retain election-era support and do not imply party membership. '
   if gap:e['notes']+=f'Recorded candidates differ from the stated valid total by {gap:,}; coverage partial pending reconciliation. '
   e['sources']=[dict(label='DVK election archive',url=x['source'])]
   if y<2022:e['sources'].append(dict(label='DVK historical candidates, proposers and turnout overview (cross-checked)',url=history))
   if y==1992:
    e['sources'].append(dict(label='Certified 1992 final report',url='https://www.dvk-rs.si/fileadmin/user_upload/dokumenti/volitve/predsednika_rs_1992/porocilo_pr_1992.pdf'));e['notes']+='Eligible total includes 940 voters admitted by certificate, omitted from the retrospective denominator. '
   if y==1997:
    e['sources'].append(dict(label='Certified final report in Official Gazette',url='https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/1997-01-3661/porocilo-o-izidu-volitev-predsednika-republike'));e['notes']+='The certified report supersedes erroneous voter and ballot totals in the retrospective overview. '
   if y==2002:e['notes']+='Runoff voters: 1,052,795 in the contemporary DVK report; the retrospective overview misprints 1,052,759. '
   if y==2012:
    e['sources'].append(dict(label='DVK certified first-round results',url='https://www.dvk-rs.si/arhivi/vp2012/rezultati/rezultati.html'));e['notes']+='The retrospective overview swaps Türk and Zver first-round totals; corrected from the certified result table. '
   if y==2017:e['notes']+='Turnout is calculated from voter counts, rather than the inconsistent rounded percentages in the retrospective overview. '
   records.append(e);audit.append(dict(id=e['id'],validVotes=valid,recordedVotes=sum(r['votes'] for r in e['results']),voteGap=gap,recordedSeats=0))
# Keep each replacement seat and each ballot denominator in its own record.
for x in json.loads((OUT/'council-extract.json').read_text()):
 e=record(x['date'],'assembly');e['id']=f"world-slovenia-{x['date']}-council-{slug(x['area'])}";e['title']='National Council replacement election: '+x['area'];e['body']='National Council (Državni svet)';e['round']='Replacement election';e['seriesId']='slovenia-council-'+x['date'][:4];e['electionMethod']=x['method'];e['totalSeats']=1;e['majorityThreshold']=None
 e['results']=[]
 for row in x['rows']:
  r=result(row['name'],'Proposer / party affiliation unassessed',row['votes'],1 if row['winner'] else 0);r['winner']=row['winner'];r['share']=round(row['votes']/x['valid']*100,6);e['results'].append(r)
 e['turnout']=round(x['voters']/x['eligible']*100,6);e['voteBasis']=f"Candidate votes / {x['valid']} valid ballots in this electoral body";e['resultCoverage']='complete';winner=next(r['name'] for r in e['results'] if r['winner']);e['summary']=winner+' was elected to the National Council for '+x['area']+'.'
 e['notes']=f"One replacement seat in the 40-member National Council. Eligible {'voters' if x['method']=='direct' else 'electors'}: {x['eligible']}; participants: {x['voters']}; valid ballots: {x['valid']}. Separate electoral bodies are not combined into one percentage table. The Council represents local and functional interests. Party affiliations and ideology are unassessed. "
 if x['date']=='1997-04-20':e['notes']+='This historical replacement contest was a direct public vote, as stated in the certified report, rather than the modern indirect electoral-college procedure. '
 if x['date']=='2018-12-17':e['notes']+='The certified report confirms Monday 17 December; the archive landing page incorrectly describes the day as Thursday. '
 if x['date']=='2023-05-31':e['notes']+='Repeat vote after the Constitutional Court annulled the culture-and-sport contest. '
 e['sources']=[dict(label='DVK contest archive',url=x['source']),dict(label='Certified result report',url=x['report'])];records.append(e);audit.append(dict(id=e['id'],validVotes=x['valid'],recordedVotes=sum(r['votes'] for r in e['results']),voteGap=0,recordedSeats=1))
# Comparable seat changes only where the previous consecutive general election explicitly identifies the same party name or profile.
assemblies=sorted([e for e in records if e['body'].startswith('National Assembly')],key=lambda e:e['startDate'])
for prev,e in zip(assemblies,assemblies[1:]):
 for r in e['results']:
  match=next((p for p in prev['results'] if (r.get('partyId') and p.get('partyId')==r['partyId']) or p['name'].upper().replace(' – ',' - ')==r['name'].upper().replace(' – ',' - ')),None)
  if match and match['seats'] is not None:r['previousSeats']=match['seats']
 if any(r['previousSeats'] is not None for r in e['results']):e['sources'].append(dict(label='Previous comparable general election (seat changes)',url=prev['sources'][0]['url']))
for e in records:
 for r in e['results']:
  if e['type']=='parliamentary' and e['startDate'][:4] in ['2018','2022','2026']:
   for p in profiles:
    if r['name'].upper().replace(' – ',' - ') in [p['name'], 'SOCIALNI DEMOKRATI - SD' if p['short_name']=='SD' else p['name']]:
     r['partyId']=p['id'];break
 linked=[r['id'] for r in records if r['seriesId']==e['seriesId'] and r['id']!=e['id']]
 if linked:e['linkedElectionIds']=linked
(OUT/'parties.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2)+'\n')
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');(OUT/'reconciliation.json').write_text(json.dumps(audit,indent=2)+'\n')
print('Built',len(records),'records')
