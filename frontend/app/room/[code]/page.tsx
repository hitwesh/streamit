"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Image from "next/image"
import { useParams, useRouter } from "next/navigation"
import {
  addConnectionHandler,
  addMessageHandler,
  connectToRoom,
  disconnectSocket,
  sendMessage,
  type ServerEvent,
  type PlayerEventData,
} from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"
import { useSessionStore } from "@/store/sessionStore"
import {
  approveParticipant,
  deleteRoom,
  getRoomDetail,
  getRoomParticipants,
  joinRoom,
  resumeProgress,
  searchContent,
  updateRoomSource,
  type ParticipantRecord,
  type RoomDetail,
  type SearchResult,
} from "@/lib/api"
import { loadRoomMeta, saveRoomMeta, type RoomMeta } from "@/lib/storage"
import VideoPlayer from "@/components/VideoPlayer"
import PlaybackControls from "@/components/PlaybackControls"
import Chat from "@/components/Chat"
import ParticipantList from "@/components/ParticipantList"
import Player from "@/components/Player"

type ConnectionState = "idle" | "connecting" | "open" | "closed" | "error"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

export default function RoomPage() {
  const params = useParams<{ code: string }>()
  const router = useRouter()
  const roomCode = params?.code ?? ""
  const { token, user, hydrate } = useSessionStore()

  const [roomMeta, setRoomMeta] = useState<RoomMeta | null>(null)
  const [roomDetail, setRoomDetail] = useState<RoomDetail | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle")
  const [systemMessages, setSystemMessages] = useState<string[]>([])
  const [participants, setParticipants] = useState<ParticipantRecord[]>([])
  const [participantsLoading, setParticipantsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [resumeInfo, setResumeInfo] = useState<{
    progress_percent: number
    last_position_seconds: number
    completed: boolean
  } | null>(null)

  const playbackTime = useRoomStore((s) => s.playback.time)
  const playbackState = useRoomStore((s) => s.playback)
  const activeParticipants = useRoomStore((s) => s.participants)
  const host = useRoomStore((s) => s.host)
  const resetRoom = useRoomStore((s) => s.resetRoom)

  const isHost = roomDetail?.is_host || roomMeta?.is_host || false
  const roomId = roomDetail?.room_id || roomMeta?.room_id || ""
  const pendingApproval = roomMeta?.status === "PENDING"

  useEffect(() => {
    hydrate()
  }, [hydrate])

  useEffect(() => {
    if (!roomCode) return
    setRoomMeta(loadRoomMeta(roomCode))
  }, [roomCode])

  useEffect(() => {
    if (!roomCode || !token) return

    let active = true
    getRoomDetail(roomCode, token)
      .then((detail) => {
        if (!active) return
        setRoomDetail(detail)

        if (!roomMeta) {
          const meta: RoomMeta = {
            room_id: detail.room_id,
            code: detail.code,
            status: "APPROVED",
            is_host: detail.is_host,
          }
          saveRoomMeta(meta)
          setRoomMeta(meta)
        }
      })
      .catch((error) => {
        if (!active) return
        setSystemMessages((prev) => [...prev, getErrorMessage(error)])
      })

    return () => {
      active = false
    }
  }, [roomCode, token, roomMeta])

  useEffect(() => {
    if (!roomCode || !token || pendingApproval) return

    setConnectionState("connecting")
    connectToRoom(roomCode, token)

    const unsubscribe = addMessageHandler((event: ServerEvent) => {
      const store = useRoomStore.getState()

      switch (event.type) {
        case "CHAT_HISTORY":
          store.loadChatHistory(event.messages)
          break

        case "CHAT_MESSAGE":
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
          setSystemMessages((prev) => [
            ...prev,
            `Host disconnected. Grace period ${event.grace_seconds}s`,
          ])
          break

        case "HOST_RECONNECTED":
          setSystemMessages((prev) => [...prev, "Host reconnected"])
          break

        case "ROOM_DELETED":
          setSystemMessages((prev) => [...prev, "Room deleted by host"])
          break

        case "ERROR":
          setSystemMessages((prev) => [...prev, event.message])
          break
      }
    })

    const unsubscribeConnection = addConnectionHandler((state) => {
      if (state === "open") setConnectionState("open")
      if (state === "closed") setConnectionState("closed")
      if (state === "error") setConnectionState("error")
    })

    return () => {
      unsubscribe()
      unsubscribeConnection()
      disconnectSocket()
      resetRoom()
    }
  }, [roomCode, token, pendingApproval, resetRoom])

  useEffect(() => {
    if (connectionState !== "open") return

    const timer = setInterval(() => {
      const playback = useRoomStore.getState().playback
      sendMessage({ type: "SYNC_CHECK", client_time: playback.time })
    }, 20000)

    return () => clearInterval(timer)
  }, [connectionState])

  useEffect(() => {
    if (!roomCode || !token) return

    resumeProgress(roomCode, token)
      .then((data) => setResumeInfo(data))
      .catch(() => setResumeInfo(null))
  }, [roomCode, token])

  const loadParticipants = useCallback(async () => {
    if (!roomId || !token || !isHost) return
    setParticipantsLoading(true)

    try {
      const data = await getRoomParticipants(roomId, token)
      setParticipants(data)
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    } finally {
      setParticipantsLoading(false)
    }
  }, [roomId, token, isHost])

  useEffect(() => {
    if (!isHost || !roomId || !token) return
    void loadParticipants()

    const timer = setInterval(() => {
      void loadParticipants()
    }, 10000)

    return () => clearInterval(timer)
  }, [isHost, roomId, token, loadParticipants])

  const handlePlay = () => {
    sendMessage({ type: "PLAY", time: playbackTime })
  }

  const handlePause = () => {
    sendMessage({ type: "PAUSE", time: playbackTime })
  }

  const handleSeek = (time: number) => {
    sendMessage({ type: "SEEK", time })
  }

  const handleSync = () => {
    sendMessage({ type: "SYNC_CHECK", client_time: playbackTime })
  }

  const handlePlayerEvent = (data: PlayerEventData) => {
    if (!isHost) return
    sendMessage({ type: "PLAYER_EVENT", data })
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)

    try {
      const data = await searchContent(searchQuery.trim())
      setSearchResults(data)
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSelectMedia = async (item: SearchResult) => {
    if (!roomId || !token) return
    if (item.media_type !== "movie") {
      setSystemMessages((prev) => [
        ...prev,
        "Only movie results are supported for playback right now",
      ])
      return
    }

    try {
      const updated = await updateRoomSource(
        {
          room_id: roomId,
          provider: item.provider,
          video_id: item.stream_id,
        },
        token
      )

      setRoomDetail((prev) =>
        prev
          ? {
              ...prev,
              video_provider: updated.video_provider,
              video_id: updated.video_id,
            }
          : prev
      )
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    }
  }

  const handleApprove = async (userId: string) => {
    if (!roomId || !token) return

    try {
      await approveParticipant({ room_id: roomId, user_id: userId }, token)
      await loadParticipants()
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    }
  }

  const handleDeleteRoom = async () => {
    if (!roomId || !token) return

    try {
      await deleteRoom({ room_id: roomId }, token)
      setSystemMessages((prev) => [...prev, "Room deleted"])
      router.push("/")
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    }
  }

  const handleCheckApproval = async () => {
    if (!token || !roomCode) return

    try {
      const data = await joinRoom({ code: roomCode }, token)
      const updatedMeta: RoomMeta = {
        room_id: data.room_id,
        code: data.code,
        status: data.status,
        is_host: data.is_host,
      }
      saveRoomMeta(updatedMeta)
      setRoomMeta(updatedMeta)
    } catch (error) {
      setSystemMessages((prev) => [...prev, getErrorMessage(error)])
    }
  }

  const connectionLabel = useMemo(() => {
    switch (connectionState) {
      case "connecting":
        return "Connecting"
      case "open":
        return "Connected"
      case "closed":
        return "Disconnected"
      case "error":
        return "Error"
      default:
        return "Idle"
    }
  }, [connectionState])

  const visibleSystemMessages = systemMessages.slice(-3)

  return (
    <div className="min-h-screen px-6 py-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="panel flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--color-muted)]">
              Room
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold text-[color:var(--color-foreground)]">
                {roomCode}
              </h1>
              <span className="badge">{isHost ? "Host" : "Guest"}</span>
              <span className="text-xs text-[color:var(--color-muted)]">
                {connectionLabel}
              </span>
            </div>
            {roomMeta?.room_password ? (
              <p className="mt-2 text-xs text-[color:var(--color-muted)]">
                Room password: {roomMeta.room_password}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <button
              onClick={() => router.push("/")}
              className="btn btn-outline"
            >
              Back to home
            </button>
            {isHost ? (
              <button onClick={handleDeleteRoom} className="btn btn-outline">
                Delete room
              </button>
            ) : null}
            {user ? (
              <span className="text-xs text-[color:var(--color-muted)]">
                Signed in as {user.display_name}
              </span>
            ) : (
              <span className="text-xs text-red-600">
                Login required to connect
              </span>
            )}
          </div>
        </header>

        {pendingApproval ? (
          <section className="panel-soft flex flex-col gap-2 p-4 text-sm">
            <p className="font-semibold">Waiting for host approval</p>
            <p className="text-xs text-[color:var(--color-muted)]">
              The host must approve your entry before you can connect.
            </p>
            <button onClick={handleCheckApproval} className="btn btn-outline">
              Check approval
            </button>
          </section>
        ) : null}

        {visibleSystemMessages.length > 0 ? (
          <section className="panel-soft flex flex-col gap-2 p-3 text-xs text-[color:var(--color-muted)]">
            {visibleSystemMessages.map((message, index) => (
              <span key={`${message}-${index}`}>{message}</span>
            ))}
          </section>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <section className="panel flex flex-col gap-4 p-5">
            <div className="aspect-video rounded-3xl bg-black/90">
              {process.env.NEXT_PUBLIC_DEMO_STREAM_URL ? (
                <Player onPlayerEvent={handlePlayerEvent} isHost={isHost} />
              ) : (
                <VideoPlayer
                  provider={roomDetail?.video_provider ?? ""}
                  videoId={roomDetail?.video_id ?? ""}
                />
              )}
            </div>

            {isHost ? (
              <PlaybackControls
                onPlay={handlePlay}
                onPause={handlePause}
                onSeek={handleSeek}
                onSync={handleSync}
                currentTime={playbackState.time}
                isPlaying={playbackState.is_playing}
              />
            ) : (
              <div className="text-xs text-[color:var(--color-muted)]">
                Playback controlled by host. Current time {playbackState.time.toFixed(1)}s
              </div>
            )}

            {resumeInfo ? (
              <div className="panel-soft flex items-center justify-between px-4 py-3 text-xs">
                <span>
                  Resume: {resumeInfo.last_position_seconds.toFixed(1)}s -
                  {" "}{resumeInfo.progress_percent.toFixed(1)}%
                </span>
                <span>
                  {resumeInfo.completed ? "Completed" : "In progress"}
                </span>
              </div>
            ) : null}

            {isHost ? (
              <div className="panel-soft flex flex-col gap-3 p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search titles"
                    className="input flex-1"
                  />
                  <button onClick={handleSearch} className="btn btn-outline">
                    {searchLoading ? "Searching" : "Search"}
                  </button>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {searchResults.length === 0 && !searchLoading ? (
                    <p className="text-xs text-[color:var(--color-muted)]">
                      Search for a title to set the room media.
                    </p>
                  ) : null}
                  {searchResults.map((result) => (
                    <div
                      key={`${result.provider}-${result.stream_id}`}
                      className="rounded-2xl border border-black/5 bg-white/70 p-3"
                    >
                      <div className="flex gap-3">
                        {result.poster ? (
                          <Image
                            src={result.poster}
                            alt=""
                            width={48}
                            height={64}
                            className="h-16 w-12 rounded-xl object-cover"
                          />
                        ) : (
                          <div className="flex h-16 w-12 items-center justify-center rounded-xl bg-black/5 text-[10px] text-[color:var(--color-muted)]">
                            No art
                          </div>
                        )}
                        <div>
                          <p className="text-sm font-semibold text-[color:var(--color-foreground)]">
                            {result.title}
                          </p>
                          <p className="text-xs text-[color:var(--color-muted)]">
                            {result.media_type} - {result.release_year ?? "N/A"}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleSelectMedia(result)}
                        className="btn btn-ghost mt-3"
                      >
                        Use this title
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>

          <aside className="flex flex-col gap-6">
            <section className="panel flex h-[420px] flex-col">
              <div className="border-b border-black/5 px-4 py-3">
                <h2 className="text-sm font-semibold">Chat</h2>
                <p className="text-xs text-[color:var(--color-muted)]">
                  Realtime messages are stored and replayed on join.
                </p>
              </div>
              <Chat isDisabled={roomDetail ? !roomDetail.is_chat_enabled : false} />
            </section>

            <section className="panel">
              <ParticipantList
                participants={activeParticipants.map((name) => ({
                  id: name,
                  display_name: name,
                  is_host: name === host,
                }))}
              />
            </section>

            {isHost ? (
              <section className="panel p-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold">Moderation</h2>
                  <button onClick={loadParticipants} className="btn btn-ghost">
                    Refresh
                  </button>
                </div>
                {participantsLoading ? (
                  <p className="mt-3 text-xs text-[color:var(--color-muted)]">
                    Loading participants...
                  </p>
                ) : participants.length === 0 ? (
                  <p className="mt-3 text-xs text-[color:var(--color-muted)]">
                    No participant data available yet.
                  </p>
                ) : (
                  <div className="mt-3 space-y-3">
                    {participants.map((participant) => (
                      <div
                        key={participant.id}
                        className="rounded-2xl border border-black/5 bg-white/70 p-3"
                      >
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-semibold">
                            {participant.display_name}
                          </span>
                          <span className="text-xs text-[color:var(--color-muted)]">
                            {participant.status}
                          </span>
                        </div>
                        {participant.status === "PENDING" ? (
                          <button
                            onClick={() => handleApprove(participant.id)}
                            className="btn btn-primary mt-3"
                          >
                            Approve
                          </button>
                        ) : participant.is_host ? (
                          <p className="mt-3 text-xs text-[color:var(--color-muted)]">
                            Host controls
                          </p>
                        ) : (
                          <div className="mt-3 flex flex-wrap gap-2">
                            <button
                              onClick={() =>
                                sendMessage({
                                  type: "MUTE_USER",
                                  user_id: participant.id,
                                })
                              }
                              className="btn btn-ghost"
                            >
                              Mute
                            </button>
                            <button
                              onClick={() =>
                                sendMessage({
                                  type: "KICK_USER",
                                  user_id: participant.id,
                                })
                              }
                              className="btn btn-outline"
                            >
                              Kick
                            </button>
                            <button
                              onClick={() =>
                                sendMessage({
                                  type: "BAN_USER",
                                  user_id: participant.id,
                                })
                              }
                              className="btn btn-outline"
                            >
                              Ban
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  )
}
