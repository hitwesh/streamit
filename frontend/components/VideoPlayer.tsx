"use client"

import { useEffect, useMemo, useRef, useCallback } from "react"
import { useRoomStore } from "@/store/roomStore"
import type { PlayerEventData } from "@/lib/websocket"

interface VideoPlayerProps {
  provider: string
  videoId: string
  mediaType?: "movie" | "tv"
  season?: number | null
  episode?: number | null
  isHost?: boolean
  isSoloMode?: boolean
  onHostPlay?: (time: number) => void
  onHostPause?: (time: number) => void
  onHostSeek?: (time: number) => void
  onPlayerEvent?: (data: PlayerEventData) => void
}

export default function VideoPlayer({
  provider,
  videoId,
  mediaType = "movie",
  season,
  episode,
  isHost = false,
  isSoloMode = false,
  onHostPlay,
  onHostPause,
  onHostSeek,
  onPlayerEvent,
}: VideoPlayerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const { is_playing, time, version } = useRoomStore((s) => s.playback)

  const localTimeRef = useRef(0)
  const lastReportedHostTime = useRef(0)
  const lastProgressReportRef = useRef(0)
  const prevSoloModeRef = useRef(isSoloMode)
  const iframeReadyRef = useRef(false)

  const src = useMemo(() => {
    if (!provider || !videoId) return ""

    if (provider === "embed-api") {
      if (mediaType === "tv") {
        if (!season || !episode) return ""
        return `https://watch.embed-api.stream/embed/tv/${videoId}/${season}/${episode}`
      }

      return `https://watch.embed-api.stream/embed/movie/${videoId}`
    }

    if (provider === "superembed") {
      const base = `https://multiembed.mov/?video_id=${videoId}&tmdb=1`
      if (mediaType === "tv") {
        if (!season || !episode) return ""
        return `${base}&s=${season}&e=${episode}`
      }
      return base
    }

    return ""
  }, [provider, videoId, mediaType, season, episode])

  const sendToIframe = useCallback(
    (message: { command: "play" | "pause" } | { command: "seek"; time: number }) => {
      const iframe = iframeRef.current
      if (!iframe?.contentWindow) return

      iframe.contentWindow.postMessage(
        {
          source: "streamframe-parent",
          ...message,
        },
        "*"
      )
    },
    []
  )

  // Listen for streamframe events emitted from inside the Embed API iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (!event.data || typeof event.data !== "object") return
      if (event.data.source !== "streamframe") return

      iframeReadyRef.current = true
      const { event: streamEvent, currentTime = 0, duration = 0 } = event.data
      localTimeRef.current = currentTime

      if (isHost) {
        if (streamEvent === "play") {
          lastReportedHostTime.current = currentTime
          onHostPlay?.(currentTime)
        } else if (streamEvent === "pause") {
          lastReportedHostTime.current = currentTime
          onHostPause?.(currentTime)
        } else if (streamEvent === "timeupdate") {
          const delta = Math.abs(currentTime - lastReportedHostTime.current)
          // A jump greater than 2s indicates a manual seek/skip inside the player
          if (delta > 2.0) {
            lastReportedHostTime.current = currentTime
            onHostSeek?.(currentTime)
          } else {
            lastReportedHostTime.current = currentTime
          }

          // Throttle progress telemetry reporting to every ~5s
          if (Math.abs(currentTime - lastProgressReportRef.current) >= 5) {
            lastProgressReportRef.current = currentTime
            const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 1
            const progress = Math.min(100, Math.max(0, (currentTime / safeDuration) * 100))
            onPlayerEvent?.({
              event: "timeupdate",
              currentTime,
              duration: safeDuration,
              progress,
            })
          }
        } else if (streamEvent === "ended") {
          const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 1
          onPlayerEvent?.({
            event: "ended",
            currentTime: safeDuration,
            duration: safeDuration,
            progress: 100,
          })
        }
      } else if (!isSoloMode) {
        // Continuous sync correction for viewer
        if (streamEvent === "play" && !is_playing) {
          // If host is paused, force viewer pause
          sendToIframe({ command: "pause" })
        } else if (streamEvent === "pause" && is_playing) {
          // If host is playing, force viewer play
          sendToIframe({ command: "play" })
        }

        const drift = Math.abs(currentTime - time)
        if (drift > 2.5 && time > 0) {
          sendToIframe({ command: "seek", time })
        }
      }
    }

    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [isHost, isSoloMode, is_playing, time, onHostPlay, onHostPause, onHostSeek, onPlayerEvent, sendToIframe])

  // Synchronize viewer iframe with host playback state when NOT in Solo Mode
  useEffect(() => {
    if (isHost || isSoloMode) return

    // Apply play/pause state
    sendToIframe({ command: is_playing ? "play" : "pause" })

    // If drift is significant or version changed (explicit seek from host), seek viewer player
    const drift = Math.abs(localTimeRef.current - time)
    if (drift > 2) {
      localTimeRef.current = time
      sendToIframe({ command: "seek", time })
    }
  }, [isHost, isSoloMode, is_playing, time, version, sendToIframe])

  // When switching from Solo Mode back to Synced Mode, instantly re-align to host
  useEffect(() => {
    if (!isHost && prevSoloModeRef.current && !isSoloMode) {
      sendToIframe({ command: "seek", time })
      sendToIframe({ command: is_playing ? "play" : "pause" })
    }
    prevSoloModeRef.current = isSoloMode
  }, [isHost, isSoloMode, time, is_playing, sendToIframe])

  // Align newly loaded iframe with active playback state for late joiners
  const handleIframeLoad = () => {
    iframeReadyRef.current = true
    if (!isHost && !isSoloMode && time > 0) {
      setTimeout(() => {
        sendToIframe({ command: "seek", time })
        if (is_playing) {
          sendToIframe({ command: "play" })
        }
      }, 1000)
    }
  }

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
        onLoad={handleIframeLoad}
        width="100%"
        height="100%"
        allowFullScreen
        allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
        referrerPolicy="no-referrer"
        frameBorder={0}
        title="StreamIt player"
      />
    </div>
  )
}
