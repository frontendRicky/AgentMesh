import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = dayjs(iso);
  if (!d.isValid()) return iso;
  return d.format('YYYY-MM-DD HH:mm');
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = dayjs(iso);
  if (!d.isValid()) return iso;
  return d.fromNow();
}

export function formatSize(bytes: number | null | undefined): string {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return '—';
  return n.toLocaleString('en-US');
}
