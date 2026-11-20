# Video essay architecture: recon (2026-11-20)

Read-only. some-ui at `main` 6a155510d, server at `main` 96f77e39. In-flight branches were read
at: PR #3316 head 3f617ec1a, PR #3314 head 5dafa84b9, `claude/walk7-spoken-card` head ba56342cf,
server PR #1051 head 76f8953a. server#1052 is an **issue** (the server half of WALK7), not a PR.
Paths without a repo prefix are some-ui's `packages/video-render/src/`.

## 0. Verdict: do we have that graph? **Partly.**

- **The back half is one compile-time graph.** Every voiced kind compiles to one schema,
  `some-ui.cut-list/2` (`cut-list.ts:27`, `CutListSchema` `cut-list.ts:220`). From there, one
  renderer draws it: captions from words, loudness, the music bed, burn-ins and HyperFrames
  compositions. One template schema describes every format (`some-ui.show-format/1`,
  `format.ts:34,182`). One cut-list builder lays a "still plus take" scene on the timeline
  (`stillsCutList`, `stills.ts:156`). One recorder loop records the stills and the voice
  (`recordStills`, `apps/www/tests/record/voiced.ts:377`). One stage frame draws the intro,
  brand and chapter slides (`apps/www/src/lib/web-surface/call/frame.tsx:54-251`). On the
  server, one voice store with one verdict (`crates/db/voice`, `verdict.rs:29`) feeds one
  render worker loop.
- **The front half is per kind.** That is each kind's source schema, its scene union, its
  framing, its speaker-to-voice map, how its takes are named and handed over, and how a
  transcript reaches it. Each kind re-implements the same small set of ideas: the framing
  sequence (intro, brand-in, chapter slides, brand-out), a scene union, a `xCutList` wrapper,
  a "take or silence" answer, and a take-file naming scheme. **"Speaker" is not a node.** It
  is a role union in the two essays (`essay.ts:1036`), a section key in the call
  (`call.ts:928`), a constant in the report and Playoff Delta, and host/narrator in cards.
- **In flight, the drift grows.** WALK7 adds a 7th scene union, a 2nd exchange schema, a 2nd
  stills loop and a 3rd way a transcript reaches the recorder. server#1052 plans a 2nd take
  exporter. #3314 adds a 5th take-naming scheme and a 2nd copy of the category list. #3316,
  by contrast, extends a shared node (`StillScene.picture`) and is the model to follow.

So the schema is compile time at the cut list, but not at the essay. "Any video essay is the
same thing at compile time" holds for what the renderer reads. It does not hold for what a
session or routine writes, nor for the scene/voice/take layer between the two.

## 1. The kinds, one by one

