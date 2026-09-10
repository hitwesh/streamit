"use client"

import { useEffect, useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { guestLogin, signup } from "@/lib/api"
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
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [signupError, setSignupError] = useState<string | null>(null)
  const [signupLoading, setSignupLoading] = useState(false)
  const [guestName, setGuestName] = useState("")
  const [guestError, setGuestError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  const handleSignup = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault()
    setSignupError(null)
    setSignupLoading(true)

    const trimmedDisplayName = displayName.trim()
    const trimmedEmail = email.trim()

    if (!trimmedDisplayName || !trimmedEmail || !password) {
      setSignupError("Display name, email, and password are required")
      setSignupLoading(false)
      return
    }

    if (password !== confirmPassword) {
      setSignupError("Passwords do not match")
      setSignupLoading(false)
      return
    }

    try {
      const data = await signup({
        display_name: trimmedDisplayName,
        email: trimmedEmail,
        password,
      })

      setSession(
        {
          id: data.id,
          display_name: data.display_name,
          is_guest: data.is_guest,
        },
        data.access_token,
        data.refresh_token
      )
      router.push("/dashboard")
    } catch (error) {
      setSignupError(getErrorMessage(error))
    } finally {
      setSignupLoading(false)
    }
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
        data.access_token,
        data.refresh_token
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
            Create your StreamIt account.
          </h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Set up your profile and start hosting rooms in minutes.
          </p>

          <form className="mt-6 space-y-3" onSubmit={handleSignup}>
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
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              type="password"
              className="input"
            />
            <input
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Confirm password"
              type="password"
              className="input"
            />
            {signupError ? (
              <p className="text-xs text-red-400">{signupError}</p>
            ) : null}
            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={signupLoading}
            >
              {signupLoading ? "Creating…" : "Create account"}
            </button>
          </form>

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

          <div className="mt-6 border border-white/10 bg-white/5 px-4 py-3 text-xs text-[color:var(--color-muted)]">
            Guest sessions can join rooms instantly, but hosting tools require a
            full account.
          </div>
        </section>
      </main>
    </div>
  )
}
