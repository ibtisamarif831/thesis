import { fail } from './pilot.js';
// Equal-weight scalar z-scores plus axial orientation distance. Stable ID breaks ties.
export function selectAlternatives(icons, featureIds) {
  if (!Array.isArray(featureIds) || featureIds.length !== 7 || new Set(featureIds).size !== 7) fail('Seven-feature catalog required.', 503);
  const vectors = icons.map(icon => featureIds.map(id => icon.features?.[id]));
  if (vectors.some(v => v.some(x => typeof x !== 'number' || !Number.isFinite(x)))) fail('Finite feature values required for every selected icon.', 503);
  const means = featureIds.map((_,j) => vectors.reduce((sum,v) => sum + v[j],0)/vectors.length);
  const scales = means.map((mean,j) => featureIds[j] === 'principal_axis_orientation_v2' ? 90 : Math.sqrt(vectors.reduce((sum,v) => sum + (v[j]-mean)**2,0)/vectors.length) || 1);
  const alternatives = {};
  icons.forEach((icon,i) => {
    const ranked = icons.map((other,k) => ({id:other.icon_id, distance:Math.sqrt(vectors[i].reduce((sum,x,j) => sum + (featureIds[j] === 'principal_axis_orientation_v2' ? Math.min(Math.abs(x-vectors[k][j]) % 180, 180-Math.abs(x-vectors[k][j]) % 180) / 90 : (x-vectors[k][j])/scales[j])**2,0))}))
      .filter(other => other.id !== icon.icon_id).sort((a,b) => a.distance-b.distance || a.id.localeCompare(b.id));
    alternatives[icon.icon_id] = {similar:ranked.slice(0,2).map(x=>x.id), dissimilar:ranked.slice(-2).map(x=>x.id), ranked};
  });
  return {alternatives, distance_spec:{method:'equal-weight Euclidean with standardized scalars and axial orientation', normalization:'scalar population standard deviation within frozen 20-icon pool; constant scalars use scale 1; axial angle uses shortest modulo-180 difference divided by 90', feature_ids:featureIds, means, scales, selection:'two nearest and two farthest; stable icon ID breaks ties; no absolute cutoff'}};
}
