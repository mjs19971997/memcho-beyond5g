// Decimal rounding for every number printed in the papers and letters.
// Number.prototype.toFixed rounds the binary value of a double.  A rate that is exactly halfway in decimal
// (468 failures in 4800 UE-minutes = 0.0975) is stored as 0.09749999999999999 or 0.09750000000000002 depending
// on how it was summed, and would print as 0.097 or 0.098 by accident.  rfix rounds half away from zero in
// decimal: the nudge of 1e-5 of the last printed digit is far above the noise of the stored values (below 1e-8
// of a unit of that digit would already do for sums of doubles; rates read from 8-digit CSV fields need about
// 1e-6) and far below the distance of any count ratio that is not an exact tie.
const rfix = (x, d = 2) => {
  const m = Math.pow(10, d);
  const r = Math.round(Math.abs(Number(x)) * m + 1e-5) / m;
  return (Number(x) < 0 ? '-' : '') + r.toFixed(d);
};
module.exports = { rfix };
