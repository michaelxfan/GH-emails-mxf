import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const APP_PASSWORD = process.env.APP_PASSWORD ?? "";

export async function POST(req: NextRequest) {
  if (!APP_PASSWORD) {
    return NextResponse.json({ error: "APP_PASSWORD not configured" }, { status: 500 });
  }
  const { password } = await req.json();
  if (password !== APP_PASSWORD) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set("gh_auth", APP_PASSWORD, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60 * 24 * 30, // 30 days
    path: "/",
  });
  return res;
}

export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set("gh_auth", "", { maxAge: 0, path: "/" });
  return res;
}
