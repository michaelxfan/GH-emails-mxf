import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/api/auth"];
const APP_PASSWORD = process.env.APP_PASSWORD ?? "";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) return NextResponse.next();

  if (!APP_PASSWORD) return NextResponse.next(); // no password set → open

  const cookie = req.cookies.get("gh_auth")?.value;
  if (cookie === APP_PASSWORD) return NextResponse.next();

  const loginUrl = req.nextUrl.clone();
  loginUrl.pathname = "/login";
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
