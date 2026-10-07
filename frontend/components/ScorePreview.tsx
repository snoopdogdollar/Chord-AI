import type { SheetResponse } from "@/services/api";

export function ScorePreview({ sheet }: { sheet: SheetResponse | null }) {
  if (!sheet?.pages?.length) {
    return (
      <div className="flex min-h-[440px] items-center justify-center rounded border border-dashed border-staff bg-paper p-8 text-center text-sm text-slate-500">
        Analyze audio to see your chord sheet with staff notation and bar lines.
      </div>
    );
  }

  return (
    <div>
      <p className="mb-3 text-xs text-slate-600">{sheet.notice}</p>
      <div className="max-h-[800px] space-y-4 overflow-auto rounded bg-paper p-3" aria-label="Chord sheet preview">
        {sheet.pages.map((svg, index) => (
          <figure key={index} className="min-w-[540px] bg-white shadow-sm">
            {/* An image keeps the generated SVG inert and preserves vector sharpness. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`}
              alt={`${sheet.title} - chord accompaniment, page ${index + 1} of ${sheet.pages.length}`}
              className="block h-auto w-full"
              width={595}
              height={842}
            />
            <figcaption className="pb-3 text-center text-xs text-slate-500">
              Page {index + 1} of {sheet.pages.length}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
