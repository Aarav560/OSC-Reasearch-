"""Volume II, The Cannons: essays and design notes. Facts come from the creators' videos (see the
atlas) and from measuring the schematics; anything I inferred rather than saw is marked so."""

INTRO = [
    '<h2>How the <em>blueprints</em> work</h2>',
    '<p class="lead">Every cannon in this volume was downloaded from its creator\'s own link, loaded block by block, '
    'and drawn from the data, not traced from video. That makes the drawings exact. It also means they show the '
    'cannon as it sits in the schematic, without the entities a real build needs (boats, minecarts, the payload).</p>',
    '<p>Each design opens with an <b>overview sheet</b>: an isometric render with the real 26.3 block textures, the '
    'footprint and height, the number of blocks and redstone parts, a short note on what the design does, and a bar '
    'showing what it is made of. The next sheet holds the <b>side pictures</b>: four orthographic elevations, one from '
    'each side. After that come the <b>layer plans</b>, from the bottom of the build to the top.</p>',
    '<h3>Reading a layer plan</h3>',
    '<p>North is up. One square is one block, and every fifth grid line is drawn brighter so you can count. Each block '
    'is filled with the average colour of its own texture, so stone reads grey, slime green, and redstone red. '
    'Redstone dust is a red dot, with arms towards the neighbours it connects to. An arrow on a repeater or '
    'comparator points the way the signal travels. An arrow on a piston, dispenser, dropper, hopper or observer '
    'points the way it faces, and an outlined triangle marks one that faces up or down. The panel at the bottom '
    'left lists the materials on that sheet; the title block at the bottom right says where you are.</p>',
    '<div class="note"><b>Small builds, big builds</b><p>Small cannons get four layers to a sheet, medium ones two, '
    'and the giants one. cubicmetre\'s original OSC 1.0 is 128 blocks square, so each of its 77 layers gets a whole '
    'page. Near-duplicate variants (the anvil version of OSC 1.0) get an overview and side pictures only.</p></div>',
    '<h3>Where the designs came from</h3>',
    '<p>The schematics were fetched by <code>tools/fetch_schematics.py</code> from the creators\' MediaFire and Google '
    'Drive links in their video descriptions. They are the creators\' work. This volume documents them; it does not '
    'replace their videos, which explain how to set up and fire each one and are catalogued in Volume IV.</p>',
]

