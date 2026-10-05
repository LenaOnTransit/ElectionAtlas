import GeographyLoader from '../geography/loader';
import {netherlandsGeography} from '../../lib/netherlands-geography.mjs';

// Preserve the existing route and ?year= links; all map behaviour is shared.
export default function MunicipalComparison(){
 return <GeographyLoader asset="nl-municipal-2023-2025.json" title="Netherlands municipal results" adapt={netherlandsGeography} initialElectionId={new URLSearchParams(window.location.search).get('year')||undefined}/>;
}
