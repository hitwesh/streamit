"use client"

import ReactPlayer from "react-player"

interface PlayerProps {
  roomCode: string
}

export default function Player({ roomCode: _ }: PlayerProps) {
  // roomCode will be used when play/pause/seek sync is wired via Zustand state
  return (
    <ReactPlayer
      url="https://example-stream-url"
      width="100%"
      height="100%"
      controls={false}
    />
  )
}
