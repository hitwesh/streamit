"use client"

import ReactPlayer from "react-player"
import { useCallback, useEffect, useRef } from "react"
import { useRoomStore } from "@/store/roomStore"
import type { PlayerEventData } from "@/lib/websocket"

interface PlayerProps {
  onPlayerEvent?: (data: PlayerEventData) => void
  isHost?: boolean
}

export default function Player({ onPlayerEvent, isHost = false }: PlayerProps) {
  const playerRef = useRef<ReactPlayer | null>(null)
  const lastProgressRef = useRef(0)
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

  const sendPlayerEvent = useCallback(
    (data: PlayerEventData) => {
      if (!isHost || !onPlayerEvent) return
      onPlayerEvent(data)
    },
    [isHost, onPlayerEvent]
  )

  const buildProgressPayload = useCallback(
    (event: PlayerEventData["event"], current: number, duration: number) => {
      const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 1
      const progress = Math.min(100, Math.max(0, (current / safeDuration) * 100))

      return {
        event,
        currentTime: current,
        duration: safeDuration,
        progress,
      } as PlayerEventData
    },
    []
  )

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
      onProgress={({ playedSeconds }) => {
        if (!isHost) return
        const now = Math.floor(playedSeconds)
        if (now - lastProgressRef.current < 5) return
        lastProgressRef.current = now

        const duration = playerRef.current?.getDuration() ?? 0
        sendPlayerEvent(buildProgressPayload("timeupdate", playedSeconds, duration))
      }}
      onPause={() => {
        if (!isHost) return
        const current = playerRef.current?.getCurrentTime() ?? 0
        const duration = playerRef.current?.getDuration() ?? 0
        sendPlayerEvent(buildProgressPayload("pause", current, duration))
      }}
      onSeek={(seconds) => {
        if (!isHost) return
        const duration = playerRef.current?.getDuration() ?? 0
        sendPlayerEvent(buildProgressPayload("seeked", seconds, duration))
      }}
      onEnded={() => {
        if (!isHost) return
        const duration = playerRef.current?.getDuration() ?? 0
        sendPlayerEvent({
          event: "ended",
          currentTime: duration,
          duration,
          progress: 100,
        })
      }}
    />
  )
}
