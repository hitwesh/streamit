import { create } from "zustand"
import type { ChatMessage } from "@/lib/websocket"

// ─── Playback state mirrors the backend PLAYBACK_STATE event ─────────────────

interface PlaybackState {
  time: number
  is_playing: boolean
  version: number
}

// ─── Store shape ──────────────────────────────────────────────────────────────

interface RoomStore {
  // Participants (backend sends display names, not objects)
  participants: string[]
  host: string | null

  // Chat
  messages: ChatMessage[]

  // Playback
  playback: PlaybackState

  // Actions
  setParticipants: (participants: string[], host: string) => void
  addParticipant: (user: string) => void
  removeParticipant: (user: string) => void
  loadChatHistory: (messages: ChatMessage[]) => void
  addMessage: (msg: ChatMessage) => void
  setPlayback: (state: PlaybackState) => void
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useRoomStore = create<RoomStore>((set) => ({
  participants: [],
  host: null,
  messages: [],
  playback: { time: 0, is_playing: false, version: 0 },

  setParticipants: (participants, host) =>
    set({ participants, host }),

  // Guard against duplicates from concurrent events
  addParticipant: (user) =>
    set((state) => ({
      participants: state.participants.includes(user)
        ? state.participants
        : [...state.participants, user],
    })),

  removeParticipant: (user) =>
    set((state) => ({
      participants: state.participants.filter((p) => p !== user),
    })),

  loadChatHistory: (messages) =>
    set({ messages }),

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  setPlayback: (playback) =>
    set({ playback }),
}))
