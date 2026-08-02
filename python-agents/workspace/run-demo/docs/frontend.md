# Frontend Summary

## State Management
No framework state is needed. A small DOMContentLoaded handler appends extra star elements if JavaScript runs; the core experience is pure HTML/CSS so it degrades gracefully when scripts are disabled.

## Accessibility Notes
- Semantic `<main>` landmark.
- `aria-hidden="true"` on the decorative star container.
- Sufficient color contrast between poem text and background.
- Responsive sizing using `clamp()` and `min()` so the card fits narrow screens.

## User Configuration
```json
{
  "star_count": 24,
  "animation_speed_seconds": 3.5
}
```
