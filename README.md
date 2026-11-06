# Published data for some-ui's stages

Two sets of data, each fetched by a stage in `paulgsc/some-ui`:
Playoff Delta's season, and the weekly call's weeks.

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
