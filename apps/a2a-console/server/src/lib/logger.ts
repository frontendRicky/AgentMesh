type Level = 'info' | 'warn' | 'error';

function emit(level: Level, msg: string, extra?: unknown): void {
  const ts = new Date().toISOString();
  const line = `[${ts}] [${level.toUpperCase()}] ${msg}`;
  const payload = extra === undefined ? '' : ` ${JSON.stringify(extra)}`;
  if (level === 'error') {
    console.error(line + payload);
  } else if (level === 'warn') {
    console.warn(line + payload);
  } else {
    console.log(line + payload);
  }
}

export const logger = {
  info: (msg: string, extra?: unknown) => emit('info', msg, extra),
  warn: (msg: string, extra?: unknown) => emit('warn', msg, extra),
  error: (msg: string, extra?: unknown) => emit('error', msg, extra),
};