GROUPS = [
    {
        "title": "cubicmetre: the original line", "short": "OSC 1.0–4.3", "color": "#e5673b",
        "kicker": "Where it started · 2023–2024",
        "dek": "The first orbital strike cannon and the four generations that followed it.",
        "essay": [
            '<h2>An abomination <em>that worked</em></h2>',
            '<p class="lead">cubicmetre called his first orbital strike cannon an abomination, and the drawings in this '
            'chapter show why: OSC 1.0 covers 128 by 128 blocks and stands 77 tall. It is also the machine that '
            'proved the whole idea.</p>',
            '<p>The principle has not changed since. Two nether-portal chunk loaders keep a 3×3 block of chunks fully '
            'processed. The chunks around that block are "lazy": they exist, but entities in them do not move. Where '
            'the processed regions of two loaders and their lazy rings meet, the payload sits frozen in a lazy chunk '
            'while propellant TNT explodes next to it in a processed one. Each explosion adds velocity that the payload '
            'cannot use yet. Thousands of explosions later, the payload\'s chunk is loaded, and it moves its entire '
            'stored velocity in one game tick: kilometres in a twentieth of a second.</p>',
            '<p>Version 1.0 aimed with lecterns and dropper counts set from an Excel sheet, and fired two warheads: an '
            'anvil, or a "bunker buster" stab charge of TNT. It would not fire while a player kept it loaded, so the '
            'operator waited in the nether. The range was about 45,000 blocks, limited by how much the client could '
            'take: past roughly 2,000 blocks of flight, singleplayer crashed without the Carpet mod\'s optimisations.</p>',
            '<h3>From 2.0 to 4.3</h3>',
            '<p>2.0 was the "nuclear" cannon: TNT duplicated inside lazy chunks keeps its random priming momentum, so a '
            'ring of TNT released together spreads into a perfect circle. Version 3.0 was skipped. 4.0 brought 10-TNT '
            'dupers instead of 3, a stonecutter trick that raised each TNT to the height of the explosion centre for '
            'about four times faster charging, and settings entered from the nether through a snaking dropper line, '
            'carried to the overworld in chest minecarts. The 4.3 schematic here is the last of that generation: 59 '
            'blocks square, 53 tall.</p>',
            '<div class="pull"><div>The payload must not cross a 16-block section boundary.</div><small>cubicmetre, Mk.4 setup rules</small></div>',
            '<p>Every version shares the setup rules that make the physics repeatable: chunk-aligned origin, the '
            'payload duper kept inside one 16-tall sub-chunk, and force-shutdown on by default. They are as much a part '
            'of the design as the blocks.</p>',
        ],
        "designs": [
            ("orbital-strike-1-0", "The first orbital strike cannon. Two portal chunk loaders, a lazy intersection and a "
             "TNT battery the size of a small town. Aimed with lecterns and dropper counts from a spreadsheet; anvil or "
             "stab-charge payload; about 45,000 blocks of range.", {}),
            ("orbital-strike-1-0-anvil", "The same machine set up for the anvil payload. The structure is nearly "
             "identical to the TNT version, so only the overview and side pictures are drawn here.", {"summary_only": True}),
            ("orbital-strike-1-0-nether", "OSC 1.0's nether side: the portal end of the chunk loaders, placed at the "
             "origin divided by 8.", {}),
            ("orbital-strike-2-0", "The \"nuclear\" cannon. TNT duplicated inside the lazy chunks keeps its random 0.02 "
             "b/t priming momentum, so a batch released together spreads into a ring. Per-batch alignment can cancel "
             "the X or Z momentum to make lines and columns instead.", {}),
            ("orbital-strike-3-0", "A third-generation build. cubicmetre's own history says 3.0 was skipped as a "
             "release, so treat this as the bridge between 2.0 and 4.0.", {}),
            ("orbital-strike-4-3", "The Mk.4 generation: 10-TNT dupers, stonecutter-aligned TNT for about four times "
             "faster charging, settings sent from the nether in chest minecarts, and selectable stab or nuke payloads.", {}),
            ("orbital-strike-nether-4-3", "Mk.4's nether control side: the dropper line where the settings are entered "
             "and the portal that carries them to the cannon.", {}),
        ],
    },
    {
        "title": "cubicmetre: Mk.6 and Minimal Signature", "short": "Mk.6", "color": "#c2410c",
        "kicker": "The state of the art · 2025–2026",
        "dek": "Fire-control ROM, wireless link, payload magazine, and the stealth build that drops all of it.",
        "essay": [
            '<h2>Minecraft\'s most advanced <em>TNT weapon</em></h2>',
            '<p class="lead">Mk.6 is where the orbital strike cannon stopped being a contraption and became a weapon '
            'system. It reads its targets from a ROM of music discs, takes orders over a wireless link, and keeps eight '
            'payloads in a magazine.</p>',
            '<p>A target is a 55-bit instruction: a 15-bit count of 10-TNT batches and a 4-bit trim per horizontal axis, '
            'a direction bit each, 5 bits of height plus a 4-bit trim, and a bit choosing nuke or stab charge with its '
            'size or depth. Music discs 13 to stal, read by a jukebox sorter as the digits 0 to 7, store those bits three '
            'at a time, 19 discs per instruction. The wireless link synchronises on the global daylight-sensor clock '
            'and sends five bits every 20 ticks; the first ten bits must match a passcode (940 by default).</p>',
            '<p>Its acceleration is two-stage, borrowed from the Hellstorm cannon, which makes the two axes independent '
            'and the response perfectly linear. The duper, acceleration chamber and magazine are flooded with water, '
            'so loading the chunks too early no longer blows the cannon up. Warheads are a three-stage stab charge '
            '(up to 279 blocks deep) and a ring nuke up to 372 blocks across.</p>',
            '<h3>Version drift</h3>',
            '<p>Mk.5 died in 1.21.4 when honey-block entity interaction changed. Mk.6 was built for 1.21.1, then broken '
            'in 1.21.9, when TNT fell slightly slower through its compressor and the explosion positions moved. Shortening '
            'the compressor by one block gave Mk.6.1, the version drawn here. cubicmetre is explicit that it does not '
            'run on Paper: "Paper does something mysterious to the way entities move."</p>',
            '<div class="note"><b>On my Paper 26.3 server</b><p>I pasted Mk.6.1 and its boat-portal loaders cycled '
            'correctly, but the cannon never received a wireless instruction, as cubicmetre predicted. Volume I has the '
            'details.</p></div>',
            '<h2>Minimal <em>Signature</em></h2>',
            '<p>The Minimal Signature variant gives up the ROM, the magazine and the item-cycling chunk loaders to leave '
            'as little trace as possible. Its trapdoor is made of falling blocks turned into entities in lazy chunks: '
            'the payload flies through, and they land again. Its wireless link syncs without daylight sensors, by running '
            'one circuit a tick fast until the two coincide and then locking.</p>',
        ],
        "designs": [
            ("the-orbital-strike-cannon-mk-6-1", "Mk.6.1: disc ROM, wireless receiver with passcode, eight-slot "
             "magazine, water-flooded duper and acceleration chamber, two-stage acceleration. Fires 3-stage stab charges "
             "or ring nukes. The fix over Mk.6 is a one-block-shorter TNT compressor for 1.21.9.", {}),
            ("osc-6-nether", "Mk.6's nether side. Its receivers are portals next to a fire block, with a decoy portal "
             "above the cannon to catch players' accidental portal links.", {}),
            ("osc-6-control-panel", "The Mk.6 control panel, where an instruction is set as a pattern of buttons and "
             "lamps before it is sent over the wireless link. My Python port of the fire-control maths fills it in "
             "(tools/firecontrol.py).", {}),
            ("osc-minimal-signature", "The stealth Mk.6: no ROM, no magazine, no item-cycling chunk loaders. A trapdoor of "
             "falling-block entities hides the barrel, and the wireless link syncs without daylight sensors.", {}),
            ("osc-ms-nether", "Minimal Signature's nether side.", {}),
            ("osc-ms-control-panel", "Minimal Signature's control panel.", {}),
        ],
    },
    {
        "title": "cubicmetre: beyond the OSC", "short": "Artillery", "color": "#9a3412",
        "kicker": "Railcannon, Skybender, artillery",
        "dek": "The other long-range machines: railguns, a breeze-powered cannon, anvil artillery and an anti-air gun.",
        "essay": [
            '<h2>A decade of <em>TNT engineering</em></h2>',
            '<p class="lead">The orbital strike cannon grew out of years of TNT machines, and cubicmetre kept building '
            'others alongside it. This chapter draws the rest of his published long-range designs.</p>',
            '<p>They share the OSC toolkit (chunk-aligned builds, TNT dupers, precise alignment of explosions against a '
            'payload) but aim it differently. The Railcannon and the TNT Railgun fire along a line. The Skybender ships '
            'with a breeze collector. The anvil and cluster artillery lob falling blocks. The '
            'Smart Artillery\'s companion "envelope" schematic, a 227×188×174 map of where the shells can land, is '
            'left out: it is a range chart, not a machine.</p>',
            '<div class="note"><b>Anti-air on 26.3</b><p>cubicmetre\'s anti-air arrow cannon broke in 1.21.9, was '
            'fixed by Mojang in 1.21.10 after his bug report, and broke again in 1.21.11 when the spear\'s entity hit '
            'detection was refactored. He considers it unfixable, and 26.3 is after that change, so treat its drawings '
            'here as history.</p></div>',
        ],
        "designs": [
            ("the-orbital-railcannon", "A railcannon in the OSC family: a long straight accelerator, 35 by 30 blocks "
             "and 50 tall.", {}),
            ("orbital-skybender-1-0", "The Orbital Skybender, 52 by 42 blocks and 28 tall. It ships with a Breeze Collector, so breezes are part of how it is powered; the drawings show the machine, not its mobs.", {}),
            ("skybender-entity-setup", "The entity setup for the Skybender: where its mobs and minecarts go.", {}),
            ("skybender-nether", "The Skybender's nether side.", {}),
            ("breeze-collector", "A breeze collector that supplies the Skybender.", {}),
            ("anvil-arty", "Anvil Artillery: a 16-by-11 gun from the same download as the cluster gun. As the name says, its shell is an anvil.", {}),
            ("cluster-arty", "Cluster Artillery: the anvil gun's sibling, slightly larger at 18 by 11.", {}),
            ("smart-arty", "Smart Artillery, the gun itself (the range-envelope schematic is left out).", {}),
            ("tnt-railgun", "A TNT railgun, 9 blocks wide and 38 long: a straight-line TNT accelerator.", {}),
            ("anti-air-auto-cannon", "The anti-air auto-cannon. It depends on arrows passing a trapdoor, which the "
             "1.21.11 spear refactor broke; drawn for the record.", {}),
        ],
    },
    {
        "title": "TK.Paarmaa: Compact Edition", "short": "TK.Paarmaa", "color": "#3f9ad6",
        "kicker": "Small, fast, accurate",
        "dek": "An OSC for players who want one without a megaproject.",
        "essay": [
            '<h2>The compact <em>edition</em></h2>',
            '<p class="lead">TK.Paarmaa\'s Compact Edition starts from a complaint: the earlier mini orbital cannon '
            '(Table\'s) fired a single particle slowly and not very accurately. The CE is his answer.</p>',
            '<p>From his tutorial: it works from 1.21.5, is designed for 1.21.11, and fires over a 90° arc, so placement '
            'decides which quarter of the map it can reach. Setup is the usual OSC routine: chunk-align the schematic to '
            'a chunk corner (one part in its own chunk, the rest in the others), raise it to the height you want, build '
            'a small structure on the nether side, and put an ender pearl in the stasis chamber. A calculator takes the '
            'origin (the bottom snow block) and the target, and gives the settings to enter. On whether it works on '
            'Paper, his advice is simply to try it.</p>',
        ],
        "designs": [
            ("osc-ce-mk1-1", "OSC Compact Edition Mk1.1: a small, chunk-aligned cannon with a 90° firing arc, aimed with "
             "TK.Paarmaa's calculator from the powder-snow origin block.", {}),
            ("osc-ce-mk3", "Compact Edition Mk3, the \"most efficient\" upgrade. 18 by 17 blocks and 15 tall.", {}),
            ("osc-ce-mk3-nether-side", "The Mk3's nether side: a handful of blocks that close the portal chunk loader.", {}),
        ],
    },
    {
        "title": "White Mc (WMC): pearls and withers", "short": "WMC", "color": "#4fae6a",
        "kicker": "Lazy acceleration, other payloads",
        "dek": "The same lazy-chunk physics, used to throw ender pearls and charging withers.",
        "essay": [
            '<h2>Teleporting, <em>and withers</em></h2>',
            '<p class="lead">WMC\'s cannons use the lazy-chunk accelerator for payloads other than TNT. The 360 Lazy '
            'Acceleration Ender Pearl Cannon is a transport: it throws you, by pearl, anywhere in the world to the block.</p>',
            '<p>He frames it as the last step in a long line of pearl cannons. A perfectly thrown pearl lands about 54 '
            'blocks away; TNT cannons pushed that further, and calculators reverse-engineered pearl flight. Lazy '
            'acceleration removes the limits, and "360" means all directions. The Wither Cannon fires a batch of '
            'withers still in their charging state. When a player loads the target area, they go off together. By '
            'his description it builds in under five minutes, a Python script gives the settings, and it fires the '
            'next time its chunks load. If you load it by accident while it charges, it launches the withers out of '
            'range rather than blowing up.</p>',
        ],
        "designs": [
            ("360-lazy-accel-canon-nether", "The 360 Lazy Acceleration Ender Pearl Cannon (nether build): a lazy-chunk "
             "accelerator that throws an ender pearl, and its owner, anywhere in the world to the block. 71 blocks tall.", {}),
            ("360-lazy-accel-canon-overworld", "The overworld side of the pearl cannon.", {}),
            ("wither-cannon-v1-wmc", "Wither Cannon V1: TNT lazy acceleration launches a batch of charging withers, which "
             "detonate when the target area is loaded. Settings come from a Python script.", {}),
        ],
    },
    {
        "title": "Paper ports and the tiniest cannons", "short": "Small & Paper", "color": "#b88ad9",
        "kicker": "HOGAN, Table, TheeDumbRock",
        "dek": "Orbital strike cannons for Paper servers, and the race to make them small.",
        "essay": [
            '<h2>Small, and <em>Paper-proof</em></h2>',
            '<p class="lead">The last chapter collects the cannons built for Paper servers and the race to make an OSC '
            'as small as possible: from Table\'s Mini Orbital Strike Cannon in 2023 to TheeDumbRock\'s 16-block MOSC '
            'in October 2026.</p>',
            '<p>HOGAN\'s Paper Orbital Strike Cannon is a 360° Paper build, with a multi-ring version in his updated '
            'tutorial. Its setup has a rule worth remembering: the drop from the origin to the target height should be '
            'about 71 blocks, and he moves the build to fit. TheeDumbRock\'s calculator says the same: under 71, or "the '
            'TNT just explodes in the air". That is the fuse running out mid-fall, the limit Volume III measures on Zephyr Mk3.</p>',
            '<p>TheeDumbRock credits HOGAN\'s cannon as the start of his own series: a first build that did not work '
            '(the wind charges hit just off-centre, where linear aiming breaks down), then a smaller layout, then '
            'TOSC and WOSC, the Hollower (his first with a ring payload), a 30-block "world\'s smallest" made with Phantom '
            'Lover, and finally the 16-block MOSC, after others in the community answered with 17, 20 and 23-block '
            'cannons.</p>',
            '<div class="note"><b>MOSC on Paper 26.3</b><p>I tested MOSC on my server. It charges perfectly, but its '
            'TNT is dispensed straight into the powder snow inside the lazy chunk, and on 26.3 that never arms the brake. '
            'On release it kept flying instead of stopping. Volume I explains the arming rule.</p></div>',
        ],
        "designs": [
            ("the-paper-orbital-strike-cannon-mk-2-1", "HOGAN's Paper Orbital Strike Cannon Mk.2.1: a 360° cannon "
             "built for Paper servers. The drop from origin to target should be about 71 blocks.", {}),
            ("ponc-2-nether", "The nether side of HOGAN's Paper orbital nuke cannon.", {}),
            ("mini-orbital-strike-cannon-500blocks", "Table's Mini Orbital Strike TNT Cannon (2023), 500-block version: "
             "the early small OSC that TK.Paarmaa set out to beat.", {}),
            ("mini-orbital-strike-cannon-2k-blocks", "The 2,000-block version of Table's mini cannon. Almost the same "
             "build; the difference is in how far it is set to throw.", {}),
            ("tosc", "TheeDumbRock's TOSC: one of the first in his series of tiny cannons.", {}),
            ("wosc-2-0", "WOSC 2.0: a wind-charge orbital strike cannon a few blocks across.", {}),
            ("wosc-thee-hollower", "The Hollower: TheeDumbRock's first cannon whose payload blows out a ring instead of a "
             "single crater. Build it about 100 blocks up.", {}),
            ("mosc", "MOSC: 16 blocks. Wind charges in, TNT in, pearls for the chunk loaders. On Paper 26.3 its powder-snow "
             "brake never arms (see the note on the chapter's first page).", {}),
        ],
    },
]
