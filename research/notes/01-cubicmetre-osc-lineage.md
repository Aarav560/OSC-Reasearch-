# cubicmetre OSC lineage — study notes

## Mk.1 "Introducing the Orbital Strike TnT Cannon" (s_TKe16WASY)
- Principle: two nether-portal chunk-loading areas (3x3 entity-processing, ring of lazy chunks)
  intersect; payload sits in stasis in the lazy intersection, hit from 4 sides by linear
  combinations of propellant TNT -> exact velocity -> flies to target in one tick.
- Two variants: anvil payload and TNT "bunker buster" (stab charge).
- Fire control: Excel sheet. Origin = red nether brick stair. Settings per axis: facing
  (N/S/E/W), "count" (items moved between droppers = number of full batches), "coarse
  adjustment" (lectern turn, bottom) and "fine adjustment" (lectern turn, top). Fine 0 is
  unreachable -> flick lever.
- Cannon refuses to fire until it is ONLY loaded by its portals (cannot hit targets inside
  render distance). Player waits in the nether / spectator with spectatorsGenerateChunks=false.
- Log-out trap: payload parked over target in unloaded chunks detonates when chunk loads.
- Range ~45,000 blocks at full load; >2,000 blocks crashed the singleplayer client;
  cubicmetre used carpet `optimizeFastEntityMovement` and `optimizedTNT`.

## "The Incredible Science" (HscY70qjSU4)
- Lazy acceleration: motion applied to entity in lazy chunk is cumulative; released when loaded.
- Intersection of two entity-processing + two lazy regions -> full directional control.
- Payload alignment: center slightly inside lazy chunk; propellant slightly inside
  entity-processing chunk; propellant on a "stair channel", toggled lazy<->processing by tiny
  nudges -> controls *when* propellant explodes. Gates drop and centre is loaded to release.
- Entity movement order at high speed: Y, then larger of X/Z (X on tie), then remaining.
  Payload escapes the cannon along a cardinal axis first.
- Powder snow brake: stuck-in-block check only applies after the entity *moved into* the snow;
  next move it travels a fraction then velocity is zeroed. Flying machine pushes payload into
  position so the movement registers. Anvils (falling blocks) treat powder snow as solid, need
  special alignment. (Trick credited to Cayman.)
- Calibration: build cannon, fire known settings per direction, log final position; the
  displacement is linear in TNT -> 2x2 matrix per quadrant (diagonal = TNT per block, off-diag
  = cross-coupling from alignment offsets). Negative axes handled by flipping direction.
- TNT source: variable linear dupers (design by Intricate), 1..111 TNT per batch;
  1000 TNT = 9 full batches + 1 batch of 1.
- Stab charge: batch spawned FIRST must have LONGER fuse; same location; shorter-fuse batch
  explodes after moving and pushes the longer-fuse batch down (explosion centre is above
  TNT feet). Fuse difference created by pushing batches into lazy chunks at different ticks.
  More stab stages -> deeper penetration. Longer wait before detonation counters login
  invulnerability.
- Bonus: TNT moving into unloaded chunks and exploding loads chunk for one tick (no item
  entities loaded) -> cascade; "instant perimeter / quarry" idea.

## Mk.4 (LglApzUJ3oI)
- Version history: 1.0 abomination, 2.0 nuclear strike cannon, 3.0 skipped, 4.0.
- 10-TNT dupers (vs 3), stonecutter alignment raises TNT feet to ~explosion origin -> ~4x
  charging speed.
- Settings entered from the NETHER via a snaking dropper line; items in a chest minecart are
  carried to the overworld; multiple targets queued; payload type encoders (stab vs nuke).
- Build ~within 10k blocks of targets, far from players. Flying machine conceals cannon
  underground; powder snow release point 200–300 blocks up.
- Must chunk-align; the payload duper must NOT cross a sub-chunk (16-tall section) boundary.
- Force-shutdown on by default; reset remote settings before disabling.
- Origin = orange glass; nether side placed at origin/8.
- Autofire off: payload waits in stasis forever; if chunks unload/reload it loses velocity and
  blows up the cannon.
