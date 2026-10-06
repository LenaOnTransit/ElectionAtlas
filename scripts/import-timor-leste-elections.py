"""Generate the assigned Timor-Leste records; publish only after the model/audit check.
National and district ballots in 2001 are deliberately not combined.
Historical alliances retain their own identities and denominators.
"""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKED = '2026-10-06'
def source(label, url): return dict(label=label, url=url)
def wiki(year, office):
    return source('Secondary transcription: full result table and historical party labels', f'https://en.wikipedia.org/wiki/{year}_East_Timorese_{office}_election')
EU2007 = source('EU election observation mission: final report, annexes 1 and 2 (CNE final tables)', 'https://aceproject.org/ero-en/regions/pacific/TL/timor-leste-final-report-presidential-and/at_download/file')
UN2012 = source('UNMIT: 2012 election compendium, court-certified presidential tables, pp. 23 and 26', 'https://www.laohamutuk.org/misc/eleisaun2012/UNMITCompendium19Jun2012.pdf')
ANFREL2023 = source('ANFREL: 2023 final observation report, court validation and ballot totals', 'https://anfrel.org/wp-content/uploads/2023/07/ANFREL_2023-Timor-Leste-Parliamentary-Elections_20July2023-F.pdf')
def ipu(year): return source(f'IPU parliamentary archive: {year} election and elected seats', f'https://data.ipu.org/election-summary/HTML/2369_{str(year)[2:]}.htm')
def ifes(id): return source('IFES Election Guide: election results and participation', f'https://electionguide.org/elections/id/{id}/')

