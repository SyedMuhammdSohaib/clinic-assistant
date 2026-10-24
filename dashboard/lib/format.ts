// Formatting helpers. Pure functions, no server-only code.
import type { Num } from "./types";

const TZ = process.env.CLINIC_TZ || "Asia/Karachi";

const dateTimeFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: TZ,
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const dayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: TZ, day: "numeric", month: "short", year: "numeric" });
const shortDayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: TZ, day: "numeric", month: "short" });
// Date-only values ("2026-06-03") are calendar days, not moments, so format them in UTC.
const plainDayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", day: "numeric", month: "short", year: "numeric" });

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

export function fmtDateTime(iso: string): string {
  return dateTimeFmt.format(new Date(iso));
}

export function fmtDay(value: string): string {
  if (DATE_ONLY.test(value)) return plainDayFmt.format(new Date(`${value}T00:00:00Z`));
  return dayFmt.format(new Date(value));
}

export function fmtShortDay(date: Date): string {
  return shortDayFmt.format(date);
}

export function num(value: Num | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** 7.00 -> "7", 7.50 -> "7.5" */
export function fmtNum(value: Num | null | undefined): string {
  const n = num(value);
  if (n === null) return "–";
  return String(Number(n.toFixed(2)));
}

export function fmtDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return "–";
  if (seconds < 60) return `${seconds} sec`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s ? `${m} min ${s} sec` : `${m} min`;
}

export function ageText(dob: string, now: Date = new Date()): string {
  const [y, m, d] = dob.split("-").map(Number);
  let years = now.getUTCFullYear() - y;
  const beforeBirthday = now.getUTCMonth() + 1 < m || (now.getUTCMonth() + 1 === m && now.getUTCDate() < d);
  if (beforeBirthday) years -= 1;
  if (years >= 2) return `${years} years`;
  let months = (now.getUTCFullYear() - y) * 12 + (now.getUTCMonth() + 1 - m);
  if (now.getUTCDate() < d) months -= 1;
  return `${Math.max(months, 0)} months`;
}

export function timesPerDayText(n: number): string {
  if (n === 1) return "Once a day";
  if (n === 2) return "Twice a day";
  return `${n} times a day`;
}

export function changeTypeText(type: string): string {
  return type.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/** The short patient id the doctor sees and types: the first 8 characters of the real id. */
export function shortId(id: string): string {
  return id.slice(0, 8).toUpperCase();
}

/** 923001234567 -> 0300 1234567; other numbers as stored. */
export function phoneText(phone: string): string {
  return /^92\d{10}$/.test(phone) ? `0${phone.slice(2, 5)} ${phone.slice(5)}` : phone;
}

/** Today's date in the clinic, as YYYY-MM-DD for date inputs. */
export function clinicToday(now: Date = new Date()): string {
  return now.toLocaleDateString("en-CA", { timeZone: TZ });
}
