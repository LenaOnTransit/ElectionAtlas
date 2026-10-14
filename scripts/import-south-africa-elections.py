"""Reproduce the sourced democratic-era South Africa import; does not publish.

Input: existing 1999–2019 records checked 2026-10-13 and the transcribed
IEC-linked 21 June 2024 national ballot table. Output: reviewable records,
party profiles and a transaction guarded against concurrent editor changes.
"""
import json, re, uuid, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scripts'
CHECKED='2026-10-14'
BASE=json.loads((OUT/'south-africa-baseline.json').read_text())
NATIONAL=json.loads((OUT/'south-africa-2024-national.json').read_text())
S=lambda label,url:dict(label=label,url=url)
W=lambda year:S(f'{year} national results and historical references',f'https://en.wikipedia.org/wiki/{year}_South_African_general_election')
IPU=lambda year,upper=False:S('Inter-Parliamentary Union — historical election record',f'https://data.ipu.org/election-summary/HTML/229{2 if upper else 1}_{str(year)[2:]}.htm')
SOC='ideology-2da13b9e-92bd-488f-9f72-de3dbbacaa39'
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def canon(s):
    k=slug(s)
    return {'pan-africanist-congress-of-azania':'pan-africanist-congress','african-people-s-convention':'african-people-s-convention','free-democrats':'free-democrats','south-african-royal-kingdoms-organization':'south-african-royal-kingdoms-organisation'}.get(k,k)
# Keep historically distinct parties separate; never conflate an ANC military
# wing with the party founded in 2023, or the Democratic Party with the DA.
INFO={
'african-national-congress':('ANC','#c0a22b',['social-democracy','nationalism'],'African_National_Congress'),
'democratic-alliance':('DA','#2767ad',['liberalism'],'Democratic_Alliance_(South_Africa)'),
'democratic-party':('DP','#6699CC',['liberalism'],'Democratic_Party_(South_Africa)'),
'national-party':('NP','#ff9933',['conservatism','nationalism'],'National_Party_(South_Africa)'),
'new-national-party':('NNP','#ff9933',['conservatism'],'New_National_Party_(South_Africa)'),
'inkatha-freedom-party':('IFP','#FF0000',['conservatism'],'Inkatha_Freedom_Party'),
'freedom-front':('FF','#FF6600',['conservatism','nationalism'],'Freedom_Front_Plus'),
'freedom-front-plus':('FF+','#FF6600',['conservatism','nationalism'],'Freedom_Front_Plus'),
'african-christian-democratic-party':('ACDP','#ba0c2f',['christian-democracy','social-conservatism'],'African_Christian_Democratic_Party'),
'united-christian-democratic-party':('UCDP','#77A32E',['christian-democracy'],'United_Christian_Democratic_Party'),
'pan-africanist-congress':('PAC','#008718',['nationalism',SOC],'Pan_Africanist_Congress_of_Azania'),
'united-democratic-movement':('UDM','#FFB300',['social-democracy'],'United_Democratic_Movement'),
'independent-democrats':('ID','#ef8321',['social-liberalism'],'Independent_Democrats'),
'economic-freedom-fighters':('EFF','#bc3138',['marxism-leninism'],'Economic_Freedom_Fighters'),
'rise-mzansi':('RISE','#F7C600',['social-democracy'],'Rise_Mzansi'),
'umkhonto-wesizwe':('MK','#4D6B27',['left-wing-populism','nationalism'],'UMkhonto_weSizwe_(political_party)'),
'congress-of-the-people':('COPE','#FFCA08',['social-democracy','social-liberalism'],'Congress_of_the_People_(South_African_political_party)'),
'patriotic-alliance':('PA','#388F35',['national-conservatism','right-wing-populism'],'Patriotic_Alliance'),
'actionsa':('ActionSA','#00A859',['classical-liberalism'],'ActionSA'),
'build-one-south-africa':('BOSA','#582D83',['liberalism'],'Build_One_South_Africa'),
'good':('GOOD','#F36900',['social-democracy'],'Good_(political_party)'),
'al-jama-ah':('Al Jama-ah','#1c9069',['islamism'],'Al_Jama-ah'),
'african-transformation-movement':('ATM','#00ADEE',['conservatism'],'African_Transformation_Movement'),
'national-coloured-congress':('NCC','#000000',['minority-politics'],'National_Coloured_Congress'),
'united-africans-transformation':('UAT','#667085',[SOC],'United_Africans_Transformation'),
}
PROFILES={}
COLORS={canon(r['name']):r['color'] for e in BASE for r in e['results']}
NAMES={canon(r['name']):r['name'] for e in BASE for r in e['results']}
SOURCES={
'umkhonto-wesizwe':S('2024 party programme and ideological profile','https://africaelects.com/south-africa/'),
'democratic-alliance':S('DA — values and principles','https://www.da.org.za/why-the-da/values-and-principles'),
'economic-freedom-fighters':S('EFF — founding principles','https://effonline.org/about-us/'),
'rise-mzansi':S('RISE Mzansi — People’s Declaration','https://risemzansi.co.za/policies/peoples-declaration'),
'pan-africanist-congress':S('PAC — basic documents and philosophy','https://pac.org.za/'),
}
def decorate(r,year):
    k=canon(r['name']); short,color,tags,page=INFO.get(k,('',COLORS.get(k,'#667085'),[],''))
    color=COLORS.get(k,color)
    r.update(party=short,color=color,ideologyIds=[t if t.startswith('ideology-') else 'ideology-'+t for t in tags])
    if tags:
        src=SOURCES.get(k,S('Party history and political programme',f'https://en.wikipedia.org/wiki/{page}'))
        r['ideologyBasis']=dict(kind='party-era',year=year,note='Broad party tradition in this election era. This is an editorial classification of the party, not a claim about every member or candidate.',sources=[src])
    else:
        r['ideologyBasis']=dict(kind='unassessed',year=year,note='',sources=[])
    pid=str(uuid.uuid5(uuid.NAMESPACE_URL,'worldofelections.com/party/za/'+k))
    r['partyId']=pid
    PROFILES[k]=dict(id=pid,country_id='za',name=NAMES.get(k,r['name']),short_name=short,color=color,ideology_ids=r['ideologyIds'],notes='',archived=False)
    return r

