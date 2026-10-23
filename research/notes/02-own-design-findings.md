# Findings that shape my own designs (all measured on Paper 26.3 build 214, cross-checked on vanilla 26.3)

## Powder-snow brake arming
- A payload that merely *starts* inside powder snow (e.g. TNT dispensed into the snow inside a
  lazy chunk) is NOT braked on 26.3 — identical trajectory to a control without snow,
  on Paper and on vanilla. (TheeDumbRock's MOSC relies on this and overshoots on 26.3.)
- The brake arms only when the entity *moves into* the snow during a tick in which it is
  processed. The armed state persists while the entity is frozen in a lazy chunk.
- "Border-drift arming": put the powder snow in the first block column of the lazy chunk and
  let the payload drift across the chunk border into it (0.3 b/t is plenty). It arms and
  freezes in the same tick. On release it moves exactly 0.9·vx, 1.5·vy, 0.9·vz and stops dead.
  Paper and vanilla give bit-identical results (49616.19 -> 49680.218 for v=71.142).

## MOSC (TheeDumbRock, 16 blocks) on Paper 26.3
- Charges correctly: 64 TNT stack in the snow with fuse frozen at 80; observer clock dispenses
  all TNT, comparator switches to wind charges.
- 181 X + 137 Z wind charges -> payload motion (-118.19, -59.66, -91.87): ~0.65 b/t per charge
  horizontally plus a large downward component (burst above payload centre). The downward part
  is cancelled by the dispenser under the snow (Y moves first and collides).
- On release the payload moved the full velocity (no 0.9 factor) and kept going with 0.686 of its
  speed: no brake on 26.3 (see above).

## Strict pasting
- `setblock ... strict` reproduces schematics exactly but leaves mid-pulse components (observer
  pairs, pistons whose power changed) without their scheduled ticks; a single real block update
  restarts them. Lever flips must be emulated by remove+place to propagate.
