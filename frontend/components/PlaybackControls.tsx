"use client"

import { useEffect, useState } from "react"

export default function PlaybackControls({
  onPlay,
  onPause,
  onSeek,
  onSync,
  currentTime,
  isPlaying,
}: {
  onPlay: () => void
  onPause: () => void
  onSeek: (time: number) => void
  onSync?: () => void
  currentTime: number
  isPlaying: boolean
}) {
  const safeTime = Number.isFinite(currentTime) ? currentTime : 0
  const [seekValue, setSeekValue] = useState(Math.round(safeTime))

  useEffect(() => {
    setSeekValue(Math.round(safeTime))
  }, [safeTime])

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button onClick={onPlay} className="btn btn-primary">
        Play
      </button>
      <button onClick={onPause} className="btn btn-outline">
        Pause
      </button>
      <div className="flex items-center gap-2">
        <input
          type="number"
          min={0}
          step={1}
          value={seekValue}
          onChange={(event) => setSeekValue(Number(event.target.value) || 0)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onSeek(Math.max(0, seekValue))
          }}
          className="input w-28"
        />
        <button
          onClick={() => onSeek(Math.max(0, seekValue))}
          className="btn btn-ghost"
        >
          Seek
        </button>
      </div>
      <div className="text-xs text-[color:var(--color-muted)]">
        {isPlaying ? "Playing" : "Paused"} at {safeTime.toFixed(1)}s
      </div>
      {onSync ? (
        <button onClick={onSync} className="btn btn-ghost">
          Sync
        </button>
      ) : null}
    </div>
  )
}