def result(name,votes=None,share=None,seats=None,winner=False):
    return dict(id=canon(name),name=name,party='',color='#667085',votes=votes,share=share,seats=seats,previousSeats=None,electoralVotes=None,winner=winner,ideologyIds=[])

def election(id,date,title,body,seats=None,method='direct',type='parliamentary',end=''):
    return dict(id=id,countryId='za',title=title,type=type,body=body,startDate=date,endDate=end,precision='day',dateStatus='confirmed',status='held',publication='published',round='',seriesId='',snap=False,summary='',government='',turnout=None,totalSeats=seats,resultStatus='final',resultCoverage='complete',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=1,electionMethod=method,linkedElectionIds=[])

first=[('African National Congress',12237655,62.65,252),('National Party',3983690,20.39,82),('Inkatha Freedom Party',2058294,10.54,43),('Freedom Front',424555,2.17,9),('Democratic Party',338426,1.73,7),('Pan Africanist Congress',243478,1.25,5),('African Christian Democratic Party',88104,.45,2),('Africa Muslim Party',34466,.18,0),('African Moderates Congress Party',27690,.14,0),('Dikwankwetla Party of South Africa',19451,.10,0),('Federal Party',17663,.09,0),('Minority Front',13433,.07,0),('Sport Organisation for Collective Contributions and Equal Rights',10575,.05,0),('African Democratic Movement',9886,.05,0),("Women's Rights Peace Party",6434,.03,0),('Ximoko Progressive Party',6320,.03,0),('Keep It Straight and Simple Party',5916,.03,0),("Workers' List Party",4169,.02,0),('Luso-South African Party',3293,.02,0)]
na=election('world-south-africa-1994','1994-04-26','South Africa National Assembly election 1994','National Assembly',400,end='1994-04-29')
na.update(results=[result(*x) for x in first],turnout=86.9,sources=[IPU(1994),S('South African History Online — all 19 national lists','https://www.sahistory.org.za/sites/default/files/election_results_1994.pdf')],summary='South Africa’s first national election with universal adult suffrage returned 252 seats for the African National Congress, 82 for the National Party and 43 for the Inkatha Freedom Party.',notes='Voting, including special voting on 26 April and extensions in some areas on 29 April, took place from 26 to 29 April. Turnout is an estimate based on the estimated eligible electorate; there was no conventional nationwide voters’ roll. Previous seats are not comparable with the apartheid-era tricameral Parliament.')
ASSEMBLIES=[na]+[copy.deepcopy(e) for e in BASE if not e['startDate'].startswith('2024')]
seats2024=[159,87,58,39,17,9,6,6,3,3,2,2,2,2,2,1,1,1]+[0]*34
assert len(NATIONAL)==52
latest=election('world-south-africa-2024','2024-05-29','South Africa National Assembly election 2024','National Assembly',400)
latest.update(results=[result(r['name'],r['votes'],r['share'],s) for r,s in zip(NATIONAL,seats2024)],turnout=58.64,sources=[S('IEC — national ballot results report, 21 June 2024','https://results.elections.org.za/home/NPEPublicReports/1334/National%20Ballot/Results%20Report/National.pdf'),S('National and regional ballot tables with IEC references','https://en.wikipedia.org/wiki/Results_of_the_2024_South_African_general_election'),S('Final 400-seat allocation','https://www.reuters.com/world/africa/south-africas-anc-wins-159-seats-national-assembly-says-electoral-commission-2024-06-02/')],summary='The African National Congress won 159 seats and lost its outright majority. The Democratic Alliance won 87 seats, uMkhonto weSizwe 58 and the Economic Freedom Fighters 39.',notes='Votes and shares cover all 52 parties on the national ballot, using the IEC-linked revised national table of 16,078,093 valid votes. Seats are the full 400-seat National Assembly allocation, combining 200 national-list and 200 regional seats. Regional ballots, including regional independent candidates, are excluded from the vote column. Earlier declaration tables report slightly different national vote counts. Previous seats refer to the 2019 election allocation; new parties have zero previous seats.')
ASSEMBLIES.append(latest)
ASSEMBLIES.sort(key=lambda e:e['startDate'])
prev={}
# Explicit continuity only; merged party totals are not invented.
continuity={'new-national-party':'national-party','freedom-front-plus':'freedom-front'}
for e in ASSEMBLIES:
    year=int(e['startDate'][:4])
    e.update(title=f'South Africa National Assembly election {year}',seriesId='south-africa-national-assembly',electionMethod='direct',checked=CHECKED,majorityThreshold=201)
    e['version']=next((b['version']+1 for b in BASE if b['id']==e['id']),1)
    e['voteBasis']='Valid national National Assembly ballots; seats include national and regional allocations'
    if year!=1994:
        e['notes']+='\n\nPrevious seats refer to the preceding election allocation, excluding later floor crossings and vacancies. The National Party/New National Party and Freedom Front/Freedom Front Plus retain their predecessor comparisons. The DA’s 2004 previous seats are blank because its formation and alliances make a single-party comparison misleading.'
    if not e['summary']:
        e['summary']=f"The African National Congress won {e['results'][0]['seats']} of the 400 National Assembly seats in South Africa’s {year} national election."
    for r in e['results']:
        k=canon(r['name'])
        r['previousSeats']=None if year==1994 else prev.get(k,prev.get(continuity.get(k,''),0))
        if year==2004 and k=='democratic-alliance': r['previousSeats']=None
        decorate(r,year)
    prev={canon(r['name']):r['seats'] for r in e['results']}
    assert sum(r['seats'] for r in e['results'])==400