| Kind | Source schema (what is written) | Compiles to | Scene union | Voice map |
|---|---|---|---|---|
| Weekly call | `CallWeekSchema` `call.ts:351` (`some-ui.call-week/1`, `:72`) | `callCutList` `call.ts:959` → `stillsCutList` | `CallScene` `call.ts:542` | `CALL_VOICES` by section `call.ts:928` (7 Kokoro voices) |
| Playoff Delta | `NarrationSchema` `packages/ui/playoff-delta/src/lib/narration.ts:30` (`some-ui.pd-narration/1`) + season | `voicedCutList` `playoff-delta/src/lib/voiced.ts:143` → `stillsCutList` | `VoicedScene` `voiced.ts:32` (uses `kind`, not `section`) | `PD_VOICE` constant `voiced.ts:30` (`af_heart`) |
| Rust Rounds essay (rust-essay) | `EssaySchema` `essay.ts:611` (`some-ui.rust-essay/1`, `:81`) | `essayCutList` `essay.ts:1403` → `stillsCutList` | `EssayScene` `essay.ts:1059` | `ESSAY_VOICES` by `Speaker` `essay.ts:1052`; owner's takes for `you` |
| …its opening exchanges | `opening.exchanges[] {n, ask, transcript, take}` `essay.ts:639`; limits `CONVERSATION_MOST=3` `opening.ts:60`, `Exchange` `opening.ts:73` | `ask-n`/`opening-n` scenes `essay.ts:1208-1225` | (inside `EssayScene`, `exchange?`) | asker = `af_heart` (Kokoro), you = owner take `opening.<n>` `essay.ts:122` |
| Interview essay | `InterviewEssaySchema` `interview-essay.ts:328` (`some-ui.interview-essay/1`, `:77`) | `interviewEssayCutList` `interview-essay.ts:692` → `stillsCutList` | `InterviewEssayScene` `interview-essay.ts:430` (same shape as `EssayScene`) | reuses `Speaker`/`ESSAY_VOICES` (imports `essay.ts`) |
| Cards essay | **is** a cut list (`parseCardsEssay` `cards-essay.ts:102`) + `Spoken` `cut-list.ts:158` | `voicedCardsCutList` `cards-essay.ts:311` → `heldFor` (not `stillsCutList`) | `CardsScene = StillScene & {shot, lines, mark}` `cards-essay.ts:204` | `CARDS_VOICES {host, narrator}` `cards-essay.ts:49`, derived from `CALL_VOICES` |
| Engagement report | `EngagementReportSchema` `engagement-report.ts:468` (`some-ui.engagement-report/1`) | `reportCutList` `engagement-report-video.ts:576` → `stillsCutList` | `ReportScene` `engagement-report-video.ts:441` | `REPORT_VOICE` constant `engagement-report-video.ts:72` (`am_michael`) |
| Preview | any `CutList` | `previewOf` `preview.ts:142` (generic) | none of its own: roles by id `preview.ts:48` | inherits |
| Release promo | `ReleaseSchema` `packages/video-motion/src/promo.ts:47` (`some-ui.promo/1`) | `promoCutList` `promo.ts:103`: composition pictures, no voice | none: on-screen "captions" are composition variables `promo.ts:151` | none |
| Clip walk | `ClipIndexSchema` `clip.ts:108` (`some-ui.clip-index/2`), `some-ui.walk/1` | **not a video**: stills + `walk.json` by `motion walk` (`packages/video-motion/src/walk/run.ts`) | n/a | n/a |
| Studio shorts / Build Journal | phone-built cut list (`packages/ui/soundbites/src/lib/project/script.ts:76` `fitted`) | the cut list directly, `record:short` (`apps/www/tests/record/short.ts`) | n/a | owner takes only |
| (in flight) WALK7 spoken card | `role: "spoken"` added to `SpokenSchema` (walk7 `cut-list.ts:158-209`), `HeardSpokenCardSchema` (walk7 `spoken-card.ts:59`, `some-ui.spoken-card/1`) | inside `voicedCardsCutList` | `SpokenScene` (walk7 `spoken-card.ts:85`) | `SPOKEN_ASKER_VOICE = ESSAY_VOICES.asker` (walk7 `spoken-card.ts:123`) |

Templates: each voiced kind's `Format` is an instance of the shared `FormatSchema`
(`format.ts:182`). Four are built in code with a `versionRefusal` wrapper: `essay.ts:261-269`,
`interview-essay.ts:155-163`, `call.ts:200-208` and `engagement-report-video.ts:109-113`.
Playoff Delta's is `formatOf` in `playoff-delta/src/lib/show`. Pinned copies are in
`templates/*/v*.json`; the interview essay has no pinned `v*.json`, only `sample-essay.json`.
**This part is generic, correctly.**

## 2. Voice: how it reaches each kind

### Kokoro lines (synthetic)
One path, shared. A kind's scene gives `{said, voice}`. `recordStills` (`voiced.ts:377`) asks
home's speaker through `takeOf`/`said` (`voiced.ts:177`, `:108`) and `speakScene`
(`speaker.ts`, which chunks and joins with `joinTakes` `speaker.ts:144`). The step cache is
keyed by model, voice and words. `heldFor` (`stills.ts:129`) turns the take into a shot with
`speaker: "kokoro"` (`stills.ts:23,144`). Cards use a sibling, `sayLines` (`voiced.ts:481`),
because a card scene has two lines in two voices. It shares `speakerOf`/`takeOf`.
**Shared, apart from the cards sibling.**

