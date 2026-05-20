# 0011 - User Local Date Filters

## Status

Accepted on 2026-05-21.

## Context

Prompteer stores server timestamps in UTC, but users reason about calendar days in their own timezone. A `date=2026-05-20` filter must not be treated as midnight-to-midnight UTC unless the user's timezone is UTC.

## Decision

Date-filtered API routes accept an IANA timezone alongside the local date. The API converts that local calendar day into a UTC `[start_at, end_at)` window, filters persisted UTC timestamps with that window, and returns the normalized window in the response.

The community board is the first route to use this pattern through `date` and `timezone` query parameters.

## Consequences

Clients can round-trip local dates without guessing offset math. Tests pin a Los Angeles date window around May 20, 2026, including the UTC boundary values. Invalid timezone names return RFC 9457 Problem Details with `code: "invalid_timezone"`.

## Alternatives considered

Filtering by raw UTC date was simpler, but it would shift results for users outside UTC. Accepting numeric offsets was rejected because IANA zones handle daylight saving transitions correctly.
