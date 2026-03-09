"use client"

import { useEffect } from "react"
import { useParams } from "next/navigation"
import {
  connectToRoom,
  disconnectSocket,
  addMessageHandler,
  type ServerEvent,
} from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"
import Player from "@/components/Player"
import Chat from "@/components/Chat"
import Participants from "@/components/Participants"
import Controls from "@/components/Controls"

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

  return (
    <div className="h-screen flex flex-col bg-zinc-950 text-zinc-100">

      {/* Player */}
      <div className="flex-1 bg-black">
        <Player roomCode={roomCode} />
      </div>

      {/* Participants + Chat */}
      <div className="flex h-80 border-t border-zinc-800 bg-zinc-900/80">
        <div className="w-1/3 border-r border-zinc-800">
          <Participants />
        </div>
        <div className="flex-1">
          <Chat />
        </div>
      </div>

      {/* Controls */}
      <div className="h-16 border-t border-zinc-800 bg-zinc-900">
        <Controls />
      </div>

    </div>
  )
}