- Settings: per axis "count" and "trim"; counts split into decimal digits by item counts.
- Short range: time dominated by payload prep; nukes take longer than stab charges.

## Mk.6 / Mk.6.1, minimal-signature variant (PI_xXZxV6tY, 2SaD3FYNfEs, FwngHf462kI)
- Mk.6 features: disc-encoded ROM, payload magazine (individually selectable shots), wireless
  receiver (daylight-sensor sync), passcode gate, trapdoor concealment.
- Minimal-signature variant: no ROM, no magazine, no hopper-minecart chunk loaders cycling
  items through portals; trapdoor of falling blocks converted to entities in lazy chunks; the
  payload flies through and they land again. Wireless sync without daylight sensors: run one
  circuit a tick faster until coincidence, then lock (can't tell which cannon it synced to).
- Fire control moved from Excel to a web app (origin, passcode, targets, payload type ->
  binary pattern; nether chunk-loader positions; time estimates; presets).
- Passcode: 10-bit, default 940; lamps set bits; composters + sticky pistons decode; manual
  reset after changing lamps (or first signal is ignored then auto-resets).
- 1.21.9 (Copper Age) broke Mk.6: TNT fell slightly slower through the compressor; explosion
  positions changed from ~(0.4923, 0.08125) to ~(0.7856, 0.06125); fixed by shortening the
  compressor one block -> Mk.6.1 (backward compatible).
- Anti-air arrow cannon: broken 1.21.9 (wind charge/bubble column/powder snow), fixed by Mojang
  in 1.21.10 via cubicmetre's bug report, broken again 1.21.11+ by the spear's
  getManyEntityHitResult refactor (no hits through the trapdoor). Not fixable.
  Unstable SMP ran it on Paper 1.21.11 as a non-functional prop.
- Implication for this project: Paper 26.3 is after 1.21.11 -> any wind-charge/arrow-trapdoor
  tech is dead; TNT compressor geometry must be re-validated on 26.3.

## OSC 2.0 / nuclear (aLLlROo_XWo)
- Payload encoder = "integrated circuit": slices, each with counters (pulses to duper rails),
  timers, scheduling counters, and a "redstone breadboard" routing to next slice / loop.
- Payload TNT is duped INSIDE lazy chunks -> each TNT keeps its random prime momentum
  (fixed magnitude 0.02 b/t, random direction). Released together they form a perfect ring.
  Option to cancel X and/or Z prime momentum per batch (alignment) -> rings, lines, columns.
- Fuse control: hopper minecart pulls 1 item/tick; items in hopper = ticks shaved off fuse;
  TNT ticks in entity-processing chunk, then pushed into lazy chunks. Only possible for
  TNT WITHOUT random momentum (else it decays while ticking) -> ring TNT always fuse 80.
- Nuke recipe: 24 x (8-TNT ring batch) + 1 single cancelled-momentum fuse-1 TNT, looped
  10x. Each single TNT explodes right after arrival and pushes earlier rings down -> cone.
- Speed limit: on chunk load, any motion component > 10 b/t is zeroed. Downward speed
  exceeds 10 before horizontal -> cone flattens into a ring -> mushroom cloud. (Same clamp
  as NBT load; confirmed in my tests: Motion 12 -> 0.)
- Damage is from a compact final charge; the mushroom is mostly cosmetic.
- Aiming simplified to ONE quadrant (no omni); decimal encoders; x count e.g. 416 = 400+10+6.
- Cannon retains last settings -> refire same target.

## Mk.6 (q78LRgHt_zU) — "Minecraft's Most Advanced TnT Weapon"
- Designed in 1.21.1; Mk.5 died in 1.21.4 (honey-block entity interaction change broke alignment).
- DOES NOT WORK ON PAPER (shown on Paper 1.21.4: alignment system fails; "Paper does something
  mysterious to the way entities move"). cubicmetre will not support Paper/Spigot/Folia forks.
- Built on Fabric with carpet, carpet-tis-addition (optimizeFastEntityMovement), lithium.
- Vanilla lag: Entity.move collects block shapes over the whole swept AABB volume -> cost ~ cube
  of motion. 171 TNT, 100 blocks -> 1.84e9 checks, one 13.2 s tick. Only ~1588 needed.
  Max range (~250k blocks) -> 3e16 checks. Bug reported to Mojang.
  -> My Paper 26.3 test: 4,436-block release tick ~ a few ms. Paper's collision code already
  avoids the cubic blow-up (at least over unloaded terrain).
- Litematica pasting on servers breaks redstone (fill updates); 1.21.5 added `strict` fill
  flag; containers >256 chars can't be pasted via chat -> use Servux or singleplayer.
- Stealth vs speed: 4k blocks ~3 min charge; ~10k blocks: +1 min per 1000 blocks;
  100k > 1 h; max ~258k blocks ~2 h 45 m.
- No block entities except a chest (F3 pie chart stealth). Auto trapdoors open when no player
  loads the area (kills grass; mangrove swamp ideal). Not underwater (daylight sensors).
- Duper -> acceleration chamber -> magazine is WATER-FLOODED: premature loading no longer
  explodes the cannon (but a running cannon interrupted by restart can still fail).
- Origin chunk-aligned: X, Y, Z all divisible by 16. Y=0 recommended.
- Nether side: origin/8; receivers are just portals next to a fire block; decoy portal above
  the cannon catches players' accidental portal links.
- Materials beyond schematic: 18 boats, 17 chest minecarts, 3 hopper minecarts, 2 stacks iron
  blocks, 3 stacks moss, 68 of each music disc 13..stal (discs 0–7 as 3-bit digits), ~40
  stacks dummy items. Hopper minecart alignment by rolling on powered rail.
- Encoding: binary counters. 15-bit TNT batch counter (batches of 10 TNT, ~7.8 blocks per
  count), 4-bit trim (final batch size), 1 direction bit, x2 axes; 5-bit Y + 4-bit Y trim;
  1 bit nuke/stab + size/depth -> 55-bit instruction.
- Two-stage acceleration (from Hellstorm cannon) -> axes independent, perfectly linear.
- Wireless: daylight-sensor 20-tick global clock; serial encoding: 5 bits per 20 ticks at
  4-tick spacing; first 10 bits must equal passcode; safe passcodes found by stress testing
  10,000 load/unload cycles. Networks isolated by repeater delay pattern (default 2-4-6).
- RWM memory: music discs in chest minecarts, 19 slots per 55-bit instruction; jukebox sorter
  reads discs 0..7 -> 3-bit groups.
- Magazine: 8 payload slots; slot index changes start position (spreadsheet compensates);
  fishing-rod remote trigger (bobber in port; reeling in fires).
- Warheads: stab charge 3 stages (kick, bulk downward accel, penetrator). "Swing" (TNT
  oscillation when exploding near co-moving TNT) kills efficiency: 2 stages 24%, add 10-TNT
  kick one tick earlier 72%, 9 kick TNT with fuses 1..9 -> 99% blast efficiency.
  Stab altitude constant relative to target; depth up to 279.
- Nuke: prime momentum ring (0.02 b/t radius); ring charge (100 TNT fuse 80) + expansion
  charge (single TNT short fuse) + 9 TNT one tick before expansion; repeated -> concentric
  rings. Improvement: TNT per ring proportional to radius (2 binary counters in series)
  -> ~half TNT and time. Nuke holds ~140 blocks above target; diameter = 12 x size
  (max 31 -> 372 blocks); blast zone starts 3.2 above target, slopes ~3 blocks down.
- Perimeters (WaveTech/JKM): deploy nuke late so TNT explodes just above ground; lower each
  shot one block.
