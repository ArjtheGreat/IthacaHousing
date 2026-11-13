/** Curated renter-facing filters, shared with listing detail display. */
export interface AmenityOption { key: string; label: string; category: string; aliases: string[] }
export const AMENITY_OPTIONS: AmenityOption[] = [
  {key:'furnished',label:'Furnished',category:'Unit features',aliases:['Furnished']},
  {key:'air_conditioning',label:'Air Conditioning',category:'Unit features',aliases:['Air Conditioning','Central Air Conditioning','Central Heat and Air Conditioning']},
  {key:'in_unit_laundry',label:'In-Unit Washer & Dryer',category:'Unit features',aliases:['Washer & Dryer','washer and dryer in unit']},
  {key:'dishwasher',label:'Dishwasher',category:'Unit features',aliases:['Dishwasher']},
  {key:'private_bathroom',label:'Private Bathroom',category:'Unit features',aliases:['Private Bathrooms']},
  {key:'private_outdoor',label:'Private Balcony / Patio',category:'Unit features',aliases:['Private Balcony','Private Patio']},
  {key:'keyless_entry',label:'Keyless Entry',category:'Unit features',aliases:['Keyless Entry','Electronic Key System']},
  {key:'fitness_center',label:'Fitness Center',category:'Building amenities',aliases:['Fitness Center','24 hour Fitness Center']},
  {key:'study_room',label:'Study Room / Lounge',category:'Building amenities',aliases:['Study Room','Study Lounge','Group Study']},
  {key:'rooftop',label:'Rooftop Terrace',category:'Building amenities',aliases:['Rooftop Terrace','Rooftop Tanning Deck']},
  {key:'pool',label:'Swimming Pool',category:'Building amenities',aliases:['Swimming Pool']},
  {key:'elevator',label:'Elevator',category:'Building amenities',aliases:['Elevator']},
  {key:'bike_storage',label:'Bike Storage',category:'Building amenities',aliases:['Bike Storage','Bike Storage Room','Bike Room','Bike Racks']},
  {key:'parking',label:'Parking Available',category:'Building amenities',aliases:['Parking Available']},
  {key:'packages',label:'Package Room',category:'Building amenities',aliases:['Package Room','Package Lockers']},
  {key:'internet_included',label:'Internet Included',category:'Utilities & services',aliases:['Internet Included','WiFi Included','WIFI Included']},
  {key:'heat_included',label:'Heat Included',category:'Utilities & services',aliases:['Heat Included']},
  {key:'electricity_included',label:'Electricity Included',category:'Utilities & services',aliases:['Electricity Included','Electric Included']},
  {key:'water_included',label:'Water Included',category:'Utilities & services',aliases:['Water Included','Water & Sewer Included']},
  {key:'shared_laundry',label:'On-Site Laundry',category:'Utilities & services',aliases:['Laundry On-Site','On-Site Laundry','Laundry Room']},
  {key:'cats',label:'Cats Allowed',category:'Pets & accessibility',aliases:['Cats']},
  {key:'dogs',label:'Dogs Allowed',category:'Pets & accessibility',aliases:['Dogs']},
  {key:'ada',label:'ADA Accessible',category:'Pets & accessibility',aliases:['ADA Accessible']},
];
export const AMENITY_CATEGORIES = [...new Set(AMENITY_OPTIONS.map(item=>item.category))];
export function rawAmenityLabels(raw: unknown): string[] {
  if (Array.isArray(raw)) return raw.filter((x): x is string=>typeof x==='string');
  if (typeof raw!=='string') return [];
  try { const parsed:unknown = JSON.parse(raw); return Array.isArray(parsed)?parsed.filter((x):x is string=>typeof x==='string'):[]; }
  catch { return []; }
}
const norm = (v:string)=>v.trim().replace(/\s+/g,' ').toLowerCase();
export function matchesAmenityKeys(raw:unknown, keys:readonly string[]):boolean {
  if (!keys.length) return true;
  const labels = new Set(rawAmenityLabels(raw).map(norm));
  return keys.every(key=>{
    const option=AMENITY_OPTIONS.find(item=>item.key===key);
    return !!option && option.aliases.some(a=>labels.has(norm(a)));
  });
}
// The source stores lease terms, property types, eligibility and location as
// amenities. Never render these as building features.
const NOT_AMENITIES = /^(?:\d+-month|academic.*|semester|summer housing|temporary|flexible|conventional leasing|per person leasing|rent by the bed|individual leases.*|apartment|suite|suite-style dorm|single|double|private|large|small|community|graduate students|undergraduates|facultystaff|family housing|close to downtown|walking distance to class|on bus line)$/i;
const GROUPS: Array<[string,RegExp]> = [
  ['Kitchen & interior',/kitchen|appliance|countertop|cabinet|refrigerator|microwave|oven|dishwasher|stove|floor|closet|ceiling|window|pantry|backsplash|bedroom|bathroom|furnish|heating|air conditioning|fireplace|laundry|washer|dryer|sink/i],
  ['Building & recreation',/fitness|gym|study|lounge|sauna|game|billiards|pool|yoga|clubhouse|coffee bar|business center|conference|computer lab|resident|wellness/i],
  ['Outdoor spaces',/roof|yard|porch|patio|balcony|deck|courtyard|grill|terrace|park|trail|outdoor|gazebo|fire pit/i],
  ['Security & services',/security|access|intercom|alarm|keyless|maintenance|management|concierge|package|mailroom|storage|smok|pest control|recycling/i],
  ['Transportation',/bike|parking|shuttle|charging station|bus line/i],
];
export function groupedAdvertisedAmenities(raw:unknown): Array<{category:string;amenities:string[]}> {
  const groups = new Map<string,string[]>();
  const seen=new Set<string>();
  for (const original of rawAmenityLabels(raw)) {
    const label=original.trim(), key=norm(label);
    if (!key||seen.has(key)||NOT_AMENITIES.test(label)) continue;
    seen.add(key);
    const category=GROUPS.find(([,regex])=>regex.test(label))?.[0]??'Other details';
    if (!groups.has(category)) groups.set(category,[]);
    groups.get(category)!.push(label);
  }
  return [...groups].map(([category,amenities])=>({category,amenities}));
}