# Colours distinguish historical ballot entities; they are editorial display colours,
# not claims about a party's ideology or official branding.
PARTIES = {
 'fretilin': ('Revolutionary Front for an Independent East Timor','FRETILIN','#d32f2f'),
 'cnrt': ('National Congress for Timorese Reconstruction','CNRT','#2368ae'),
 'pd': ('Democratic Party','PD','#174b83'),
 'psd': ('Social Democratic Party','PSD','#ed8b23'),
 'asdt': ('Timorese Social Democratic Association','ASDT','#2c8a56'),
 'udt': ('Timorese Democratic Union','UDT','#477ab8'),
 'pnt': ('Timorese Nationalist Party','PNT','#91643c'),
 'kota': ('Association of Timorese Heroes','KOTA','#d2ad32'),
 'ppt': ("People's Party of Timor",'PPT','#775eaa'),
 'pdc': ('Christian Democratic Party','PDC','#9b703e'),
 'pst': ('Socialist Party of Timor','PST','#a83247'),
 'pl2001': ('Liberal Party (2001 ballot name)','PL','#b2a21e'),
 'udcpdc': ('Christian Democratic Union of Timor','UDC/PDC','#8d713f'),
 'apodeti': ('Timorese Popular Democratic Association','APODETI','#608771'),
 'pt': ('Timorese Labour Party','PT / PTT','#935045'),
 'parentil': ('National Republic Party of East Timor','PARENTIL','#48755b'),
 'pdm': ('Maubere Democratic Party','PDM','#667b9d'),
 'asdtpsd': ('ASDT–PSD electoral coalition','ASDT–PSD','#ca7c36'),
 'pun': ('National Unity Party','PUN','#a070a3'),
 'ad2007': ('Democratic Alliance (KOTA–PPT)','AD (KOTA–PPT)','#998140'),
 'undertim': ('National Unity of Timorese Resistance','UNDERTIM','#507d50'),
 'pdrt': ('Democratic Republic of Timor-Leste Party','PDRT','#5d8b8e'),
 'pr': ('Republican Party','PR','#b2673c'),
 'pmd': ('Millennium Democratic Party','PMD','#766d96'),
 'fm': ('Frenti-Mudança','FM','#d49c20'),
 'khunto': ('Kmanek Haburas Unidade Nasional Timor Oan','KHUNTO','#45974e'),
 'pdn': ('National Development Party','PDN','#886f55'),
 'plpapdrt': ('PLPA–PDRT electoral coalition','PLPA–PDRT','#608f9e'),
 'apmt': ("Timorese Monarchist People's Association",'APMT','#ad8b3a'),
 'bp': ('Coligação Bloco Proclamador (PMD–PARENTIL)','Bloku Proklamador','#756287'),
 'ad2012': ('Democratic Alliance (KOTA–PTT)','AD (KOTA–PTT)','#a99452'),
 'ptd': ('Timorese Democratic Party','PTD','#558b99'),
 'pdl': ('Democratic Liberal Party (2012 ballot name)','PDL','#ad9f29'),
 'pdp': ("People's Development Party",'PDP','#659cb0'),
 'plp': ("People's Liberation Party",'PLP','#edbc30'),
 'pudd': ('United Party for Development and Democracy','PUDD','#c45177'),
 'fpatria': ('Hope of the Fatherland Party','Frente Patriótica','#9776a5'),
 'bup': ('Bloku Unidade Popular (PMD–PLPA–PDRT)','BUP','#4f8a94'),
 'casdt': ('Timorese Social Democratic Action Center','CASDT','#847b40'),
 'mlpm': ('Maubere People’s Liberation Movement','MLPM','#b05858'),
 'amp2018': ('Alliance for Change and Progress (CNRT–PLP–KHUNTO)','AMP','#326bbb'),
 'fdd': ('Democratic Development Forum (PUDD–UDT–FM–PDN)','FDD','#895397'),
 'mdn': ('National Development Movement (APMT–PLPA–MLPM–UNDERTIM)','MDN','#6d875d'),
 'msd': ('Social Democratic Movement (CASDT–PSD–PST–PDC)','MSD','#c77b45'),
 'pvt': ('Green Party of Timor','PVT','#438c3d'),
 'plpa': ("People's Freedom Party of the Aileba",'PLPA','#587aa3'),
}
def party_id(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://worldofelections.com/party/tl/'+key))
used = set()
def row(key, votes, seats=None, name=None, previous=None, winner=False, advanced=False):
    if key == 'independent':
        pname, short, color = 'Independent', 'Independent', '#808080'
    else:
        used.add(key); pname, short, color = PARTIES[key]
    r = dict(id=key if name is None else str(uuid.uuid5(uuid.NAMESPACE_URL, 'tl-result/'+name)),name=name or pname,party=short,color=color,votes=votes,share=None,seats=seats,previousSeats=previous,electoralVotes=None,winner=winner,advanced=advanced,ideologyIds=[])
    if key != 'independent': r['partyId']=party_id(key)
    return r

records=[]; audits=[]
def election(date,office,round,valid,cast,registered,results,sources,summary,notes='',coverage='complete',government='',snap=False):
    year=int(date[:4]); pres=office=='president'
    id=f'world-tl-{date}-{office}'+(f'-r{round}' if pres else '')
    for r in results:
        if r['votes'] is not None: r['share']=r['votes']/valid*100
        if pres: r['ideologyBasis']=dict(kind='unassessed',year=year,note='No reviewed election-era candidate-specific classification or sourced party-era fallback is assigned.',sources=[])
    totals=sum(r['votes'] or 0 for r in results)
    assert totals==valid,(date,totals,valid)
    totalSeats=None if pres else 88 if year==2001 else 65
    if totalSeats is not None: assert sum(r['seats'] or 0 for r in results)==totalSeats
    turnout=cast/registered*100 if registered is not None else None
    ballot_note=f'Vote shares are calculated from {valid:,} valid '+('candidate' if pres else 'national-list')+' votes. '
    ballot_note+=f'{cast:,} ballots were cast; {cast-valid:,} ballots were outside the valid-vote denominator. '
    ballot_note+=(f'Turnout is ballots cast divided by {registered:,} registered voters.' if registered else 'A verified registration denominator is unavailable; turnout is left null.')
    system=('The president is elected directly by an absolute majority of valid votes. If no candidate obtains more than half, the two leading candidates contest a separate runoff; each round has its own denominator.' if pres else 'The 65 members of the National Parliament are elected directly by closed-list proportional representation in one nationwide constituency, using the d’Hondt allocation method. The threshold is '+('3%' if year<=2012 else '4%')+' of valid votes.')
    if not pres and year==2001: system='Under UN transitional administration, voters used separate ballots for 75 national proportional seats and 13 single-member district seats. The elected Constituent Assembly became the first National Parliament at independence in 2002.'
    e=dict(id=id,countryId='tl',title=('Presidential election · '+('Runoff' if round==2 else 'First round') if pres else 'Constituent Assembly election' if year==2001 else 'National Parliament election'+(' · Early election' if snap else '')),type='presidential' if pres else 'parliamentary',body='President of the Republic' if pres else 'Constituent Assembly' if year==2001 else 'National Parliament',startDate=date,endDate='',precision='day',dateStatus='confirmed',status='held',publication='published',round='Second round' if pres and round==2 else 'First round' if pres else 'General election',seriesId=f'tl-president-{year}' if pres else 'tl-national-parliament',snap=snap,summary=summary,government=government,turnout=turnout,totalSeats=totalSeats,majorityThreshold=None if pres else totalSeats//2+1,resultStatus='final',resultCoverage=coverage,voteBasis=f'Valid national {"candidate" if pres else "list"} votes ({valid:,}); '+('separate presidential round' if pres else 'seats as elected'),results=results,sources=sources,checked=CHECKED,notes=system+'\n\n'+ballot_note+'\n\n'+notes+'\n\nColours are editorial identifiers. No numeric ideology scores or unsupported election-era ideology links have been assigned.',articleId='',version=0,electionMethod='direct',linkedElectionIds=[])
    records.append(e);audits.append(dict(id=id,validVotes=valid,ballotsCast=cast,registeredVoters=registered,unenteredValidVotes=0,seatTotal=totalSeats,coverage=coverage))
    return e

def parliamentary(data, previous={}):
    return [row(k,v,s,previous=previous.get(k)) for k,v,s in data]

election('2001-08-30','assembly',1,363501,384248,None,parliamentary([
 ('fretilin',208531,55),('pd',31680,7),('psd',29726,6),('asdt',28495,6),('udt',8581,2),('pnt',8035,2),('kota',7735,2),('ppt',7322,2),('pdc',7181,2),('pst',6483,1),('pl2001',4013,1),('udcpdc',2413,1),('apodeti',2181,0),('pt',2026,0),('parentil',1970,0),('pdm',1788,0)
])+[row('independent',5341,0,name='Independent national-list candidates (aggregate)'),row('independent',None,1,name='António da Costa Lelan · Oecusse district')],[source('UNTAET / UN: final assembly result, 75 national seats and 13 district seats','https://reliefweb.int/report/timor-leste/untaet-daily-briefing-06-sep-2001-final-election-results-east-timor'),ifes(1320),wiki(2001,'parliamentary'),source('Contemporary transcription of IEC tables: national-list and district ballots','https://timor-online.blogspot.com/2006/08/resultados-das-eleies-de-2001_17.html')], 'FRETILIN won 55 of the 88 Constituent Assembly seats: 43 national-list seats and 12 district seats. An independent won Oecusse’s district seat.', 'The votes and shares in this table are from the national-list ballot only. Seats are the combined national and district outcome: FRETILIN 43 + 12; other parties national-list seats only; António da Costa Lelan one district seat with its vote count and share left null. The 5,341 independent national-list votes are retained as a source aggregate; they won no national-list seats. No district votes or percentages are added to the national denominator. Complete district candidate vote tables have not been verified, so coverage is partial.\n\nThe national figures follow the 363,501-valid / 384,248-cast series. The contemporary transcription reports PARENTIL 1,971 and totals 363,502 / 384,249 (one higher); this record uses 1,970, the table that reconciles to the IFES valid total. IFES has UDT 8,584 rather than 8,581, another conflicting transcription; no three votes are invented to balance that version. The exact registration denominator has not been resolved: later tables give 446,666 and 86.03%, while contemporary reports estimated around 93%; turnout remains null. Previous seats are null because there was no comparable prior national election.',coverage='partial')

p2007=[('fretilin',120592,21),('cnrt',100175,18),('asdtpsd',65358,11),('pd',46946,8),('pun',18896,3),('ad2007',13294,2),('undertim',13247,2),('pnt',10057,0),('pdrt',7718,0),('pr',4408,0),('pdc',4300,0),('pst',3982,0),('udt',3753,0),('pmd',2878,0)]
election('2007-06-30','parliament',1,415604,426210,529198,parliamentary(p2007),[EU2007,ipu(2007),wiki(2007,'parliamentary')], 'FRETILIN led the national vote and won 21 seats. CNRT won 18, the ASDT–PSD coalition 11 and the Democratic Party eight.', 'All 14 lists and all 65 seats are recorded. Joint lists ASDT–PSD and Democratic Alliance (KOTA–PPT) retain their combined votes and seats; no component vote split is inferred. Previous seats are null because the 2001 mixed 88-seat Constituent Assembly and the 2007 65-seat national PR chamber are not like-for-like contests.')

p2012=[('cnrt',172831,30),('fretilin',140786,25),('pd',48581,8),('fm',14648,2),('khunto',13998,0),('pst',11379,0),('psd',10158,0),('pdn',9386,0),('asdt',8487,0),('undertim',7041,0),('udt',5332,0),('pr',4270,0),('plpapdrt',4012,0),('apmt',3968,0),('pun',3191,0),('bp',3125,0),('ad2012',2622,0),('ptd',2561,0),('pdl',2222,0),('pdp',1904,0),('pdc',887,0)]
prev2007={k:s for k,v,s in p2007}
election('2012-07-07','parliament',1,471389,482792,645624,parliamentary(p2012,prev2007),[ipu(2012),ifes(1634),wiki(2012,'parliamentary'),UN2012], 'CNRT won 30 of 65 seats, followed by FRETILIN with 25, the Democratic Party with eight and Frenti-Mudança with two.', 'All 21 ballot lists and 65 seats are recorded. Coalitions PLPA–PDRT, Bloku Proklamador (PMD–PARENTIL) and Democratic Alliance (KOTA–PTT) retain the source grouping. The 2012 KOTA–PTT alliance is not the 2007 KOTA–PPT alliance. ASDT and PSD previous seats are null because they contested jointly in 2007. New lists and changed coalitions have null previous seats. The 2012 Liberal list is labelled Democratic Liberal Party (PDL), following IFES; the 2001 Liberal name is kept as a separate historical profile without assuming organizational continuity.')

p2017=[('fretilin',168480,23),('cnrt',167345,22),('plp',60098,8),('pd',55608,7),('khunto',36547,5),('pudd',15887,0),('udt',11255,0),('fm',8849,0),('fpatria',6775,0),('apmt',5461,0),('bup',4999,0),('pst',4891,0),('psd',4688,0),('pr',3951,0),('pdn',3846,0),('casdt',2330,0),('pdp',2079,0),('pdc',1764,0),('mlpm',1332,0),('undertim',1216,0),('ptd',669,0)]
election('2017-07-22','parliament',1,568070,583956,760907,parliamentary(p2017,{k:s for k,v,s in p2012}),[ipu(2017),ifes(3036),wiki(2017,'parliamentary')], 'FRETILIN won 23 seats, one more than CNRT. PLP entered with eight seats, the Democratic Party won seven and KHUNTO five.', 'All 21 ballot lists reconcile to 568,070 valid votes and 65 seats. Bloku Unidade Popular (PMD–PLPA–PDRT) remains a joint list. CASDT is not treated as the historical ASDT. The threshold rose from 3% in 2012 to 4%; previous-seat counts refer to unchanged parties in the preceding 65-seat national chamber. The old CNE apuramento/public.php link has been reused for 2022 presidential results and is therefore not used as a 2017 source.')

p2018=[('amp2018',309663,34),('fretilin',213324,23),('pd',50370,5),('fdd',34301,3),('fpatria',5060,0),('mdn',4494,0),('pr',4125,0),('msd',3188,0)]
election('2018-05-12','parliament',1,624525,635116,784286,parliamentary(p2018,{k:s for k,v,s in p2017}),[source('IPU: 2018 election and 65-seat outcome','https://data.ipu.org/parliament/TL/TL-LC01/election/TL-LC01-E20180512/'),ANFREL2023,wiki(2018,'parliamentary')], 'The Alliance for Change and Progress won an outright majority with 34 of 65 seats in the early parliamentary election.', 'All eight ballot lists are recorded. AMP combines CNRT–PLP–KHUNTO, FDD combines PUDD–UDT–FM–PDN, MDN combines APMT–PLPA–MLPM–UNDERTIM and MSD combines CASDT–PSD–PST–PDC. Coalition votes and seats are not allocated to constituent parties in this ballot table. The new alliances have null previous seats, rather than treating component totals as a previous election result for the same list. The 2018 AMP electoral alliance is distinct from the similarly abbreviated 2007 governing coalition. The CNE live endpoint has since been reused for 2022; the dated parliamentary archive and observation report preserve this election’s totals.',snap=True)

p2023=[('cnrt',288289,31),('fretilin',178338,19),('pd',64517,6),('khunto',52031,5),('plp',40720,4),('pvt',25106,0),('pudd',21647,0),('apmt',6678,0),('plpa',3272,0),('casdt',3170,0),('pst',2415,0),('pr',1558,0),('pdc',1262,0),('udt',1256,0),('undertim',1023,0),('mlpm',642,0),('pdn',597,0)]
election('2023-05-21','parliament',1,692521,705692,890145,parliamentary(p2023,{k:s for k,v,s in p2018}),[source('Tatoli: CNE national verification, all 17 party vote totals and ballot categories','https://id.tatoli.tl/2023/05/30/hasil-pilpar-2023-cne-berikan-waktu-48-jam-bagi-parpol-ajukan-pengajuan/'),source('IPU: 2023 result and government formation','https://data.ipu.org/parliament/TL/TL-LC01/election/TL-LC01-E20230521/'),ANFREL2023,wiki(2023,'parliamentary')], 'CNRT won 31 seats, followed by FRETILIN with 19. The Democratic Party won six, KHUNTO five and PLP four.', 'All 17 party rows reconcile exactly to 692,521 valid votes and all 65 seats. The Court of Appeal validated the result on 5 June 2023. Turnout uses the published ANFREL / result-table series: 705,692 ballots divided by 890,145 registered voters. Blank ballots: 2,698; other non-valid ballots: 10,473, totaling 13,171 excluded from valid-vote shares. Tatoli’s CNE report instead gives 705,693 participants, with 10,387 null, 61 rejected and 26 abandoned ballots; its categories plus valid and blank votes sum to 705,693. This one-ballot discrepancy between the participation series is unresolved, so coverage is marked partial despite complete party votes and seats.\n\nPrevious seats for parties that contested within AMP or FDD in 2018 are null: this record does not infer separate 2018 party vote results from coalition lists. Unchanged standalone parties use their 2018 seats.',coverage='partial',government='On 1 July 2023, Xanana Gusmão became prime minister with a government backed by CNRT and the Democratic Party (IPU). Together those parties held 37 of the 65 elected seats.')

def candidates(data,winners=(),advanced=()):
    return [row(k,v,name=n,winner=n in winners,advanced=n in advanced) for n,k,v in data]
election('2002-04-14','president',1,364780,378548,446256,candidates([('Xanana Gusmão','independent',301634),('Francisco Xavier do Amaral','asdt',63146)],winners=['Xanana Gusmão']),[ifes(1859),wiki(2002,'presidential')], 'Xanana Gusmão was elected president with 301,634 of 364,780 valid votes.', 'Both candidates are recorded. Gusmão stood as an independent; the later CNRT party is not backdated to this election. No second round was required.')
c2007=[('Francisco Guterres','fretilin',112666),('José Ramos-Horta','independent',88102),('Fernando de Araújo','pd',77459),('Francisco Xavier do Amaral','asdt',58125),('Lúcia Lobato','psd',35789),('Manuel Tilman','kota',16534),('Avelino Coelho da Silva','pst',8338),('João Viegas Carrascalão','udt',6928)]
election('2007-04-09','president',1,403941,427198,522933,candidates(c2007,advanced=['Francisco Guterres','José Ramos-Horta']),[EU2007,source('ANFREL: first-round final CNE table, p. 27','https://anfrel.org/wp-content/uploads/2012/02/2007_east_timor.pdf')], 'Francisco Guterres and José Ramos-Horta led the first round and advanced to a runoff; neither had an absolute majority.', 'All eight candidates are recorded. The CNE final table gives 7,723 blank and 15,534 invalid ballots. Some early reports cited 81.79% turnout; the reconciled final series is 427,198 divided by 522,933 (81.69%). No candidate is marked elected in this round.')
election('2007-05-09','president',2,413177,424475,524073,candidates([('José Ramos-Horta','independent',285835),('Francisco Guterres','fretilin',127342)],winners=['José Ramos-Horta']),[EU2007,ifes(2042)], 'José Ramos-Horta won the presidential runoff with 285,835 of 413,177 valid votes.', 'Both runoff candidates are recorded. The EU final annex reports 2,015 blank and 9,283 invalid ballots. The registration denominator changed between rounds; no first-round percentage is mixed into this table.')
c2012=[('Francisco Guterres','fretilin',133635),('Taur Matan Ruak','independent',119462),('José Ramos-Horta','independent',81231),('Fernando de Araújo','pd',80381),('Rogério Lobato','independent',16219),('José Luís Guterres','fm',9235),('Manuel Tilman','kota',7226),('Abílio Araújo','pnt',6294),('Lucas da Costa','independent',3862),('Francisco Gomes','plpa',3531),('Maria do Céu Lopes da Silva','independent',1843),('Angelita Pires','independent',1742)]
election('2012-03-17','president',1,464661,489933,626503,candidates(c2012,advanced=['Francisco Guterres','Taur Matan Ruak']),[UN2012,ifes(2227),wiki(2012,'presidential')], 'Francisco Guterres and Taur Matan Ruak advanced to the runoff. Incumbent José Ramos-Horta finished third.', 'All 12 active candidates are recorded. Francisco Xavier do Amaral died before polling and his candidacy was cancelled: he is not assigned zero votes or a result row. Blank votes: 6,484; null votes: 18,788. The court-certified first-round table in UNMIT gives 626,503 eligible voters and 78.20% turnout. IFES uses 627,295, the second-round registration total; this record follows the certified first-round denominator. The PLP party was established later and is not assigned to Taur Matan Ruak in 2012.')
election('2012-04-16','president',2,449879,458703,627295,candidates([('Taur Matan Ruak','independent',275471),('Francisco Guterres','fretilin',174408)],winners=['Taur Matan Ruak']),[UN2012,ifes(2231),wiki(2012,'presidential')], 'Taur Matan Ruak was elected president with 275,471 of 449,879 valid runoff votes.', 'Both candidates are recorded. The UNMIT court-certified page has an internal inconsistency: its small summary prints 275,441 and 174,386 (52 fewer combined), while its national total beneath the district table prints 275,471 and 174,408, totaling 449,879. This record follows the latter national totals, also reported by IFES, and calculates shares from 449,879; no missing ballots are converted to zeros. The header discrepancy remains documented. The independent label is election-era; PLP is not backdated.',coverage='partial')
c2017=[('Francisco Guterres','fretilin',295048),('António da Conceição','pd',167794),('José Luís Guterres','fm',13513),('José Neves','independent',11663),('Luís Alves Tilman','independent',11125),('Antonio Maher Lopes','pst',9102),('Ángela Freitas','pt',4353),('Amorim Vieira','independent',4283)]
election('2017-03-20','president',1,516881,528813,743150,candidates(c2017,winners=['Francisco Guterres']),[ifes(2552),wiki(2017,'presidential'),source('La’o Hamutuk: 2017 presidential election documentation and results','https://www.laohamutuk.org/Justice/2017/PresElec/17PresElec.htm')], 'Francisco Guterres won an absolute majority in the first round, so no presidential runoff was held.', 'All eight candidates are recorded, including candidates below IFES’s published 2% cutoff. The complete CNE-derived table supplies the smaller candidates. IFES labels the 11,125-vote candidate Manuel Tilman; the election-specific complete table identifies Luís Alves Tilman. This record uses Luís Alves Tilman and does not conflate him with the 2007 and 2012 candidate Manuel Tilman. Null, blank and rejected ballots are excluded from the 516,881-valid-vote denominator.')
c2022=[('José Ramos-Horta','cnrt',303477),('Francisco Guterres','fretilin',144282),('Armanda Berta dos Santos','khunto',56690),('Lere Anan Timur (Tito da Costa Cristóvão)','independent',49314),('Mariano Sabino Lopes','pd',47334),('Anacleto Bento Ferreira','pdrt',13205),('Martinho Germano da Silva Gusmão','pudd',8598),('Hermes da Rosa Correia Barros','independent',8030),('Milena Pires (Maria Helena Lopes de Jesus Pires)','independent',5430),('Isabel da Costa Ferreira','independent',4219),('Felisberto Araújo Duarte','independent',2709),('Constâncio da Conceição Pinto','independent',2520),('Rogério Lobato','independent',2058),('Virgílio da Silva Guterres','independent',1720),('Antero Benedito Silva','independent',1562),('Ángela Freitas','independent',711)]
CNE1=source('CNE: 2022 first-round national tabulation, all candidates and ballot categories','https://www.cne.tl/apuramento/public.html')
CNE2=source('CNE: 2022 runoff national tabulation, candidates and ballot categories','https://www.cne.tl/apuramento2022r2/public.html')
election('2022-03-19','president',1,651859,664106,859613,candidates(c2022,advanced=['José Ramos-Horta','Francisco Guterres']),[CNE1,source('Official Gazette: Court of Appeal final first-round judgment, 29 March 2022','https://mj.gov.tl/jornal/public/docs/2022/serie_1/SERIE_I_NO_13_C.pdf'),source('Tatoli: Court of Appeal advances the two leading candidates, final result','https://tatoli.tl/2022/03/29/tribunal-rekursu-deside-kandidatu-horta-no-lu-olo-hakat-ba-segunda-volta/'),wiki(2022,'presidential')], 'José Ramos-Horta and incumbent Francisco Guterres advanced to the presidential runoff; no candidate won a first-round majority.', 'All 16 candidates reconcile to 651,859 valid votes. The CNE live page retains a provisional heading; final status here rests on the Court of Appeal judgment of 29 March and the corresponding Tatoli report. Blank: 3,743; null: 8,386; rejected: 65; abandoned: 53. These categories plus valid votes reconcile to 664,106 participants. Party labels identify election-era candidacies or support, not automatic ideology. Ramos-Horta was the CNRT-supported candidate; Lere Anan Timur contested separately from FRETILIN’s nominee, and Ángela Freitas is recorded as an independent in this election.')
election('2022-04-19','president',2,640967,646389,859925,candidates([('José Ramos-Horta','cnrt',398028),('Francisco Guterres','fretilin',242939)],winners=['José Ramos-Horta']),[CNE2,source('Tatoli: Court of Appeal certifies Ramos-Horta elected, 29 April 2022','https://en.tatoli.tl/2022/04/29/court-of-appeal-officially-announces-horta-as-elected-president-of-tl/15/'),source('Tatoli: CNE final verification and revisions to preliminary candidate totals','https://en.tatoli.tl/2022/04/24/cne-concludes-final-tabulation-of-ballots-cast-in-presidential-election/09/')], 'José Ramos-Horta won the presidential runoff with 398,028 votes to Francisco Guterres’s 242,939.', 'Both candidates reconcile to 640,967 valid votes. Final status rests on court certification on 29 April, not the CNE web page’s retained provisional heading. CNE verification added 883 valid votes to Ramos-Horta and 499 to Guterres compared with STAE’s preliminary 397,145 / 242,440 totals. Blank: 1,643; null: 3,734; rejected: 28; abandoned: 17. Together with valid votes these reconcile to 646,389 participants. Registration changed to 859,925; shares and turnout use this round’s own denominators.')

records.sort(key=lambda e:e['startDate'])
records[0]['results'][-1]['winner']=True
for e in records:
    if e['type']=='presidential': e['linkedElectionIds']=[x['id'] for x in records if x['seriesId']==e['seriesId'] and x['id']!=e['id']]
    if e['startDate'].startswith('2007'):
        for r in e['results']:
            if r.get('partyId')==party_id('pst'):
                r['ideologyIds']=['ideology-marxism-leninism']
                r['ideologyBasis']=dict(kind='party-era',year=2007,note='Election-era party fallback: ANFREL’s 2007 report describes PST as developed on Marxist-Leninist principles. This assesses the party tradition in that election year; it is not an independently established personal classification of Avelino Coelho da Silva.',sources=[source('ANFREL 2007 mission report: PST principles and its presidential candidate, p. 7','https://anfrel.org/wp-content/uploads/2012/02/2007_east_timor.pdf')])
                if not any(s['url']=='https://anfrel.org/wp-content/uploads/2012/02/2007_east_timor.pdf' for s in e['sources']): e['sources'].append(source('ANFREL 2007: election-era PST classification','https://anfrel.org/wp-content/uploads/2012/02/2007_east_timor.pdf'))
profiles=[]
for k in sorted(used):
    name,short,color=PARTIES[k]
    profiles.append(dict(id=party_id(k),country_id='tl',name=name,short_name=short,color=color,ideology_ids=[],notes='Historical ballot identity in the reviewed Timor-Leste election records. Colour is an editorial identifier; no election-era ideology classification is inferred. '+('This alliance is kept distinct from other alliances or governing coalitions with similar names.' if k in ['amp2018','ad2007','ad2012','asdtpsd','plpapdrt','bp','bup','fdd','mdn','msd'] else '')+(' Historical Liberal ballot names are kept separate because continuity has not been assessed.' if k in ['pl2001','pdl'] else '')+(' CASDT and ASDT have distinct profiles.' if k in ['casdt','asdt'] else ''),archived=False))
    examples=[e for e in records if any(r.get('partyId')==party_id(k) for r in e['results'])]
    profiles[-1]['notes']+=' Election records: '+', '.join(e['startDate'] for e in examples)+'. Sources: '+examples[0]['sources'][0]['url']
assert len(records)==14 and len({e['id'] for e in records})==14
for name,content in [('timor-leste-election-records.json',records),('timor-leste-party-profiles.json',profiles),('timor-leste-election-audit.json',audits)]:
    (ROOT/name).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
print(f'Generated {len(records)} elections, {sum(len(e["results"]) for e in records)} result rows and {len(profiles)} party/list profiles.')
