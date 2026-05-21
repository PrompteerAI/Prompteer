# 0018 — Challenge Media Reference Read Contract

## Status

Accepted on 2026-05-21.

## Context

The domain model already stores image and video challenge reference rows, and
the seed data creates representative media references. The public challenge API
only returned common challenge fields, so frontend clients could list image and
video challenges but could not distinguish or preview their reference assets in
a typed way.

## Decision

Expose a read-only `references` array on `ChallengeRead`. Image references and
video references use a discriminated union with `kind: "img"` or
`kind: "video"`, `file_path`, and `file_type`. Problem-solving challenges return
an empty array.

This is intentionally a read contract only. Media serving, uploads, generated
image/video outputs, likes, and gallery behavior remain separate contracts.

## Consequences

Frontend clients can safely build read-only image/video challenge pages without
guessing from database table shape or legacy path conventions. The generated
OpenAPI TypeScript types now carry the discriminated union, and future media
delivery work can extend the schema with stable browser URLs without breaking
the current reference metadata.

## Alternatives considered

The API could have waited until full media generation was implemented, but that
would block incremental frontend work despite the reference data already being
available. Returning ad hoc `image_reference` and `video_reference` fields was
rejected because it would make shared challenge UI harder to type and evolve.
