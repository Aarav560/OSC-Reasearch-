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

## Zephyr Mk1-A controller: what broke and why (all fixed, `paper-tests/zephyr.py`)
- **Dust feedback through a diagonal step.** Stage dust one block above and one block over from
  the delay-line dust connects to it. Every stage pulse fed back into the line, and observer +
  line became a 12-tick clock that fired the stager right through the launch. Use a repeater
  wherever two lines pass diagonally.
- **Quasi-connectivity through the X launcher.** A repeater (or dust) into the X dispenser makes
  it a powered block, and that block touches the space above the stager piston. The piston
  then counts as powered, but only reacts when something else updates it, so it looked
  random: in live runs it extended on the next feed edge and held its head in the W cell for
  the whole launch pulse, and every X charge burst on the head (X motion 0, Z normal). Fix:
  fire the X launcher through *its own* quasi-connectivity, with dust pointing into the air
  above it, so the dispenser itself is never a powered block.
- **Strong power leaking from staircase supports.** Dust strongly powers the block it sits on.
  A concrete support under the launch staircase sat next to stage dust and fed it. Supports
  next to other circuitry are glass.
- **Dust on glass passes signal up a step, never down one.** Step-down supports have to be solid.
- **Repeater delay counts redstone ticks.** `delay=4` = 8 game ticks. A comparator ignores 2-gt
  pulses, and a copper bulb's `powered` flag flips on both edges, so an observer watching a bulb
  fires twice per toggle. Watch a comparator that reads the bulb to get one pulse per toggle.
- **The delay chain needs ~50 game ticks to settle** after loading. Arming earlier lets one launch
  pulse through.

## Zephyr Mk1-A: per-feed staging, equal fuses
- With enchanting-table floors a dispensed TNT takes 4 ticks to land (0.25 drop). It needs 8
  ticks after the feed edge, but the next TNT arrives 12 ticks after the last, so staging
  everything once at the end of feeding was the only option. That left fuses spread by 12 per
  TNT ([3, 15, 27, 39] for 4) and capped the payload near 4.
- Full-block floors under S, W and N raise payload and bursts by the same 0.25, so the
  burst-to-payload geometry is unchanged. A dispensed TNT then lands in 2 ticks (the X launcher
  above caps the 0.2 hop). The stager pushes each TNT 6 game ticks after its feed edge and is
  clear before the next one.
- Result (8 TNT, 100 X + 100 Z charges, real time): all 8 staged, every fuse 75. Motion
  (67.379, -34.005, 67.253) against the core calibration (66.83, -34.1, 66.9). Spread
  sd 0.003 / 0.18 / 0.16 b/t, so after the 0.9x brake the landing spread is about 0.15 blocks.
  (`paper-tests/mk1a-test-8x100.json`)
