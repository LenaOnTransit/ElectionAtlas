"""Build reviewed PRC national institution records; never substitute attendance for membership.
Run this generator and scripts/check-china-elections.mjs before importing the JSON.
NPC cycles are indexed by their opening year, not an invented national polling day.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CHECKED='2026-10-05'
def src(label,url):return {'label':label,'url':url}
NBS=src('National Bureau of Statistics: 2011 yearbook, table 23-1, historical NPC deputy totals','https://www.stats.gov.cn/sj/ndsj/2011/html/W2301e.htm')
METHOD=src('NPC: national legislature structure and indirect electoral bodies','https://en.npc.gov.cn.cdurl.cn/2023-03/10/c_670999.htm')
HISTORY=src('People’s Daily / CPC: state-presidency history and officeholders','https://cpc.people.com.cn/daohang/n/2013/0307/c357001-20703935.html')
CONSULT=src('NPC news: deputy credentials history, including consultation in 1975 and validated 1988 membership','https://npc.people.com.cn/n/2015/0120/c14576-26415070.html')
SCOPE='Our archive covers the national institutions of the People’s Republic of China. It does not include Republic of China elections or separate Hong Kong or Macao contests. National NPC totals retain the institution’s own delegations, including special administrative region delegations where applicable and its mainland-selected Taiwan delegation; this is not a record of elections conducted by Taiwan’s electorate.'
YEARS=[1954,1959,1964,1975,1978,1983,1988,1993,1998,2003,2008,2013,2018,2023]
TOTALS=[1226,1226,3040,2885,3497,2978,2970,2978,2979,2984,2987,2987,2980,2977]
PRES=[('1954-09-27','Mao Zedong',1954),('1959-04-27','Liu Shaoqi',1959),('1965-01-03','Liu Shaoqi',1964),('1983-06-18','Li Xiannian',1983),('1988-04-08','Yang Shangkun',1988),('1993-03-27','Jiang Zemin',1993),('1998-03-16','Jiang Zemin',1998),('2003-03-15','Hu Jintao',2003),('2008-03-15','Hu Jintao',2008),('2013-03-14','Xi Jinping',2013),('2018-03-17','Xi Jinping',2018),('2023-03-10','Xi Jinping',2023)]
def base(year,office):return dict(id=f'world-cn-{office}-{year}',countryId='cn',title='',type='parliamentary' if office=='npc' else 'presidential',body='National People’s Congress' if office=='npc' else 'President of the People’s Republic of China',startDate=f'{year}-01-01',endDate='',precision='year',dateStatus='expected',status='held',publication='published',round='Institutional selection',seriesId=f'cn-{office}',snap=False,summary='',government='',turnout=None,totalSeats=None,resultStatus='final',resultCoverage='partial',voteBasis='',results=[],sources=[],checked=CHECKED,notes='',articleId='',version=0,electionMethod='indirect',linkedElectionIds=[])
def result(name,**kwargs):return dict(id=name.lower().replace(' ','-'),name=name,party='',color='#8993a2',votes=None,share=None,seats=None,electoralVotes=None,winner=False,ideologyIds=[],**kwargs)
COMPOSITION=json.loads((ROOT/'china-npc-composition-sources.json').read_text())
records=[]
for n,(year,total) in enumerate(zip(YEARS,TOTALS),1):
 e=base(year,'npc');e['title']=f'National People’s Congress · {n}{"st" if n==1 else "nd" if n==2 else "rd" if n==3 else "th"} term';e['totalSeats']=total
 e['summary']=f'NPC term {n} is recorded with {total:,} deputies in the cited institutional series. This is a national legislature membership record, not a competitive nationwide party vote.'
 e['voteBasis']='Reported NPC deputy membership; party affiliations and selection ballots not tabulated'
 r=result('Deputies — party affiliation not tabulated');r.update(id='npc-deputies',seats=total);e['results']=[r]
 e['sources']=[NBS,METHOD] if year<=2008 else [METHOD]
 if year==2013:e['sources'].insert(0,src('Xinhua: authorized list of 2,987 deputies to the 12th NPC','https://www.xinhuanet.com/2013lh/2013-02/27/c_114824100.htm'))
 if year==2018:e['sources'].insert(0,src('NPC Standing Committee: 2,980 validated deputies to the 13th NPC','https://www.gov.cn/xinwen/2018-02/24/content_5268520.htm'))
 if year==2023:e['sources'].insert(0,src('NPC Standing Committee: 2,977 validated deputies to the 14th NPC','https://paper.people.com.cn/rmrb/html/2023-02/25/nw.D110000renmrb_20230225_4-03.htm'))
 e['notes']=SCOPE+'\n\nThe date is an archive cycle year, generally the year the new NPC first convened. Deputy selection takes place across different bodies and can start in the preceding year; 1 January is a storage anchor, not an election day. Membership totals follow the cited historical series through 2008 and the initial validated deputy lists for 2013–2023. They are not attendance totals, maximum quotas or the current membership after later vacancies and replacements.\n\nParty-level composition and nationwide selection ballot totals have not been verified for this record. The grey membership category represents unclassified deputies, not a political party, independents, an opposition bloc or a shared ideology. No popular vote share or popular turnout is inferred.'
 if year==1959:e['notes']+='\n\nThe cited NBS series reports 1,226 deputies for this cycle. Some later lists use a different total; our figure is explicitly tied to this statistical series rather than treating all published totals as interchangeable.'
 if year==1964:e['notes']+='\n\nThe third NPC’s first session continued into January 1965, when it re-elected Liu Shaoqi president. That selection has a separate 1965 presidential record.'
 if year==1975:
  e['summary']='The fourth NPC was constituted with 2,885 deputies selected by consultation during the Cultural Revolution. This was not an ordinary election under the electoral law.'
  e['voteBasis']='Membership after selection by consultation; no competitive party ballot'
  e['sources'].append(CONSULT);e['notes']+='\n\nNPC historical reporting states that fourth-term deputies were chosen through consultation rather than election. The indirect-method category identifies a non-popular institutional selection and does not assert that ordinary electoral procedures were followed.'
 if year in (1975,1978):e['sources'].append(HISTORY);e['notes']+='\n\nThe 1975 and 1978 constitutions did not provide for the state presidency. The office was restored in the 1982 Constitution; no presidential selection is invented for this cycle.'
 if year==1988:e['sources'].append(CONSULT);e['notes']+='\n\nThe credential review initially validated 2,970 deputies against a quota of 2,978; five of 2,975 initially selected deputies failed the statutory vote requirement. Later supplementary selections are not added to this initial total.'
 if year in (2013,2018,2023):e['notes']+=f'\n\nDeputy selection for this cycle spanned late {year-1} and early {year}; the archive indexes the resulting NPC by {year}.'
 composition=COMPOSITION.get(str(year))
 if composition:
  e['version']=1;e['results']=[]
  for row in composition['rows']:
   r=result(row['name']);r.update(id=row['id'],party=row.get('party',''),color=row['color'],seats=row['seats']);e['results'].append(r)
  remainder=total-sum(r['seats'] or 0 for r in e['results'])
  assert remainder>=0
  if remainder:
   r=result(composition['remainderLabel']);r.update(id='npc-unclassified',seats=remainder);e['results'].append(r)
  e['sources']+=composition['sources']
  e['voteBasis']='NPC deputy membership by reported affiliation; no national popular vote'
  e['notes']=e['notes'].replace('Party-level composition and nationwide selection ballot totals have not been verified for this record. The grey membership category represents unclassified deputies, not a political party, independents, an opposition bloc or a shared ideology. No popular vote share or popular turnout is inferred.',composition['note']+' The grey remainder is not an independent party, an opposition bloc or a shared ideology. A dash means a count is unknown, not zero. No popular vote shares are inferred. Colours distinguish categories visually; they do not signify competing electoral lists.')
 e['linkedElectionIds']=[f'world-cn-president-{d[:4]}'for d,_,cycle in PRES if cycle==year];records.append(e)
for date,name,cycle in PRES:
 year=int(date[:4]);e=base(year,'president');e.update(title='President · NPC selection',startDate=date,precision='day',dateStatus='confirmed',summary=f'{name} was elected president of the People’s Republic of China by the National People’s Congress. This was an indirect state-office selection, not a nationwide popular presidential election.',voteBasis='NPC selection of the state president; any figures are approval ballots, not popular votes',linkedElectionIds=[f'world-cn-npc-{cycle}'])
 r=result(name);r.update(party='Communist Party of China',color='#c63735',winner=True);e['results']=[r];e['sources']=[HISTORY]
 if year<=1998 and year!=1993:e['sources'].insert(0,src(f'NPC announcement of {year}: original selection declaration, transcribed at Wikisource',f'https://zh.wikisource.org/wiki/中华人民共和国全国人民代表大会公告/{year}年'))
 if year==1993:e['sources'].insert(0,src('Yantian government historical archive: Jiang Zemin elected on 27 March 1993','https://www.yantian.gov.cn/ytdayszxxw/lsjt/content/post_11737171.html'))
 if year==2003:e['sources'].insert(0,src('China Daily: contemporary report of Hu Jintao’s election, 15 March 2003','https://www.chinadaily.com.cn/en/doc/2003-03/15/content_158115.htm'))
 if year==2008:e['sources'].insert(0,src('Xinhua / China Daily: NPC elects leaders, 15 March 2008','https://www.chinadaily.com.cn/china/2008npc/2008-03/15/content_6539344.htm'))
 if year==2013:e['sources'].insert(0,src('NPC: selection of Xi Jinping on 14 March 2013','https://www.npc.gov.cn/zgrdw/englishnpc/news/Events/2013-03/15/content_1784435.htm'))
 if year==2018:e['sources']=[src('Xinhua: live NPC transcript, 2,970 presidential approval ballots','https://www.xinhuanet.com/politics/2018lh/zb/gov_20180317a/wzsl.htm'),src('Supreme People’s Procuratorate / Xinhua: unanimous presidential selection','https://www.spp.gov.cn/spp/zdgz/201803/t20180318_371226.shtml')];r.update(votes=2970,share=100);e['resultCoverage']='complete'
 if year==2023:e['sources']=[src('NPC / Xinhua: Xi Jinping unanimously elected president, 2,952 votes','https://subsites.chinadaily.com.cn/npc/2023-03/11/c_868263.htm'),src('Ministry of Education / Xinhua: 2,952 ballots issued, returned and approved','https://www.moe.gov.cn/jyb_xwfb/xw_zt/moe_357/2023/2023_zt02/yw/202303/t20230311_1050345.html')];r.update(votes=2952,share=100);e['resultCoverage']='complete'
 if year in (2003,2008,2013):
  votes,against,abstained,reference={2003:(2937,None,None,src('VOA: contemporary presidential count, 2,937 approvals and seven opposition or abstention ballots','https://www.voachinese.com/a/a-21-a-2003-03-15-5-1-63308907/982908.html')),2008:(2956,3,5,src('Reuters / Der Standard: contemporary count, 2,956 approvals, three against, five abstentions','https://www.derstandard.at/story/3265923/staats-und-regierungsspitze-vom-volkskongress-bestaetigt')),2013:(2952,1,3,src('VOA: contemporary presidential count, 2,952 approvals, one against, three abstentions','https://www.voachinese.com/a/xi-jinping-china-20130315/1622057.html'))}[year]
  r['votes']=votes;e['sources'].append(reference)
 e['notes']=SCOPE+'\n\nThe state presidency is distinct from the Communist Party general secretary, party chairman, NPC Standing Committee chair and Central Military Commission offices. Our table records the elected state president only, not simultaneous selections for those offices or for vice president. Mao’s 1949 selection as Central People’s Government chairman was a different office and is not relabelled as a presidential election.\n\nNo candidate-specific ideology attribution has been added without a reviewed source. Missing ballot figures are unknown, not zero. The country’s current legitimacy assessment is available on our country timeline and atlas; it is not backdated as an observer verdict on these historical selections.'
 if year in (2003,2008,2013):e['notes']+=f'\n\nContemporary reporting records {r["votes"]:,} presidential approval ballots. '+('Seven ballots were reported together as opposition or abstention; no split is inferred.' if year==2003 else f'{against} against and {abstained} abstentions were also reported.')+' Approval share is left unentered because a complete denominator including write-ins and invalid ballots has not been verified. Session attendance is not substituted for ballots cast.'
 elif year not in (2018,2023):e['notes']+='\n\nThe cited sources verify the elected officeholder and selection date. A complete presidential ballot tally has not been verified for this record; approval, opposition, abstention, write-in and invalid figures are therefore left unentered.'
 else:e['notes']+=f'\n\nThe official report records {r["votes"]:,} presidential ballots, all approving Xi Jinping. Approval share is 100% of those NPC ballots. Votes against or abstentions, when present, are ballot categories rather than rival candidates. This is neither 100% support among the population nor a measure of political competition. Absent deputies are excluded from the ballot denominator.'
 records.append(e)
assert len(records)==26 and len({e['id']for e in records})==26
(ROOT/'china-election-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('Generated 14 NPC cycles and 12 presidential selections; only verified numeric totals entered.')
