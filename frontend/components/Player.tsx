"use client"

import ReactPlayer from "react-player"
import { useRoomStore } from "@/store/roomStore"

interface PlayerProps {
  roomCode: string
}

export default function Player({ roomCode: _ }: PlayerProps) {
  const { is_playing } = useRoomStore((s) => s.playback)

  return (
    <ReactPlayer
      url="https://example-stream-url"
      playing={is_playing}
      width="100%"
      height="100%"
      controls={false}
    />
  )
}
