"use client"

import { useEffect, useRef } from "react"
import { useRoomStore } from "@/store/roomStore"

export default function VideoPlayer({ videoId }: { videoId: string }) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const { is_playing, time } = useRoomStore((s) => s.playback)

  const src = `https://www.vidking.net/embed/movie/${videoId}?autoPlay=true`

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    // Placeholder: sync will be wired once the player exposes a postMessage API.
    // Current store values are retained for future control.
    void is_playing
    void time
  }, [is_playing, time])

  return (
    <div className="h-full w-full">
      <iframe
        ref={iframeRef}
        src={src}
        width="100%"
        height="100%"
        allowFullScreen
        frameBorder={0}
      />
    </div>
  )
}
