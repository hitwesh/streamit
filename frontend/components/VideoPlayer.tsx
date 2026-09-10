"use client"

import { useEffect, useMemo, useRef } from "react"
import { useRoomStore } from "@/store/roomStore"

export default function VideoPlayer({
  provider,
  videoId,
  mediaType = "movie",
  season,
  episode,
}: {
  provider: string
  videoId: string
  mediaType?: "movie" | "tv"
  season?: number | null
  episode?: number | null
}) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const { is_playing, time } = useRoomStore((s) => s.playback)

  const src = useMemo(() => {
    if (!provider || !videoId) return ""

    if (provider === "vidphantom") {
      if (mediaType === "tv") {
        if (!season || !episode) return ""
        return `https://vidphantom.com/tv/${videoId}/${season}/${episode}?autoplay=false&poster=true`
      }

      return `https://vidphantom.com/movie/${videoId}?autoplay=false&poster=true`
    }

    return ""
  }, [provider, videoId, mediaType, season, episode])

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    // Placeholder: sync will be wired once the player exposes a postMessage API.
    // Current store values are retained for future control.
    void is_playing
    void time
  }, [is_playing, time])

  if (!src) {
    return (
      <div className="flex h-full w-full items-center justify-center border border-dashed border-white/10 bg-black/60 text-sm text-[color:var(--color-muted)]">
        No media selected yet.
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <iframe
        ref={iframeRef}
        src={src}
        width="100%"
        height="100%"
        allowFullScreen
        allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
        sandbox="allow-presentation allow-same-origin allow-scripts"
        referrerPolicy="no-referrer"
        loading="lazy"
        frameBorder={0}
        title="StreamIt player"
      />
    </div>
  )
}
