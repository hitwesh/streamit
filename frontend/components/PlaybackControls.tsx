"use client"

export default function PlaybackControls({
  onPlay,
  onPause,
  onSeek,
}: {
  onPlay: () => void
  onPause: () => void
  onSeek: (time: number) => void
}) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onPlay}
        className="px-3 py-2 bg-green-600 text-white rounded"
      >
        Play
      </button>
      <button
        onClick={onPause}
        className="px-3 py-2 bg-yellow-500 text-white rounded"
      >
        Pause
      </button>
      <button
        onClick={() => onSeek(120)}
        className="px-3 py-2 bg-blue-600 text-white rounded"
      >
        Seek 2:00
      </button>
    </div>
  )
}
