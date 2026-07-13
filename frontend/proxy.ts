/**
 * Optimistic auth guard (Next.js 16 Proxy — formerly Middleware).
 *
 * Presence of the access-token cookie gates dashboard routes; the API still
 * verifies the JWT on every request, and the axios layer redirects to /login
 * when a token is rejected. This is only the fast, edge-level check.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ACCESS_COOKIE = "ws_access";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasToken = Boolean(request.cookies.get(ACCESS_COOKIE)?.value);
  const isLoginPage = pathname === "/login";

  if (!hasToken && !isLoginPage) {
    const url = new URL("/login", request.url);
    if (pathname !== "/") url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (hasToken && isLoginPage) {
    return NextResponse.redirect(new URL("/wells", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Everything except Next internals, static assets, and public files.
  matcher: ["/((?!_next|favicon\\.ico|data/|.*\\.[\\w]+$).*)"],
};
