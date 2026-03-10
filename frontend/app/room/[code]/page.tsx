"use client"

import { useEffect } from "react"
import { useParams } from "next/navigation"
import {
  connectToRoom,
  disconnectSocket,
  addMessageHandler,
  sendMessage,
  type ServerEvent,
} from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"
import VideoPlayer from "@/components/VideoPlayer"
import PlaybackControls from "@/components/PlaybackControls"
import Chat from "@/components/Chat"
import ParticipantList from "@/components/ParticipantList"

export default function RoomPage() {
  const params = useParams<{ code: string }>()
  const roomCode = params?.code ?? ""

  useEffect(() => {
    if (!roomCode) return

    const token = localStorage.getItem("token") ?? ""
    connectToRoom(roomCode, token)

    const unsubscribe = addMessageHandler((event: ServerEvent) => {
      // useRoomStore.getState() is the correct way to access the store
      // outside of a React render (i.e. inside a plain callback).
      const store = useRoomStore.getState()

      switch (event.type) {
        case "CHAT_HISTORY":
          store.loadChatHistory(event.messages)
          break

        case "CHAT_MESSAGE":
          // Backend broadcast omits created_at — generate client-side
          store.addMessage({
            user: event.user,
            message: event.message,
            created_at: new Date().toISOString(),
          })
          break

        case "PLAYBACK_STATE":
          store.setPlayback({
            time: event.time,
            is_playing: event.is_playing,
            version: event.version,
          })
          break

        case "ROOM_PARTICIPANTS":
          store.setParticipants(event.participants, event.host)
          break

        case "USER_JOINED":
          store.addParticipant(event.user)
          break

        case "USER_LEFT":
          store.removeParticipant(event.user)
          break

        case "SYNC_CORRECTION":
          store.setPlayback({
            ...store.playback,
            time: event.time,
            version: event.version,
          })
          break

        case "HOST_DISCONNECTED":
          console.warn("[WS] host disconnected — grace period:", event.grace_seconds, "s")
          break

        case "HOST_RECONNECTED":
          console.log("[WS] host reconnected")
          break

        case "ROOM_DELETED":
          console.warn("[WS] room deleted")
          break

        case "ERROR":
          console.error("[WS] error:", event.message)
          break
      }
    })

    return () => {
      unsubscribe()
      disconnectSocket()
    }
  }, [roomCode])

  const playbackTime = useRoomStore((s) => s.playback.time)
  const participants = useRoomStore((s) => s.participants)
  const host = useRoomStore((s) => s.host)

  const handlePlay = () => {
    sendMessage({ type: "PLAY", time: playbackTime })
  }

  const handlePause = () => {
    sendMessage({ type: "PAUSE", time: playbackTime })
  }

  const handleSeek = (time: number) => {
    sendMessage({ type: "SEEK", time })
  }

  return (
    <div className="h-screen grid grid-cols-[3fr_1fr] bg-zinc-950 text-zinc-100">
      <div className="flex flex-col">
        <div className="flex-1 bg-black">
          <VideoPlayer videoId="1078605" />
        </div>
        <div className="border-t border-zinc-800 bg-zinc-900 p-3">
          <PlaybackControls
            onPlay={handlePlay}
            onPause={handlePause}
            onSeek={handleSeek}
          />
        </div>
      </div>

      <div className="border-l border-zinc-800 flex flex-col bg-zinc-900/80">
        <div className="flex-1 border-b border-zinc-800">
          <Chat />
        </div>
        <div className="h-40 border-b border-zinc-800">
          <ParticipantList
            participants={participants.map((name) => ({
              id: name,
              display_name: name,
              is_host: name === host,
            }))}
          />
        </div>
        <div className="h-16" />
      </div>
    </div>
  )
}