### The owner's takes
- **Server, one store.** Every take is a voice note (`crates/db/voice/src/lib.rs:139` `Of`)
  with a transcript, words and a verdict (`verdict.rs:29`: heard, garbled, nothing_said,
  failed), judged once in `file_host/src/transcribe/verdict.rs` (rule `heard-1`). **One
  node.**
- **Server, handed to the recorder.** One exporter writes `<id>.<ext>` and `<id>.words.json`
  into `takes/`. It is `rust_essays::takes` (`file_host/src/rust_essays.rs:588-623`), shared
  by the Rust Rounds and interview kinds through `Kind`/`Spec` (`rust_essays.rs:121-156`;
  the module doc says a third kind "is a Kind and a Spec, not a copy"). If a take has not
  reached home, the essay waits (`Takes::Waiting`, `:579-586`). If a take was deleted, the
  essay is refused. An unheard take is set aside (`unheard`, `:503`).
  **Planned second copy:** server#1052 asks `cards_essays` to write `$ESSAYS/<key>.takes/`
  with `<take>.<ext>`, `<take>.words.json` **and** `<take>.transcript.json`, with its own
  hold and refuse rules. That is a parallel exporter, not a third `Kind`.
- **Client, which file is which take.** One function, `takeFilesOf` (`take-files.ts:27`),
  wrapped per kind: `essayTakeFiles` `essay.ts:1498`, `interviewEssayTakeFiles`
  `interview-essay.ts:742`, and (walk7) `spokenTakeFilesOf` `spoken-card.ts:201`. Each
  wrapper has its own scene→take mapper: `essayTakeOf` `essay.ts:1460`, `interviewTakeOf`
  `interview-essay.ts:772`, and walk7's exchange `take` ids.
- **Client, play the take.** One function, `ownTake` (`voiced.ts:66`): ffmpeg to mono WAV,
  probe its length, words from `.words.json` or `spreadWords` (`stills.ts:76`). Walk7 exports
  and reuses it. **Shared.**
- **Take naming.** Each kind names its takes its own way:
  - `<TICKET>` and `<TICKET>.<n>` (`essay.ts:695`);
  - `opening.<n>` (`essay.ts:122`);
  - `<question>` and `read.<card>`, with the interview opening as `read.opening`
    (`interview-essay.ts:731-734`);
  - walk7: a raw home take id (`SPOKEN_TAKE_ID`);
  - #3314: `spoken:<card>.<part>` (`apps/www/src/lib/studio-spoken/model.ts`, C807);
  - Studio shorts: `<project>:<shot>:<take>` (server `voice/src/lib.rs:150-155`).

### Transcript
- **Essays.** The transcript travels **inside the essay JSON**, written by the routine:
  `transcript: words` at `essay.ts:423,444,644` and `interview-essay.ts:290,317,345`. The
  answer scene's `said` is that transcript (`essay.ts:1177`).
- **Walk7.** The recorder reads `<id>.transcript.json` beside the take and calls `hearingOf`
  itself (`heardSpokenCard`, walk7 `spoken-card.ts:245-270`).
- **Phone.** It reads the verdict with the same `hearingOf` in
  `packages/ui/interview-week/src/lib/essay/record.ts:107` and
  `packages/ui/rust-rounds/src/lib/monday/record.ts:169`.
- **So:** two channels for the transcript into a render (embedded by a routine, or a file
  beside the take), with walk7 making the second.

### Word timings
Five definitions of the same `{text, startMs, endMs}`:
- `TimedWordSchema` `cut-list.ts:122`;
- `TimedWord` `packages/ui/burn-ins/src/lib/captions/timing.ts:21`;
- `HeardWord` `heard.ts:11` (plus `p`, `unsure`);
- the recorder's `TimedSchema` `apps/www/tests/record/voiced.ts:97`;
- the server's ad hoc `serde_json::json!` at `rust_essays.rs:614-618`, rather than a shared
  wire type.

### Verdict
- One server type with 4 kinds (`verdict.rs:29`). One client reader collapses it to 3
  (`hearingOf` `verdict.ts:26`).
