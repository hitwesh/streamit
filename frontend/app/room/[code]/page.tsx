"use client"

import { useEffect } from "react"
import {
  connectToRoom,
  disconnectSocket,
  addMessageHandler,
  type ServerEvent,
} from "@/lib/websocket"

export default function RoomPage({ params }: { params: { code: string } }) {
  const roomCode = params.code

  useEffect(() => {
    const token = localStorage.getItem("token") ?? ""
    connectToRoom(roomCode, token)

    // addMessageHandler returns an unsubscribe fn — used as the cleanup below.
    const unsubscribe = addMessageHandler((event: ServerEvent) => {
      switch (event.type) {
        case "CHAT_HISTORY":
          console.log("[WS] chat history loaded", event.messages)
          break

        case "CHAT_MESSAGE":
          console.log("[WS] chat message", event.user, event.message)
          break

        case "PLAYBACK_STATE":
          console.log("[WS] playback state", event)
          break

        case "ROOM_PARTICIPANTS":
          console.log("[WS] participants", event.participants, "host:", event.host)
          break

        case "USER_JOINED":
          console.log("[WS] user joined", event.user)
          break

        case "USER_LEFT":
          console.log("[WS] user left", event.user)
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

        case "SYNC_CORRECTION":
          console.log("[WS] sync correction — seek to", event.time)
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

  return <div>Room {roomCode}</div>
}
