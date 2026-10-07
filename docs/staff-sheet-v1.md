# Staff chord sheet v1

The result panel now shows a paginated A4 chord accompaniment score and a Download PDF action.
Five-line staves, a treble clef, estimated 4/4 measures, chord symbols, beat slashes, bar numbers,
and an ending double bar replace the plain-text presentation. No melody, lyrics, key signature,
repeat structure, or song sections are inferred. Slashes are accompaniment guides, not detected notes.
`N.C.` means no chord / unknown, including gaps in the detected chord timeline.

## Timing

New analyses retain a structured version-2 score in the existing `GeneratedSheet.content` text
column. Detected beat timestamps determine fractional chord positions. The grid extends to cover
leading and trailing audio. Grouping every four beats into bars is an explicit assumption:
the detector does not identify meter, downbeats, pickups, or meter changes. The last bar may be partial.
Chords continuing across bars are repeated at each bar start so each system is readable independently.

Existing text sheets are adapted on read from saved chord events, duration, and BPM. No schema
migration or audio re-analysis is required. Missing beat timestamps use a constant tempo grid;
missing tempo uses a clearly labeled 120 BPM guide. These fallbacks do not assert a detected tempo.

## Rendering and compatibility

`sheets/score.py` builds the score without changing DSP or detection. `sheets/notation.py` supplies
one vector layout shared by SVG previews and ReportLab PDF export. SVG is displayed as an inert
image in the frontend. PDF embeds the bundled OFL Noto Sans font for Vietnamese titles; preview
text uses the browser's sans-serif font. Dense chord changes receive more room and additional label
lanes. Long scores paginate; titles and notation are repeated on subsequent pages.

`GET /songs/{id}/sheet` adds `title`, `notice`, and `pages` (SVG strings). The existing `sections`
field and TXT export endpoint remain available for API compatibility, but TXT is no longer an action
in the UI. PDF and TXT remain the only downloadable export formats. Routes remain thin, and audio
processing still runs in the existing background pipeline.

## Validation

Run `python -m pytest tests` from `backend` using the project interpreter, and `npx tsc --noEmit`
plus `npm run build` from `frontend`. Score tests cover variable beats, boundary changes, sustained
chords, gaps, partial bars, fallback timing, Unicode/escaped titles, dense changes, and pagination.
API tests cover previews and PDF/TXT downloads for both legacy and version-2 records; a mocked
pipeline test checks beat data persistence. Visual QA should include a multi-page PDF, a dense
score, an empty result, and a browser preview. Real-audio detection quality is outside this change.