- One `Silence` shape shared by both essays (`SILENCE_FIELDS` `verdict.ts:52`,
  `UNHEARD_SAID` `:41`). **Shared, correctly.**
- **The take side is not shared.** The "take" half of an answer is redeclared 4 times:
  - `AnswerSchema` take `essay.ts:419-427`;
  - `PointAnswerSchema` take `essay.ts:441-448`;
  - interview question answer `interview-essay.ts:285-297`;
  - interview read answer `interview-essay.ts:312-323`.
- Each is `{kind:"take", transcript, …kind-specific judgement}`.

### Noise and loudness
- No denoise anywhere: no `afftdn`, `arnndn` or similar in `video-render` or the recorders.
- One voice chain for every kind: `planVoice` (`plan.ts:554`, `highpass=f=70`) and
  `LOUDNESS` (`plan.ts:596`, two-pass loudnorm, `planMeasure` `:599`).
- Noise is judged only as a verdict signal on the server (speech loudness,
  `voice/src/verdict.rs:101`).
- **Generic, one path.**

### Captions
- One path: `heardWords` (`render.ts:137`) trims words to the take, then `spokenLines`
  (`render.ts:159`) feeds the burn-ins `captions` design
  (`packages/ui/burn-ins/src/lib/captions/*`).
- Turned on per format by `hasCaptions(format)` (`stills.ts:52`). Cards force it on
  (`cards-essay.ts:322-325`).
- **Generic, correctly.**

### Joining takes
Three implementations of "several takes as one":
- `joinTakes` (`speaker.ts:144`): WAV bytes and words, no gap, for Kokoro chunks;
- `joinedTake` (`cards-essay.ts:290`): words and length only, with a `CHAPTER_GAP_MS` gap;
- the audio side of `joinedTake`, an ffmpeg `apad`/`concat` graph rebuilt in the recorder
  (`apps/www/tests/record/cards.ts:80-131`).

The second and third must agree on the gap by convention.

### Take to scene length
- Two rules: `heldFor` (`stills.ts:129`: 300 ms in, take, 700 ms tail) for feeds and
  essays, and `fitToTake` (`timing.ts:14`) for phone Studio projects
  (`soundbites/src/lib/project/script.ts:66-73`).
- Both use `TAIL_MS`, but through different functions.

## 3. Scenes and templates

### Picture kinds: shared
`capture | still | card | composition` (`cut-list.ts:44-77`). Compositions are HyperFrames:
- brand in and out by `brandPicture` (`stills.ts:106`);
- promos (`promo.ts`);
- #3316's `screen-zoom`, through a new optional `StillScene.picture` (#3316 `stills.ts`
  diff, `zoom.ts`).

That is a shared node, extended once and used by any kind.

### Scene kinds: per kind
Six unions (seven with walk7), each pairing a section or role with `{id, said}` and a chapter
variant:

| Union | Where |
|---|---|
| `CallScene` | `call.ts:542` |
| `EssayScene` | `essay.ts:1059` |
| `InterviewEssayScene` | `interview-essay.ts:430` |
| `ReportScene` | `engagement-report-video.ts:441` |
| `VoicedScene` | `playoff-delta/src/lib/voiced.ts:32` |
| `CardsScene` | `cards-essay.ts:204` |
| `SpokenScene` (walk7) | `spoken-card.ts:85` |

- **Framing type, 4 copies.** `type Framing = "intro" | "brand-in" | "chapter" | "brand-out"`
  is declared at `call.ts:166`, `essay.ts:203`, `interview-essay.ts:114` and
  `engagement-report-video.ts:77`. Playoff Delta spells it inline (`voiced.ts:33-44`),
  `storyboard.ts:28` lists it, and `preview.ts:48` re-derives it by id.
- **Framing sequence, 5 copies.** The sequence (locked intro, `brand.intro`, a chapter
  before each section in `shape.chapters`, `brand.outro`) is hand-built in:
  - `call.ts:766-794` (`framed`);
  - `essay.ts:1188-1206 …`;
  - `interview-essay.ts:533-550 …`;
  - `engagement-report-video.ts:508-556`;
  - `playoff-delta/src/lib/voiced.ts:96-126`.
