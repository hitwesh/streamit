"use client"

import { useEffect, useState } from "react"
import { sendMessage } from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"

export default function Controls() {
  // Host-only rendering will be gated here once auth state is wired
  const playbackTime = useRoomStore((s) => s.playback.time)
  const [seekTime, setSeekTime] = useState(0)

  // Keep seek input aligned with latest server playback state.
  useEffect(() => {
    setSeekTime(playbackTime)
  }, [playbackTime])

  const sendSeek = () => {
    const clamped = Math.max(0, seekTime)
    sendMessage({ type: "SEEK", time: clamped })
  }

  return (
    <div className="flex items-center justify-center gap-4 h-full px-4">
      <button
        onClick={() => sendMessage({ type: "PLAY", time: playbackTime })}
        className="btn btn-primary"
      >
        Play
      </button>
      <button
        onClick={() => sendMessage({ type: "PAUSE", time: playbackTime })}
        className="btn btn-outline"
      >
        Pause
      </button>
      <input
        type="number"
        min={0}
        step={1}
        value={Number.isFinite(seekTime) ? seekTime : 0}
        onChange={(e) => setSeekTime(Number(e.target.value) || 0)}
        className="input w-28"
      />
      <button
        onClick={sendSeek}
        className="btn btn-ghost"
      >
        Seek
      </button>
    </div>
  )
}
