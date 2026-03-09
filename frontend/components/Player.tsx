"use client"

import ReactPlayer from "react-player"
import { useEffect, useRef } from "react"
import { useRoomStore } from "@/store/roomStore"

interface PlayerProps {
  roomCode: string
}

export default function Player({ roomCode: _ }: PlayerProps) {
  const playerRef = useRef<ReactPlayer | null>(null)
  const { is_playing, time } = useRoomStore((s) => s.playback)
  const demoStreamUrl = process.env.NEXT_PUBLIC_DEMO_STREAM_URL

  useEffect(() => {
    const player = playerRef.current
    if (!player) return

    const current = player.getCurrentTime()
    const drift = Math.abs(current - time)

    // Keep clients aligned with server-authoritative playback state.
    if (drift > 2) {
      player.seekTo(time, "seconds")
    }
  }, [time])

  if (!demoStreamUrl) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-black text-zinc-200">
        <div className="text-center space-y-2">
          <p className="text-lg font-semibold">Player Ready</p>
          <p className="text-sm text-zinc-400">
            Set `NEXT_PUBLIC_DEMO_STREAM_URL` to render video.
          </p>
          <p className="text-xs text-zinc-500">
            Playback: {is_playing ? "playing" : "paused"} @ {time.toFixed(1)}s
          </p>
        </div>
      </div>
    )
  }

  return (
    <ReactPlayer
      ref={playerRef}
      url={demoStreamUrl}
      playing={is_playing}
      width="100%"
      height="100%"
      controls={false}
    />
  )
}