- **Cut-list wrapper, 5 copies.** The `xCutList` wrapper is the same 20 lines 5 times: build
  the feed header from `format`, map scenes to `{id, file: stillFile(i,id), said}`, then call
  `stillsCutList`. See `call.ts:959-993`, `essay.ts:1403-1429`, `interview-essay.ts:692-718`,
  `engagement-report-video.ts:576-599` and `playoff-delta/src/lib/voiced.ts:143-166`.
- **Stage side.** The shared parts are generic: `StageFrame`, `LockedIntro`, `BrandSlide` and
  `ChapterSlide` (`frame.tsx`), and template A's two bubbles (`Call`/`Bubble`,
  `essay-parts.tsx:59-110`), which both essays share. Each kind has its own view parser and
  stage (`view.ts`, `essay-view.ts`, `interview-essay-view.ts`, `report-view.ts`,
  `rust-screen-view.ts` and the `*-stage.tsx` files). These are content, and are right to be
  per kind.
- **Exchange, 2 copies.** The essay opening (`essay.ts:639`, limit 3 at `opening.ts:60`,
  `Exchange` at `opening.ts:73`) and walk7's spoken card (`cut-list.ts:158-209` on walk7,
  limit `SPOKEN_EXCHANGES_MOST = 6` at `:171`). Both mean "Kokoro asks, then the owner's take
  answers". The interview essay's opening is a single read (`interview-essay.ts:345`), a
  third shape.

## 4. Server side: how home hands each kind to the render

### Render worker: one loop, 8 jobs
`infra/render/render-calls.sh:288`: `JOBS=(call playoff-delta preview rust-essay clip-walk
cards-essay interview-essay report)`.

- **Shared across all jobs:** the lane, retry, policy caps and refusal holds (`:162-215`),
  the step cache, heartbeats and progress.
- **Per kind:** six `case` tables with one arm per job:

| Table | Line |
|---|---|
| `use_job` (folders) | `:313-339` |
| `episodes` (key regex and order) | `:349-411` |
| `holds` | `:538-547` |
| `record` (the recorder command line) | `:550-617` |
| `finished` | `:629-645` |
| `max_minutes` | `:282-286` |

`record` has 8 arms but only 6 recorders. Rust-essay and interview-essay share
`tests/record/essay.ts`. Preview dispatches to the call, report, essay or Playoff Delta
recorders (`apps/www/tests/record/preview.ts`).

**Verdict:** one generic loop with per-kind tables. Adding a kind is about 6 case arms plus a
recorder. #1051 adds a conditional `--week-file` arm for rust-essay. server#1052 plans a
conditional `--takes` arm for cards-essay.

### file_host: N pollers and exporters, one per kind
- **The kinds:**

| Kind | Poller or exporter | Notes |
|---|---|---|
| Weekly call | `call_weeks.rs` + `call_weeks/{pass,render,lane}.rs` | polls testing |
| Playoff Delta | `pd_fills` | |
| Preview | `previews.rs` | |
| Rust Rounds and interview essays | `rust_essays.rs` | the one generic exporter, by `Kind` |
| Cards essay | `cards_essays.rs` + `cards_essays/pass.rs` | polls testing |
| Engagement report | `report_weeks.rs` | |
| Clip walk | `clips.rs` + `clips/pass.rs` | |

- **Shared:** the board, `call_weeks::render::{tally, Held, Renders}`, used by
  `cards_essays.rs`, `report_weeks.rs`, `rust_essays.rs`, `previews.rs`, `pd_fills/render.rs`
  and `feeds/*`. The Studio › Renders board is one read (`feeds/renders.rs`).
- **Duplicated:** each module has its own `observe`:
  - `call_weeks/render.rs:168`;
  - `cards_essays.rs:172`;
  - `report_weeks.rs:481`;
  - `rust_essays.rs:906`, with its own `Seen` at `:896`;
  - `pd_fills/render.rs:154`, with its own `Seen` at `:138`.
