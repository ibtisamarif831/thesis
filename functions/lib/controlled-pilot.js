import { fail, token } from './pilot.js';
// Equal-weight scalar z-scores plus axial orientation distance. Stable ID breaks ties.
export const SELECTION_RULE = 'near-distinct-band-12-16-sha256-v1';
export const SCHEDULE_RULE = 'balanced-target-positions-v1';
export async function sampleIndex(seed, targetId, count) {
  if (!Number.isInteger(count) || count < 1 || count > 0x100000000) fail('Invalid sample count.');
  const limit = Math.floor(0x100000000 / count) * count;
  for (let counter = 0; ; counter++) {
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify([SELECTION_RULE, seed, targetId, counter])));
    const value = new DataView(bytes).getUint32(0, false);
    if (value < limit) return value % count;
  }
}
export function validateImageChecks(icons, spec) {
  const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  if (spec?.version !== 'white-rgb-lanczos-v1' || JSON.stringify(spec.source_size) !== '[256,256]' || JSON.stringify(spec.sizes) !== '[6,8,10,12,14]' || typeof spec.pillow_version !== 'string' || !spec.pillow_version || typeof spec.rendering !== 'string' || !spec.rendering || icons.some(i => !hex(i.image_checks?.source_sha256) || spec.sizes.some(size => !hex(i.image_checks?.size_sha256?.[size])))) fail('Valid image-check metadata required for every selected icon.', 503);
}
export async function selectAlternatives(icons, featureIds, imageCheckSpec, seed = token()) {
  if (!Array.isArray(icons) || icons.length !== 20 || new Set(icons.map(i => i.icon_id)).size !== 20) fail('Exactly 20 unique pool icons required.');
  validateImageChecks(icons, imageCheckSpec);
  if (!/^[a-f0-9]{64}$/.test(seed)) fail('Invalid selection seed.');
  if (!Array.isArray(featureIds) || featureIds.length !== 7 || new Set(featureIds).size !== 7) fail('Seven-feature catalog required.', 503);
  const vectors = icons.map(icon => featureIds.map(id => icon.features?.[id]));
  if (vectors.some(v => v.some(x => typeof x !== 'number' || !Number.isFinite(x)))) fail('Finite feature values required for every selected icon.', 503);
  const means = featureIds.map((_,j) => vectors.reduce((sum,v) => sum + v[j],0)/vectors.length);
  const scales = means.map((mean,j) => featureIds[j] === 'principal_axis_orientation_v2' ? 90 : Math.sqrt(vectors.reduce((sum,v) => sum + (v[j]-mean)**2,0)/vectors.length) || 1);
  const alternatives = {};
  const errors = [], collision_diagnostics = [];
  for (const [i, icon] of icons.entries()) {
    const ranked = icons.map((other,k) => ({id:other.icon_id, distance:Math.sqrt(vectors[i].reduce((sum,x,j) => sum + (featureIds[j] === 'principal_axis_orientation_v2' ? Math.min(Math.abs(x-vectors[k][j]) % 180, 180-Math.abs(x-vectors[k][j]) % 180) / 90 : (x-vectors[k][j])/scales[j])**2,0))}))
      .filter(other => other.id !== icon.icon_id).sort((a,b) => a.distance-b.distance || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
    ranked.forEach((entry, index) => { entry.rank = index + 1; });
    const byId = new Map(icons.map(x => [x.icon_id, x]));
    const seen = new Set([icon.image_checks.source_sha256]), near = [];
    for (const candidate of ranked) {
      const digest = byId.get(candidate.id).image_checks.source_sha256;
      if (!seen.has(digest)) { near.push(candidate); seen.add(digest); }
      if (near.length === 2) break;
    }
    const band = ranked.filter(x => x.rank >= 12 && x.rank <= 16);
    const combinations = [];
    for (let a = 0; a < band.length; a++) for (let b = a + 1; b < band.length; b++) {
      const ha = byId.get(band[a].id).image_checks.source_sha256, hb = byId.get(band[b].id).image_checks.source_sha256;
      if (!seen.has(ha) && !seen.has(hb) && ha !== hb) combinations.push([band[a], band[b]]);
    }
    if (near.length !== 2 || !combinations.length) { errors.push(`${icon.icon_id}: ${near.length !== 2 ? 'insufficient source-distinct near alternatives' : 'no source-distinct pair in original ranks 12–16'}`); continue; }
    const distant = combinations[await sampleIndex(seed, icon.icon_id, combinations.length)];
    alternatives[icon.icon_id] = {
      similar: near.map(x => x.id), dissimilar: distant.map(x => x.id), ranked,
      selected_ranks: {similar: near.map(x => x.rank), dissimilar: distant.map(x => x.rank)},
      valid_combination_count: combinations.length,
      diagnostics: {distance_ties: ranked.slice(1).filter((x,j) => x.distance === ranked[j].distance).map(x => x.rank), near_distant_overlap: Math.max(...near.map(x => x.distance)) >= Math.min(...distant.map(x => x.distance))},
    };
    const options = [icon.icon_id, ...near.map(x => x.id), ...distant.map(x => x.id)];
    for (const size of imageCheckSpec.sizes) for (let a = 0; a < 5; a++) for (let b = a + 1; b < 5; b++) {
      if (byId.get(options[a]).image_checks.size_sha256[size] === byId.get(options[b]).image_checks.size_sha256[size]) collision_diagnostics.push({target_id: icon.icon_id, size, icon_pair: [options[a], options[b]], target_involved: a === 0});
    }
  }
  if (errors.length) fail('Alternative selection failed: ' + errors.join('; '));
  return {alternatives, selection_rule_version: SELECTION_RULE, schedule_rule_version: SCHEDULE_RULE, selection_seed: seed, image_check_spec: imageCheckSpec, image_hashes: Object.fromEntries(icons.map(i => [i.icon_id, i.image_checks])), collision_diagnostics, collision_label: "standardized rendering collision diagnostics", distance_spec:{method:'equal-weight Euclidean with standardized scalars and axial orientation', normalization:'scalar population standard deviation within frozen 20-icon pool; constant scalars use scale 1; axial angle uses shortest modulo-180 difference divided by 90', feature_ids:featureIds, means, scales, selection:'two nearest source-distinct options; uniform valid pair from original ranks 12–16; stable icon ID breaks ties; no absolute cutoff', interpretation:'implementation choice, not a transcript requirement or validated perceptual measure', random_stream:'SHA-256 UTF-8 JSON [selection rule version, seed, target ID, counter starting at 0]; first big-endian uint32; rejection sampling'}};
}