# Permanent NCOP delegates only: the 36 rotating special delegates are not
# seats elected to a fixed term. Do not mix their allocations into comparisons.
UPPER={1994:[('African National Congress',60),('National Party',17),('Inkatha Freedom Party',5),('Freedom Front',5),('Democratic Party',3)],1999:[('African National Congress',32),('Democratic Party',7),('New National Party',7),('Inkatha Freedom Party',3),('United Democratic Movement',2),('African Christian Democratic Party',2),('United Christian Democratic Party',1)],2004:[('African National Congress',35),('Democratic Alliance',10),('Inkatha Freedom Party',3),('New National Party',2),('United Democratic Movement',1),('Independent Democrats',1),('Freedom Front Plus',1),('United Christian Democratic Party',1)],2009:[('African National Congress',35),('Democratic Alliance',10),('Congress of the People',7),('Independent Democrats',1),('Inkatha Freedom Party',1)],2014:[('African National Congress',33),('Democratic Alliance',13),('Economic Freedom Fighters',6),('Inkatha Freedom Party',1),('United Democratic Movement',1)],2019:[('African National Congress',29),('Democratic Alliance',13),('Economic Freedom Fighters',9),('Freedom Front Plus',2),('Inkatha Freedom Party',1)],2024:[('African National Congress',24),('Democratic Alliance',12),('Economic Freedom Fighters',8),('uMkhonto weSizwe',5),('Freedom Front Plus',2),('Inkatha Freedom Party',1),('Patriotic Alliance',1),('United Democratic Movement',1)]}
DATES={1994:'1994-04-26',1999:'1999-06-02',2004:'2004-04-14',2009:'2009-04-22',2014:'2014-05-21',2019:'2019-05-23',2024:'2024-06-15'}
upper=[]; previous={}
for year,allocation in UPPER.items():
    senate=year==1994; body='Senate' if senate else 'National Council of Provinces'
    e=election(f'world-south-africa-{ "senate" if senate else "ncop"}-{year}',DATES[year],f'South Africa {body} election {year}',body if senate else body+' — permanent delegates',90 if senate else 54,'indirect',end='1994-04-29' if senate else '')
    e.update(seriesId='south-africa-upper-chamber',voteBasis='Indirect provincial-legislature selection; no national popular-vote total',sources=[IPU(year,True),W(year)] if year<=2009 else [S('IPU — upper chamber renewal',f'https://data.ipu.org/parliament/ZA/ZA-UC01/election/ZA-UC01-E{DATES[year].replace("-","")}/'),W(year)])
    e['summary']=f'The {body} was constituted indirectly through South Africa’s provincial legislatures. '+('All 90 Senate seats are recorded.' if senate else 'This table covers the 54 permanent delegates; the 36 rotating special delegates are excluded.')
    e['notes']='Party seats follow the cited upper-chamber record. Votes, vote shares and elector participation are blank because this is an indirect provincial-legislature allocation, not a national popular ballot. '+('The date range is the provincial election cycle that determined the Senate, which first met on 20 May 1994.' if senate else 'Only permanent delegates are counted in this table and its seat comparisons.')
    if year in (1999,2004,2009): e['notes']+=' The date follows the general-election cycle used by the IPU historical archive, rather than implying a simultaneous public vote for upper-chamber delegates.'
    if year==1999: e['notes']+=' The permanent-party distribution follows the IPU historical record (ANC 32, IFP 3, ACDP 2); South Africa Survey 2002/03 gives a different within-term composition (ANC 34, IFP 2, ACDP 1). No counts from the two snapshots are combined.'
    if year==2024: e['notes']+=' The renewal date is 15 June, the first sitting reported by Parliament and the IPU; provincial legislatures selected their delegations on 13–14 June.';e['sources']+=[S('Parliament — first sitting and 54 permanent delegates','https://www.parliament.gov.za/press-releases/ncop-hold-its-first-sitting-and-elects-its-office'),S('Permanent and special delegate composition','https://en.wikipedia.org/wiki/National_Council_of_Provinces')]
    if year==2019:e['sources']+=[S('Parliament — designated delegates by province','https://www.gov.za/news/media-statements/parliament-current-composition-newly-sworn-6th-parliament-06-jun-2019')]
    for name,seats in allocation:
        r=result(name,seats=seats);k=canon(name)
        r['previousSeats']=None if year in (1994,1999) else previous.get(k,previous.get(continuity.get(k,''),0))
        if year==2004 and k=='democratic-alliance': r['previousSeats']=None
        e['results'].append(decorate(r,year))
    assert sum(r['seats'] for r in e['results'])==e['totalSeats']
    previous={canon(r['name']):r['seats'] for r in e['results']};upper.append(e)