- **Holds and refusals:**
  - Waiting for takes exists only in `rust_essays` (`Takes::Waiting`, `:579-586`).
  - Refusal against the week's final record is `rust_essays` only (`keep_refusal`, `:849`).
  - server#1052 plans the same hold-and-refuse for cards, written separately.

### Kind lists kept in step by hand
- **Template ids, 3 copies:** `templates.ts:37-43`; server `previews.rs:73`
  (`TEMPLATES: [&str; 5]`); `render-calls.sh:293` (`PREVIEW_ID` regex).
- **Cards key, 3 copies:** `cards-essay.ts:61`; `render-calls.sh:303`;
  `cards_essays/pass.rs:94` (`is_key`).

## 5. Speakers

- **Essays.** `Speaker = "tutor" | "you" | "asker"` (`essay.ts:1036`) with `Voicing = owner |
  sample` (`:1044`). `ESSAY_VOICES` maps tutor to `am_michael`, you to `bm_george` (sample
  only) and asker to `af_heart` (`:1052-1056`). The interview essay imports both types.
  Template A's bubbles draw them: `ICONS: Record<Speaker,…>` (`essay-parts.tsx:53`) and
  `Bubble` (`:59`).
- **Call.** It has no speaker. The voice is keyed by **section** (`CALL_VOICES:
  Record<Section|Framing,string>`, `call.ts:928-941`), so "who speaks" is implicit in what
  is said.
- **Report and Playoff Delta.** One constant each: `REPORT_VOICE` (`am_michael`) and
  `PD_VOICE` (`af_heart`).
- **Cards.** `host` and `narrator` (`cards-essay.ts:49-52`), borrowed from `CALL_VOICES.intro`
  and `.moved`.
- **Walk7.** asker and you, borrowed from `ESSAY_VOICES.asker`.
- **Who said the take.** The cut list records it only as `Shot.speaker?: string` (the model,
  absent for the owner; `cut-list.ts:206`) and `StillTake.owner?` (`stills.ts:60-73`).
- **The same voice under several names.** The literal `"am_michael"` is the tutor, the
  call's host and the report's voice. `"af_heart"` is the asker, Playoff Delta's host and the
  call's `moved` section voice.
- **No one place says "these are the roles, these are their voices".**

## 6. The emergent model as it is

```
                 [per kind]                               [shared]
 source JSON ──► scene union ──► StillScene[] ──┐
 (CallWeek, Essay,  (6 copies,     {id,file,said,│
  InterviewEssay,    Framing x4,    holdMs,       ├─► stillsCutList ──► cut-list/2 ──► renderer
  Report, PD fill,   framing seq x5) picture?}    │    + heldFor         (Shot: picture,   (captions from
  cards cut list)                                 │                       take{file,words}, words, loudness,
 speaker→voice map (5 shapes) ──► recordStills ───┘                       speaker?)         bed, burn-ins,
 take naming (4 + 2 in flight) ──► takeFilesOf ──► ownTake                                   compositions)
 transcript: inside essay JSON (routine)  |  beside take (walk7)
 server: voice note + verdict (shared) ──► rust_essays::takes (one, 2 kinds) | cards_essays (planned copy)
         render-calls.sh: one loop, 6 case tables x 8 jobs
```

| Node | Shared or per kind |
|---|---|
| voice note (audio + transcript + words + verdict) | **shared** server-side (`crates/db/voice`) |
| take (owner) as a render input | shared reader (`takeFilesOf`, `ownTake`); per-kind naming and mapping (`essayTakeOf`, `interviewTakeOf`, walk7) |
| Kokoro line | **shared** (`recordStills`/`takeOf`/`speakScene`); cards has a sibling `sayLines` |
| transcript | per kind: embedded in essay JSON (4 redeclared take-answer shapes); walk7 a file |
| verdict | **shared** (`hearingOf`, `Silence`) |
| words | 5 type definitions of the same triple |
| caption | **shared** (`render.ts` → burn-ins) |
| loudness / noise | **shared** (`plan.ts`); no denoise |
| picture | **shared** (`cut-list.ts:44`); #3316 extends it correctly |
| scene | per kind (6, walk7 7) |
| framing (intro/brand/chapter) | per kind (type x4, sequence x5); stage-side **shared** (`frame.tsx`) |
| speaker | per kind (5 shapes), no shared role type |
| template / format | **shared schema** (`show-format/1`), per-kind instance (correct) |
| essay / content | per kind (correct: this is content) |
| cut list | **shared** (`cut-list/2`) |
| render job | one loop, per-kind case arms (6 tables); file_host per-kind pollers with shared board |

