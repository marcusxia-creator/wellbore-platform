/**
 * API router — set NEXT_PUBLIC_USE_MOCK=true in .env.local to use mock data
 * without a running Django backend. Flip it to false (or remove it) to
 * switch back to the real Axios-based implementation.
 *
 * Both implementations export identical signatures, so nothing else in the
 * codebase needs to change.
 */
import * as mock from "./mock-api";
import * as real from "./real-api";

const impl = process.env.NEXT_PUBLIC_USE_MOCK === "true" ? mock : real;

export const fetchWells               = impl.fetchWells;
export const fetchWell                = impl.fetchWell;
export const fetchWellFilterOptions   = impl.fetchWellFilterOptions;
export const fetchSections            = impl.fetchSections;
export const fetchSubstations         = impl.fetchSubstations;
export const fetchSubstation          = impl.fetchSubstation;
export const fetchSubstationFilterOptions = impl.fetchSubstationFilterOptions;
export const fetchNearbyWells         = impl.fetchNearbyWells;
export const fetchBestPoint           = impl.fetchBestPoint;
export const fetchWellRankings        = impl.fetchWellRankings;
export const fetchSubstationRankings  = impl.fetchSubstationRankings;
export const fetchSubstationCandidates = impl.fetchSubstationCandidates;
