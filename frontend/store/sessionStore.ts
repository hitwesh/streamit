import { create } from "zustand"
import type { SessionUser } from "@/lib/api"
import { clearSession, loadSession, saveSession } from "@/lib/storage"

interface SessionState {
  user: SessionUser | null
  token: string | null
  hydrated: boolean
  hydrate: () => void
  setSession: (user: SessionUser, token: string, refreshToken?: string) => void
  clear: () => void
}

export const useSessionStore = create<SessionState>((set, get) => ({
  user: null,
  token: null,
  hydrated: false,
  hydrate: () => {
    if (get().hydrated) return

    const stored = loadSession()
    if (stored) {
      set({ user: stored.user, token: stored.token, hydrated: true })
      return
    }

    set({ hydrated: true })
  },
  setSession: (user, token, refreshToken) => {
    saveSession({ user, token, refreshToken })
    set({ user, token, hydrated: true })
  },
  clear: () => {
    clearSession()
    set({ user: null, token: null, hydrated: true })
  },
}))
