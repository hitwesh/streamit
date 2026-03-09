"use client"

import { sendMessage } from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"

interface ControlsProps {
  roomCode: string
}

export default function Controls({ roomCode: _ }: ControlsProps) {
  // Host-only rendering will be gated here once auth state is wired
  const playbackTime = useRoomStore((s) => s.playback.time)

  return (
    <div className="flex items-center justify-center gap-4 h-full">
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
    </div>
  )
}
