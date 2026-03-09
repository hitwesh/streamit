"use client"

import { useEffect, useState } from "react"
import { sendMessage } from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"

interface ControlsProps {
  roomCode: string
}

export default function Controls({ roomCode: _ }: ControlsProps) {
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
        className="px-4 py-2 bg-green-600 text-white rounded"
      >
        Play
      </button>
      <button
        onClick={() => sendMessage({ type: "PAUSE", time: playbackTime })}
        className="px-4 py-2 bg-yellow-500 text-white rounded"
      >
        Pause
      </button>
      <input
        type="number"
        min={0}
        step={1}
        value={Number.isFinite(seekTime) ? seekTime : 0}
        onChange={(e) => setSeekTime(Number(e.target.value) || 0)}
        className="w-28 border rounded px-2 py-2"
      />
      <button
        onClick={sendSeek}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Seek
      </button>
    </div>
  )
}
