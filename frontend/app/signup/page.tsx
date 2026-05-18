"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { guestLogin } from "@/lib/api"
import { useSessionStore } from "@/store/sessionStore"

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Something went wrong"
}

export default function SignupPage() {
  const router = useRouter()
  const { hydrate, setSession } = useSessionStore()

  const [displayName, setDisplayName] = useState("")
  const [email, setEmail] = useState("")
  const [requestStatus, setRequestStatus] = useState<string | null>(null)
  const [guestName, setGuestName] = useState("")
  const [guestError, setGuestError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  const handleRequestAccess = () => {
    setRequestStatus(null)

    if (!displayName.trim() || !email.trim()) {
      setRequestStatus("Display name and email required")
      return
    }

    setRequestStatus(
      "Account creation is invite only. Our team will reach out with access."
    )
  }

  const handleGuestLogin = async () => {
    setGuestError(null)

    if (!guestName.trim()) {
      setGuestError("Display name required")
      return
    }

    try {
      const data = await guestLogin(guestName)
      setSession(
        {
          id: data.id,
          display_name: data.display_name,
          is_guest: data.is_guest,
        },
        data.access_token
      )
      router.push("/dashboard")
    } catch (error) {
      setGuestError(getErrorMessage(error))
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/5 bg-black/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <Link
            href="/"
            className="text-sm font-semibold uppercase tracking-[0.4em] text-white"
          >
            StreamIt
          </Link>
          <div className="flex items-center gap-3 text-xs">
            <Link href="/login" className="btn btn-outline">
              Sign in
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-5xl gap-6 px-6 py-10 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="panel p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Create account
          </p>
          <h1 className="mt-3 text-2xl font-semibold">
            Request access to StreamIt.
          </h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            We are onboarding creators in cohorts to keep quality high. Submit
            your details and we will reach out with access.
          </p>

          <div className="mt-6 space-y-3">
            <input
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Display name"
              className="input"
            />
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              type="email"
              className="input"
            />
            {requestStatus ? (
              <p className="text-xs text-[color:var(--color-muted)]">
                {requestStatus}
              </p>
            ) : null}
            <button onClick={handleRequestAccess} className="btn btn-primary w-full">
              Request access
            </button>
          </div>

          <div className="mt-6 flex items-center justify-between text-xs text-[color:var(--color-muted)]">
            <span>Already invited?</span>
            <Link href="/login" className="btn btn-link">
              Sign in
            </Link>
          </div>
        </section>

        <section className="panel-soft p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[color:var(--color-muted)]">
            Try StreamIt
          </p>
          <h2 className="mt-3 text-lg font-semibold">
            Explore with a guest session.
          </h2>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Guests can join public rooms instantly and experience the full live
            chat and sync features.
          </p>

          <div className="mt-6 space-y-3">
            <input
              value={guestName}
              onChange={(event) => setGuestName(event.target.value)}
              placeholder="Display name"
              className="input"
            />
            {guestError ? (
              <p className="text-xs text-red-400">{guestError}</p>
            ) : null}
            <button onClick={handleGuestLogin} className="btn btn-outline w-full">
              Continue as guest
            </button>
          </div>

          <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-[color:var(--color-muted)]">
            Guest sessions are public only and do not unlock hosting tools. Host
            access requires an invite.
          </div>
        </section>
      </main>
    </div>
  )
}
