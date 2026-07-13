"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, Eye, EyeOff, Gauge, Loader2, Lock, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { login } from "@/lib/auth";

const IS_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      const next = searchParams.get("next");
      router.replace(next && next.startsWith("/") ? next : "/wells");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      {/* Brand */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-900/40">
          <Gauge className="text-white" size={30} />
        </div>
        <div className="text-center leading-tight">
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            WellScout
          </h1>
          <p className="text-sm text-stone-400">Terralog Technologies</p>
        </div>
      </div>

      {/* Card */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-8 shadow-2xl shadow-black/40 backdrop-blur">
        <h2 className="text-lg font-semibold text-white">Sign in</h2>
        <p className="mb-6 mt-1 text-sm text-stone-400">
          Access the well &amp; substation intelligence dashboard
        </p>

        {error && (
          <div
            role="alert"
            className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300"
          >
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="username"
              className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-stone-400"
            >
              Username
            </label>
            <div className="relative">
              <User
                size={16}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-500"
              />
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                autoFocus
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your.username"
                className="w-full rounded-lg border border-white/10 bg-stone-950/60 py-2.5 pl-9 pr-3 text-sm text-white placeholder:text-stone-600 outline-none transition-colors focus:border-emerald-500/60 focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-stone-400"
            >
              Password
            </label>
            <div className="relative">
              <Lock
                size={16}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-stone-500"
              />
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-white/10 bg-stone-950/60 py-2.5 pl-9 pr-10 text-sm text-white placeholder:text-stone-600 outline-none transition-colors focus:border-emerald-500/60 focus:ring-2 focus:ring-emerald-500/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-stone-500 transition-colors hover:text-stone-300"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className={cn(
              "mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-900/40 transition-opacity",
              submitting ? "cursor-not-allowed opacity-70" : "hover:opacity-90"
            )}
          >
            {submitting && <Loader2 size={16} className="animate-spin" />}
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-stone-500">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            IS_MOCK ? "bg-amber-400" : "bg-emerald-500"
          )}
        />
        <span>
          {IS_MOCK
            ? "Demo mode — any credentials will work"
            : "Connected to live data"}
        </span>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-stone-900 to-stone-950 px-4 py-12">
      <Suspense fallback={null}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