## 7. Duplications and parallel paths, ranked by risk of silent drift

1. **How an owner's take and its transcript reach a render: 2 server exporters (1 live, 1
   planned) and 2 transcript channels.**
   - Live: `rust_essays::takes` (`rust_essays.rs:588-623`; transcript inside the essay by the
     routine).
   - Planned: server#1052's `cards_essays` export adds `.transcript.json`, with its own hold
     and refuse rules.
   - Walk7's `heardSpokenCard` (`spoken-card.ts:245`) reads the transcript beside the take.
   - Two rule sets decide "wait, refuse, set aside" for the same voice note. A change to one
     (a new verdict kind, a take deleted from My data) silently misses the other.
2. **The take-answer shape `{kind:"take", transcript} | Silence`: 4 copies, plus 3
   take-naming schemes and 2 more in flight.**
   - Copies at `essay.ts:419-427,441-448` and `interview-essay.ts:285-297,312-323`.
   - Ids: `essay.ts:122,695`, `interview-essay.ts:731-734`, walk7 `SPOKEN_TAKE_ID`, #3314
     `spoken:<card>.<part>`.
   - `takeFilesOf` keeps the refusals in one place, but which id plays where is per kind.
3. **Exchange (Kokoro asks, the owner answers): 2 schemas with different limits.**
   - `essay.ts:639` + `opening.ts:60,73` (3) against walk7 `cut-list.ts:158-209,171` (6).
   - The interview opening is a third shape (`interview-essay.ts:345`).
   - Plus the category list in 2 places: walk7 `cut-list.ts:158` and #3314
     `studio-spoken/model.ts:25`.
4. **Framing: `type Framing` x4, the framing sequence x5, the `xCutList` wrapper x5.**
   Locations are in §3. A change to the shape semantics (a new `brand.*` field, a chapter
   rule, a part split) has to be made five times. Only the call has parts (`call.ts:863`).
5. **The speaker-to-voice mapping: 5 shapes, with shared literals.**
   - `call.ts:928`, `essay.ts:1052`, `engagement-report-video.ts:72`,
     `playoff-delta/src/lib/voiced.ts:30` and `cards-essay.ts:49`.
   - The same Kokoro voice means different roles in different kinds, and nothing types a
     role.
6. **Joining takes: 3 implementations.** `speaker.ts:144`, `cards-essay.ts:290` and
   `apps/www/tests/record/cards.ts:80-131`. The gap must match `CHAPTER_GAP_MS` by
   convention.
7. **The stills recording loop: 2 copies (1 in flight).** `recordStills` (`voiced.ts:377`)
   against walk7's `spokenStills` (`apps/www/tests/record/cards.ts:236`). The second repeats
   `goto`, `shownFrame`, `fonts.ready`, `data-overflow` and the screenshot, but without the
   `scenes <n>`/`recorded <file>` progress lines.
8. **Kind lists across repos, 3 copies each.** Template ids (`templates.ts:37`,
   `previews.rs:73`, `render-calls.sh:293`) and the cards key (`cards-essay.ts:61`,
   `render-calls.sh:303`, `cards_essays/pass.rs:94`). Tests hold some of these, but they
   drift loudly only if tested.
9. **Word type: 5 definitions** (§2). Low risk, since the shape is trivial.
10. **Take-to-length rule: 2** (`stills.ts:129` and `soundbites/.../script.ts:66` via
    `timing.ts:14`). #3316's `ESSAY_ZOOM_FOOT = 372/1080` copies burn-ins' caption band
    height, held equal by a www test.