# Every substantive parliamentary presidential selection, including the two
# mid-term replacements. Acting appointments without an election are excluded.
PRES=[('1994-05-09','Nelson Mandela',None,None,IPU(1994)),('1999-06-14','Thabo Mbeki',None,None,S('Mbeki elected unopposed','https://mg.co.za/news/south-africa/1999-06-14-mbeki-chosen-as-next-president/')),('2004-04-23','Thabo Mbeki',None,None,S('Parliament — unopposed presidential election','https://www.parliament.gov.za/storage/app/media/NA-Procedural-Devs/10.pdf')),('2008-09-25','Kgalema Motlanthe',269,('Joe Seremane','Democratic Alliance',50),S('Presidential ballot result','https://mg.co.za/news/south-africa/2008-09-25-motlanthe-elected-south-african-president/')),('2009-05-06','Jacob Zuma',277,('Mvume Dandala','Congress of the People',47),S('Government news service — presidential vote','https://www.sanews.gov.za/south-africa/jacob-zuma-elected-sas-new-president')),('2014-05-21','Jacob Zuma',None,None,S('Parliament — 2014 presidential election','https://www.parliament.gov.za/storage/app/media/Publications/InSession/2014-05/final.pdf')),('2018-02-15','Cyril Ramaphosa',None,None,S('Parliament — Ramaphosa elected president','https://www.parliament.gov.za/news/ramaphosa-elected-president-rsa')),('2019-05-22','Cyril Ramaphosa',None,None,S('Parliament — election of President','https://www.gov.za/news/media-statements/parliament-elects-president-speaker-and-deputy-speaker-22-may-2019')),('2024-06-14','Cyril Ramaphosa',283,('Julius Malema','Economic Freedom Fighters',44),S('Parliament — complete candidate vote counts','https://parliament.gov.za/press-releases/national-assembly-elects-cyril-ramaphosa-president-elect'))]
presidents=[]
for date,name,votes,opponent,src in PRES:
    year=int(date[:4]); e=election(f'world-south-africa-presidential-{year}',date,f'South Africa presidential election {year}','President of South Africa',method='indirect',type='presidential')
    e.update(seriesId='south-africa-president',sources=[src],voteBasis='Valid National Assembly presidential ballots; no national popular vote',summary=f'{name} was elected President of South Africa by the National Assembly'+(' without opposition.' if votes is None else '.'),snap=year in (2008,2018))
    e['notes']='The President is elected by members of the National Assembly. This record covers the parliamentary selection, not the general election or the inauguration. '+('A sole nominee was declared elected without a counted contest; votes, vote share and turnout are therefore blank.' if votes is None else 'Vote shares use valid votes for the two nominated candidates, excluding spoilt ballots. No public turnout figure is applied to the parliamentary ballot.')
    if year==2008: e['notes']+=' Contemporary accounts differ on the total ballots cast (360 or 361); elector participation is left blank.'
    for candidate,party,count in [(name,'African National Congress',votes)]+([opponent] if opponent else []):
        r=decorate(result(party),year);r.update(id=slug(candidate),name=candidate,party=party,votes=count,share=None if count is None else count/(votes+opponent[2])*100,seats=None,previousSeats=None,winner=candidate==name)
        r['ideologyBasis']['note']='Party tradition is shown for affiliation context; no separate personal ideology is inferred.' if r['ideologyIds'] else ''
        e['results'].append(r)
    presidents.append(e)

