"""Build sourced UK House of Commons general election records; never publishes."""
from pathlib import Path
import json, uuid, re, unicodedata, hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scripts/uk-election-import'
OUT.mkdir(parents=True,exist_ok=True)
checked='2026-10-06'
source=json.loads((OUT/'official-results.json').read_text())
colors={
 'Conservative':'#0087dc','Labour':'#e4003b','Liberal Democrat':'#fdbb30',
 'Scottish National Party':'#fff95d','Plaid Cymru':'#005b54',
 'Democratic Unionist Party':'#d46a4a','Sinn Féin':'#326760',
 'UK Independence Party':'#70147a','The Brexit Party':'#12b6cf','Reform UK':'#12b6cf',
 'Green Party':'#6ab023','Green Party Northern Ireland':'#2e8b57',
 'Scottish Green Party':'#4aab38','Ulster Unionist Party':'#1683c4',
 'Social Democratic & Labour Party':'#2aa82c','Alliance':'#f6cb2f',
 'Traditional Unionist Voice':'#123b5d'
}
def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-') or 'party'

# Save reusable profiles for established parties that either won seats or had
# at least 0.5% of the UK vote in one of these elections. Lesser-known lists
# remain fully represented in the election results with neutral colours.
saved=set()
for election in source:
 for row in election['rows']:
  if row['seats'] or row['votes']/election['valid']>=0.005:saved.add(row['party'])
parties=[];party_ids={}
for name in sorted(saved):
 pid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://worldofelections.com/parties/gb/'+name))
 party_ids[name]=pid
 parties.append({'id':pid,'country_id':'gb','name':name,'short_name':name[:100],
  'color':colors.get(name,'#777777'),'ideology_ids':[],
  'notes':'Reusable UK election party profile. Election records retain period-specific results; no unsourced ideology classification is applied.','archived':False})

records=[]
for election in source:
 year=int(election['year'])
 date=election['dateISO']
 party_votes=sum(r['votes'] for r in election['rows'])
 party_seats=sum(r['seats'] for r in election['rows'])
 speaker=election['speaker']
 other_votes=election['valid']-party_votes-speaker['votes']
 other_seats=650-party_seats-1
 assert other_votes>=0 and other_seats>=0
 results=[]
 for row in election['rows']:
  name=row['party']
  item={'id':f"gb-{year}-{slug(name)}",'name':name,'party':name,
   'color':colors.get(name,'#777777'),'votes':row['votes'],
   'share':round(row['votes']/election['valid']*100,4),'seats':row['seats'],
   'electoralVotes':None,'winner':False}
  if name in party_ids:item['partyId']=party_ids[name]
  results.append(item)
 results.extend([
  {'id':f'gb-{year}-independent-and-non-party','name':'Independent and other non-party candidates',
   'party':'Non-party candidates','color':'#777777','votes':other_votes,
   'share':round(other_votes/election['valid']*100,4),'seats':other_seats,
   'electoralVotes':None,'winner':False},
  {'id':f'gb-{year}-commons-speaker','name':'Commons Speaker','party':'Commons Speaker',
   'color':'#777777','votes':speaker['votes'],
   'share':round(speaker['votes']/election['valid']*100,4),'seats':1,
   'electoralVotes':None,'winner':False}
 ])
 assert sum(r['votes'] for r in results)==election['valid'],year
 assert sum(r['seats'] for r in results)==650,year
 turnout=round(election['valid']/election['electorate']*100,3)
 major=max(election['rows'],key=lambda r:r['seats'])
 verdict='won an overall majority' if major['seats']>325 else 'won the most seats, but no party won an overall majority'
 notes=(f"Final UK-wide results from the UK Parliament Election Results archive. "
  f"Party votes and seats are transcribed for every registered party in the official table. "
  f"The Independent and other non-party candidates row aggregates the remaining {other_votes:,} valid votes and {other_seats} elected MPs after accounting for the official party table and the separately recorded Commons Speaker. "
  f"The Speaker is listed separately; the 650-seat total includes the Speaker. Sinn Féin MPs are included in seat totals although they do not take their seats. "
  f"Shares are calculated from exact votes as a proportion of {election['valid']:,} valid votes; turnout is valid votes divided by the official electorate. "
  f"Smaller parties with no reusable saved profile are still included with neutral display colours.")
 sources=[
  {'label':'UK Parliament: official election results by party', 'url':election['partyUrl']},
  {'label':'UK Parliament: official non-party candidate results, including the Speaker', 'url':election['nonPartyUrl']},
  {'label':'House of Commons Library: full results and analysis', 'url':election['libraryUrl']}
 ]
 rid='world-uk-commons-2024' if year==2024 else f'world-uk-general-{year}'
 record={'id':rid,'countryId':'gb','title':'General Election','type':'parliamentary',
  'body':'House of Commons','startDate':date,'endDate':'','precision':'day',
  'dateStatus':'confirmed','status':'held','publication':'published','round':'General',
  'seriesId':'UK-HOC','snap':year==2024,'summary':f"{major['party']} {verdict} with {major['seats']} seats.",
  'government':'','turnout':turnout,'totalSeats':650,'resultStatus':'final',
  'resultCoverage':'complete','voteBasis':f"{election['valid']:,} official valid votes",
  'results':results,'sources':sources,'checked':checked,'notes':notes,'articleId':'',
  'version':0,'electionMethod':'direct','majorityThreshold':326}
 records.append(record)

assert len(records)==5
for rec in records:
 assert len(rec['results'])==len({r['id'] for r in rec['results']})
 assert sum(r['share'] or 0 for r in rec['results'])<=100.01
(OUT/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'parties.json').write_text(json.dumps(parties,ensure_ascii=False,indent=2)+'\n')
audit={'checked':checked,'records':len(records),'savedParties':len(parties),
 'sources':[{'url':s['partyUrl'],'validVotes':s['valid'],'electorate':s['electorate'],
  'registeredParties':len(s['rows']),'partyVotes':sum(r['votes'] for r in s['rows']),
  'nonPartyVotes':s['valid']-sum(r['votes'] for r in s['rows'])-s['speaker']['votes'],
  'speakerVotes':s['speaker']['votes']} for s in source],
 'sha256':hashlib.sha256((OUT/'official-results.json').read_bytes()).hexdigest()}
(OUT/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(f"Built {len(records)} complete election records and {len(parties)} reusable party profiles.")
