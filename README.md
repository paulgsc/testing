# Published data for some-ui's stages

Three sets of data, each read by `paulgsc/some-ui`: Playoff Delta's season,
the weekly call's weeks, and each release promo's fill and sample.

## Playoff Delta

The weekly numbers behind the Playoff Delta vlog: one NFL team's
regular-season story, as the JSON that `paulgsc/some-ui`'s
`@some-ui/playoff-delta` stage renders (`story.ts`, contract version 1).

Nothing here is written by hand. `.github/workflows/playoff-delta.yml` runs
every Tuesday in season: it fetches ESPN's scoreboards
(`scripts/fetch-espn.sh`), builds and runs `paulgsc/server`'s
`playoff-delta` job (`apps/playoff_delta_job`, math in
`crates/playoff_delta`), and commits the result when a week has closed. Run
it by hand from the Actions tab ("Run workflow").

## Files

| Path | What |
|---|---|
| `playoff-delta/<season>/<team>.json` | The story so far: one entry per completed week the team played |
| `playoff-delta/<season>/narration/<team>-week-NN.json` | What is said over each scene of week NN's episode (`some-ui.pd-narration/1`); week 00 is the legend |
| `playoff-delta/index.json` | Every fill above, by season, team and week, with its file's SHA-256 (`some-ui.pd-narration-index/1`): what home reads to keep each one |

## Narration

What is said over each Playoff Delta episode is written here by a scheduled
session each Tuesday in season, after the week's data lands, following
`packages/ui/playoff-delta/NARRATION-ROUTINE.md` in `paulgsc/some-ui`. It
fills the weeks due (the legend once, then each new week), checks every
fill with `pnpm --filter @some-ui/playoff-delta narration check` before it
lands, rewrites `playoff-delta/index.json` with `narration index`, and never
edits a fill already here. Home reads the index hourly and keeps every fill,
with its season file as served, for good. Each fill is pinned to the
season up to its week, so it still checks as later weeks are added.

## Fetching

```
https://raw.githubusercontent.com/paulgsc/testing/main/playoff-delta/2026/SF.json
```

Served with `Access-Control-Allow-Origin: *`, so a browser app can fetch it
directly. GitHub caches it for about five minutes.

## The weekly call

The agents' weekly stand-up for the owner (`paulgsc/some-ui`,
`packages/video-render/src/call.ts`): one week's data per file, which
`/call` plays and the owner's home voices and renders. A scheduled session
writes each week on Fridays (`packages/video-render/CALL-ROUTINE.md` in
`paulgsc/some-ui`), checked against the call's schema before it lands.

| Path | What |
|---|---|
| `call/index.json` | The weeks kept here, newest first, at most `keep` |
| `call/<from>.json` | One week's call (`some-ui.call-week/1`), named for its first day |

Only the last `keep` weeks stay here. Home keeps every week, and a week
leaves this repository only once home holds it, so the full record is
home's.

```
https://raw.githubusercontent.com/paulgsc/testing/main/call/index.json
```

## Release promos

A 9:16 vertical for a release of one of the apps or extensions
(`paulgsc/some-ui`, `packages/video-motion`, HYPER3): the app walked in a
sandbox that holds only the sample below, drawn in three HyperFrames scenes
and rendered on home. The template is code; per release, a session writes
only the words, checked against the template before they land.

| Path | What |
|---|---|
| `promo/<app>/<version>/release.json` | The release and the words drawn over it (`some-ui.promo/1`) |
| `promo/<app>/<version>/sample.json` | What the app shows in the sandbox walk, made up (`some-ui.walk-sample/<app>/1`) |

On home, from `paulgsc/server` (its Makefile's `promo` target):

```
make promo APP=suspender-ledger VERSION=0.3.1
```
