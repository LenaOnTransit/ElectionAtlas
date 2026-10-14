import GeographyLoader from '../geography/loader';

// Existing ?year= links remain usable; comparison links may name an earlier year.
export default function MunicipalComparison(){
 const params=new URLSearchParams(window.location.search);
 return <GeographyLoader asset="nl-municipal-history.json" title="Netherlands Tweede Kamer municipal results 2003–2025" initialElectionId={params.get('year')||undefined} initialComparisonId={params.get('compare')||undefined}/>;
}
