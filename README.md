# Playoff Delta data

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
