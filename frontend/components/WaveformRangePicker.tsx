"use client";

import { useEffect, useRef, useState } from "react";
import type WaveSurfer from "wavesurfer.js";
import type RegionsPlugin from "wavesurfer.js/dist/plugins/regions";
import type { Region } from "wavesurfer.js/dist/plugins/regions";
import type { AnalysisRange } from "@/services/api";

type WaveformRangePickerProps = {
  file: File;
  disabled?: boolean;
  onRangeChange: (range: AnalysisRange | null) => void;
};

function formatSeconds(seconds: number): string {
  const safeSeconds = Math.max(0, seconds);
  const minutes = Math.floor(safeSeconds / 60);
  const remainingSeconds = Math.floor(safeSeconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function toRange(region: Region): AnalysisRange {
  return {
    start: Number(region.start.toFixed(3)),
    end: Number(region.end.toFixed(3))
  };
}

export function WaveformRangePicker({ file, disabled = false, onRangeChange }: WaveformRangePickerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const activeRegionRef = useRef<Region | null>(null);
  const [duration, setDuration] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [range, setRange] = useState<AnalysisRange | null>(null);

  useEffect(() => {
    let isCancelled = false;
    const objectUrl = URL.createObjectURL(file);

    setDuration(0);
    setIsReady(false);
    setIsPlaying(false);
    setRange(null);
    onRangeChange(null);

    async function createWaveform() {
      const [{ default: WaveSurferModule }, { default: RegionsModule }] = await Promise.all([
        import("wavesurfer.js"),
        import("wavesurfer.js/dist/plugins/regions")
      ]);

      if (isCancelled || !containerRef.current) {
        URL.revokeObjectURL(objectUrl);
        return;
      }

      const regions = RegionsModule.create();
      const waveSurfer = WaveSurferModule.create({
        container: containerRef.current,
        url: objectUrl,
        height: 96,
        waveColor: "#d7cdc0",
        progressColor: "#2f7f73",
        cursorColor: "#1f2933",
        cursorWidth: 2,
        barWidth: 2,
        barGap: 2,
        barRadius: 2,
        dragToSeek: true,
        normalize: true,
        plugins: [regions]
      });

      waveSurferRef.current = waveSurfer;
      regionsRef.current = regions;

      function updateRange(region: Region) {
        activeRegionRef.current = region;
        const nextRange = toRange(region);
        setRange(nextRange);
        onRangeChange(nextRange);
      }

      regions.enableDragSelection(
        {
          color: "rgba(47, 127, 115, 0.24)",
          drag: true,
          resize: true,
          minLength: 1
        },
        10
      );

      regions.on("region-created", (region) => {
        for (const existingRegion of regions.getRegions()) {
          if (existingRegion.id !== region.id) {
            existingRegion.remove();
          }
        }
        updateRange(region);
      });

      regions.on("region-updated", updateRange);

      regions.on("region-clicked", (region, event) => {
        event.stopPropagation();
        region.play(true);
      });

      waveSurfer.on("ready", (audioDuration) => {
        setDuration(audioDuration);
        setIsReady(true);
        regions.clearRegions();
        updateRange(
          regions.addRegion({
            start: 0,
            end: audioDuration,
            color: "rgba(47, 127, 115, 0.24)",
            drag: true,
            resize: true,
            minLength: 1
          })
        );
      });

      waveSurfer.on("play", () => setIsPlaying(true));
      waveSurfer.on("pause", () => setIsPlaying(false));
      waveSurfer.on("finish", () => setIsPlaying(false));
    }

    void createWaveform();

    return () => {
      isCancelled = true;
      activeRegionRef.current = null;
      regionsRef.current = null;
      waveSurferRef.current?.destroy();
      waveSurferRef.current = null;
      URL.revokeObjectURL(objectUrl);
    };
  }, [file, onRangeChange]);

  function onPlayPause() {
    const waveSurfer = waveSurferRef.current;
    if (!waveSurfer || disabled || !isReady) {
      return;
    }

    if (waveSurfer.isPlaying()) {
      waveSurfer.pause();
      return;
    }

    const activeRegion = activeRegionRef.current;
    if (activeRegion) {
      activeRegion.play(true);
      return;
    }

    void waveSurfer.play();
  }

  return (
    <div className="mt-4 space-y-3">
      <div ref={containerRef} className="min-h-24 overflow-hidden rounded border border-staff bg-paper" />
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600">
        <button
          className="rounded border border-staff bg-white px-3 py-2 text-sm font-semibold text-ink"
          type="button"
          disabled={disabled || !isReady}
          onClick={onPlayPause}
        >
          {isPlaying ? "Pause" : "Play"}
        </button>
        <span>
          {range ? `${formatSeconds(range.start)} - ${formatSeconds(range.end)}` : "0:00 - 0:00"}
          {duration ? ` / ${formatSeconds(duration)}` : ""}
        </span>
      </div>
    </div>
  );
}
