"use client"

import { sendMessage } from "@/lib/websocket"

interface ControlsProps {
  roomCode: string
}

export default function Controls({ roomCode: _ }: ControlsProps) {
  // roomCode will be used when host-only rendering is wired via Zustand state.
  // time defaults to 0 until current player time is read from shared state.

  return (
    <div className="flex items-center justify-center gap-4 h-full">
      <button
        onClick={() => sendMessage({ type: "PLAY", time: 0 })}
        className="px-4 py-2 bg-green-600 text-white rounded"
      >
        Play
      </button>
      <button
        onClick={() => sendMessage({ type: "PAUSE", time: 0 })}
        className="px-4 py-2 bg-yellow-500 text-white rounded"
      >
        Pause
      </button>
    </div>
  )
}
