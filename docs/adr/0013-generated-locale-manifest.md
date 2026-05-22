# 0013 - Generated Locale Manifest

## Status

Accepted on 2026-05-21.

## Context

Prompteer ships English only at launch, but the web app should be ready for a
new locale by adding one complete JSON message file. The previous
`next-intl` routing configuration hard-coded `["en"]`, so adding a locale also
required source edits.

## Decision

Generate the web locale manifest from `apps/web/src/messages/*.json` before
web dev, build, lint, typecheck, test, e2e, and Docker build commands. The
generated manifest feeds `defineRouting`, request message loading, navigation,
and redirect helpers.

The generator validates locale file names, requires `en.json`, and compares
message keys against English so incomplete locale files fail early.

## Consequences

Adding a locale is now a message-file operation: drop
`apps/web/src/messages/<locale>.json` and run the normal web command. The
generated TypeScript file is ignored by Git because it is derived state.

Every build environment must run the generator before invoking Next.js; package
scripts and the web Dockerfile both do that.

## Alternatives considered

Keeping `routing.locales` hand-written was simpler but made locale additions
code changes. Loading locales with filesystem APIs at runtime was rejected
because the routing config also runs in Next.js proxy code where filesystem
access is not appropriate.
