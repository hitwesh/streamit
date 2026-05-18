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

    if (provider === "vidking") {
      if (mediaType === "tv") {
        if (!season || !episode) return ""
        const params = new URLSearchParams({ autoPlay: "true" })
        return `https://www.vidking.net/embed/tv/${videoId}/${season}/${episode}?${params.toString()}`
      }

      const params = new URLSearchParams({ autoPlay: "true" })
      return `https://www.vidking.net/embed/movie/${videoId}?${params.toString()}`
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
      <div className="flex h-full w-full items-center justify-center rounded-3xl border border-dashed border-black/10 bg-white/70 text-sm text-[color:var(--color-muted)]">
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
        frameBorder={0}
        title="StreamIt player"
      />
    </div>
  )
}
