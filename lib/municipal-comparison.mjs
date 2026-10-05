// Compatibility exports for the Dutch import audit; calculations live in the engine.
export {rankedResults,winningMargin,blocShares,populationRadius,mixWhite} from './election-geography.mjs';
import {voteShift} from './election-geography.mjs';
export function municipalShift(before,after,classifications){return voteShift(before,after,classifications);}
