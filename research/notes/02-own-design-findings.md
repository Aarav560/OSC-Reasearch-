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

## Zephyr Mk1-A live fire (`paper-tests/mk1a_livefire.py`, `livefire-8x150x120.json`)
- Cannon at S = (56000, -10, 56000) in a superflat world. The W, N and NW chunks are
  force-loaded and the payload chunk stays lazy. Charging runs in real time, fully automatic:
  8 TNT staged in 5.9 s, then 150 X + 120 Z charges in 90 s.
- Frozen payload: motion (101.35, -45.49, 81.60) b/t, every fuse 75. The prediction from the
  8x100 calibration was (101.07, -45.9, 80.70).
- Release (force-load the payload chunk): Y moves first and is blocked by the cell floor, so
  the payload goes 0.9·v in X then Z within one tick (117 blocks straight-line) and stops dead
  in the powder snow. It then falls 40 blocks and detonates at tick 75 on the target.
- Stop point (56091.72, 56073.95) against the predicted (56091.46, 56073.13): a 0.85-block miss.
  Crater in a 10-high stone block: 311 blocks, 5 deep, centroid within 0.6 blocks of the stop.
- For aiming, the cannon height only has to keep the fall inside the fuse (~70 blocks max at
  fuse 75); the vertical component of the charges is wasted on the floor.

## Zephyr Mk2: compact (`zephyr.py: mk2_layout`, 102 blocks, 8x4x13)
- Same core, stager and launcher drive as Mk1-A, so the same calibration. No base slab and no
  arming plate. The clock is a 4-block column behind the feeder, and the launch is held by
  *locking* one repeater (RL) while the feeder still holds TNT: the feeder comparator's
  boosted signal points into RL's side. No inverter and no 50-tick delay chain. Load TNT
  first, then the wind charges.
- 64 TNT x 100+100 charges: all 64 staged, every fuse 75, motion (67.59, -33.94, 67.95),
  sd 0.006 / 0.26 / 0.23.
- Live fire, 64 TNT x 150/120 (`livefire-mk2-64x150x120.json`): stop 0.79 blocks from the
  prediction. Crater 650 blocks, 6 deep: 2.1x Mk1-A's 8-TNT shot for 8x the TNT.

## Payload timing matters more than payload size (`payload_drill_test.py`)
TNT stacked exactly on one spot of a 31x31x20 stone block (fuse 20 + k*stagger):

| payload | destroyed | depth |
|---|---|---|
| 8 equal | 236 | 5 |
| 64 equal | 251-357 | 5-6 |
| 10 @ 4 t | 385 | 10 |
| 12 @ 4 t | 471 | 12 |
| 16 @ 4 t | 647 | 16 |
| 20 @ 4 t | 825 | 19 |
| 64 @ 1 t | 1015-1441 | 20+ (to bedrock) |

Explosions at one point in one tick mostly overlap. Staggered fuses drill: each TNT falls into
the last one's hole, roughly one block deeper per TNT. A dispenser fires at most every 4 ticks
and a fuse is at most 80, so a single-feeder drill holds about 12-16 TNT.

## Zephyr Mk3 "Drill" (`zephyr.py: mk3_layout`, 106 blocks) - works, drill underperforms
- Mk2 with a 4-tick two-repeater ring clock. TNT collects in the W cell and is pushed in all
  at once when the feeder runs empty (an observer on the feeder comparator), so the fuses come
  out 4 ticks apart (37..73). It launches twice as fast as Mk2.
- Live fire, 12 TNT (`livefire-mk3-12x150x120.json`): stop 0.55 blocks from the prediction,
  but only 377 blocks / 6 deep against 471 / 12 deep for the same payload stacked exactly.
- Why: the payload has to be *exactly* co-located to drill. In the W channel each TNT sits
  0.01 against one wall or the other (z 0.49 or 0.51). The Z charges turn that into a 0.6%
  velocity difference, about 0.45 blocks at the target. Spread TNT throw each other sideways
  instead of falling into the hole (one landed 4 blocks off). One TNT pushed mid-hop by the
  stager's first pulse also ends up 0.7 off. Mk2 doesn't care, since its whole payload
  detonates at once.
- Next: centre the TNT in Z before staging (bias the dispense drift to one wall, or a second
  push along Z), and stop the first stager pulse from firing during the load.