records=sorted(ASSEMBLIES+upper+presidents,key=lambda e:e['startDate'])
for e in records:
    # Link chamber and presidential selections within the same electoral cycle.
    year=e['startDate'][:4]
    e['linkedElectionIds']=[x['id'] for x in records if x['id']!=e['id'] and x['startDate'].startswith(year)]
for name,value in [('south-africa-election-records',records),('south-africa-party-profiles',list(PROFILES.values()))]:
    (OUT/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
# Baseline guards prevent overwriting intervening editor work. Profiles use
# deterministic IDs, and existing names are checked before applying this import.
def lit(s):return "'"+s.replace("'","''")+"'"
def j(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'
lines=['begin;','do $import$ begin']
for b in BASE:
    lines+=[f"if not exists(select 1 from public.ea_records where id={lit(b['id'])} and data={j(b)}) then raise exception 'Election changed since baseline: {b['id']}'; end if;"]
for e in records:
    if not any(b['id']==e['id'] for b in BASE):lines+=[f"if exists(select 1 from public.ea_records where id={lit(e['id'])}) then raise exception 'Election already exists: {e['id']}'; end if;"]
lines+=['end $import$;']
for p in PROFILES.values():
    arr='ARRAY['+','.join(lit(x) for x in p['ideology_ids'])+']::text[]'
    lines+=[f"insert into public.ea_country_parties(id,country_id,name,short_name,color,ideology_ids,notes,archived) values ({lit(p['id'])}::uuid,'za',{lit(p['name'])},{lit(p['short_name'])},{lit(p['color'])},{arr},'',false) on conflict(id) do nothing;"]
for e in records:
    lines+=[f"insert into public.ea_records(id,kind,data,updated) values ({lit(e['id'])},'world_election',{j(e)},now()) on conflict(id) do update set data=excluded.data,updated=excluded.updated;"]
lines += ["update public.ea_records set data=jsonb_set(data,'{coverageNote}',to_jsonb('Democratic-era national elections, 1994–2024: National Assembly results, indirect upper-chamber renewals and parliamentary presidential elections. National-ballot party tables include zero-seat parties. NCOP results count permanent delegates; earlier apartheid-era elections are outside this series.'::text)),updated=now() where id='world-country-za';"]
lines+=['commit;']
(OUT/'south-africa-election-import.sql').write_text('\n'.join(lines)+'\n')
print(f'{len(records)} election records, {len(PROFILES)} party profiles; 7 assembly, 7 upper chamber, 9 presidential selections')