## 8. Where the code is already generic (keep it), and where it should stay granular

**Generic, correctly:**
- `cut-list/2`;
- `show-format/1`, plus `versionRefusal` (`format.ts:240`);
- `stillsCutList`/`heldFor`;
- `brandPicture` and composition pictures;
- `previewOf` (preview of any kind);
- `takeFilesOf` and `ownTake`;
- `hearingOf`, `Silence` and `UNHEARD_SAID`;
- the Kokoro path (`recordStills`, `takeOf`, `speakScene`, the step cache);
- captions (`render.ts` → burn-ins);
- loudness (`plan.ts`);
- `StageFrame`, `LockedIntro`, `BrandSlide`, `ChapterSlide`, template A's `Call`/`Bubble`;
- the server voice note and verdict;
- `rust_essays` `Kind`/`Spec` (two kinds, one exporter);
- the render worker's one loop, lane and policy;
- the Renders board.

**Granular, correctly (content):**
- each kind's data schema (what a ticket, question, board item or wing is);
- its judgements (marks, SOLO, faults, forks);
- its stage views (what a scene shows);
- its fit models (`call-fit.ts`, `essay-fit.ts`);
- its locked intro's wording;
- its chapter titles;
- its per-section text.

**Not voiced cut lists, correctly separate:** clip walks (stills plus `walk.json`) and promos
(compositions, no voice).

## 9. A compile-time-schema, content-dynamic graph: the minimal shared nodes

Smallest consolidations, as a list (not a plan):

1. **`Voice` / `Role`.** One typed role set (host, tutor, asker, owner, narrator…) and one
   role-to-Kokoro map. `owner` means "a take, never Kokoro". Replaces the 5 maps in §7.5.
2. **`Take`.** One `{kind:"take", id, transcript} | Silence` answer type with a single id
   grammar. Every kind's answers and exchanges reference it. Replaces the 4 answer copies and
   unifies the take ids.
3. **`Exchange`.** One `{ask: Sayable, take: TakeRef}` node, with the limit as policy per
   use. Shared by the essay opening, walk7's spoken card and #3314's parts (`ask` + part).
4. **`Framed<S>`.** One generic `framed(shape, intro, body, chapterOf)` producing
   intro/brand-in/chapter/…/brand-out, with one exported `Framing` type. Replaces the 4 type
   copies and 5 sequence copies.
5. **`feedCutList(format, title, scenes, takes)`.** One helper replacing the 5 `xCutList`
   wrappers. `stillsCutList` already takes almost exactly this.
6. **One take hand-off on home.** Generalize `rust_essays::takes` (and its
   Waiting/Deleted/unheard rules) into a shared `takes_for(subject, ids) → files` that writes
   `<id>.<ext>`, `<id>.words.json` and, if wanted, `<id>.transcript.json`. Cards then becomes
   a caller, not a copy (server#1052).
7. **One `joinTakes`.** Audio and words with an optional gap, used by both the Kokoro chunks
   and the cards' chapter and narration.
8. **One `TimedWord`** wire type, imported by burn-ins, heard and the recorder.
9. **One kind registry** (template ids, keys) generated or checked across the 3 places.

**In flight, adding a copy:**
- **walk7:** a 2nd exchange schema, a 2nd category list (with #3314), a 2nd transcript
  channel, a 2nd stills loop and a 7th scene union. It reuses `takeFilesOf`, `ownTake`,
  `hearingOf` and `ESSAY_VOICES` (`spoken-card.ts:30-36`), and its last commit "reuses the
  essays' stage".
- **server#1052:** a 2nd take exporter with its own hold and refuse rules.
- **#3314:** a 5th take-naming scheme (`spoken:<card>.<part>`) and a 2nd category list. It
  moved `phrasesOf` into `@some-ui/shared` (a dedup).
- **#3316:** **no copy.** It extends the shared `StillScene` with an optional composition
  `picture` and is usable by any kind (`zoom.ts`). Its only copy is the caption-band
  constant.
- **server#1051:** one more per-kind optional arm in `render-calls.sh`
  (`--week-file`, rust-essay only). No new copy of logic.
