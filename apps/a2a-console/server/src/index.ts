import cors from 'cors';
import express from 'express';

import { createApp } from './app.js';
import { logger } from './lib/logger.js';
import { loadConfig, getConfigFilePath } from './config/config-store.js';
import { contextRouter } from './routes/context.js';
import { locksRouter } from './routes/locks.js';
import { policyRouter } from './routes/policy.js';
import { projectsRouter } from './routes/projects.js';
import { queueRouter } from './routes/queue.js';
import { runsRouter } from './routes/runs.js';
import { sandboxRouter } from './routes/sandbox.js';
import { testRouter } from './routes/test.js';
import { usageRouter } from './routes/usage.js';

const PORT = Number(process.env.A2A_CONSOLE_PORT ?? 5174);

const app = express();
const config = loadConfig();

app.use(cors({ origin: ['http://localhost:5173'] }));
app.use(express.json({ limit: '64kb' }));
app.use('/api/a2a/context', contextRouter);
app.use('/api/a2a/locks', locksRouter);
app.use('/api/a2a/policy', policyRouter);
app.use('/api/a2a/projects', projectsRouter);
app.use('/api/a2a/queue', queueRouter);
app.use('/api/a2a/runs', runsRouter);
app.use('/api/a2a/sandbox', sandboxRouter);
app.use('/api/a2a/test', testRouter);
app.use('/api/a2a/usage', usageRouter);
app.use(createApp());

app.listen(PORT, () => {
  logger.info(`A2A Console server listening on http://localhost:${PORT}`);
  logger.info(`Config file: ${getConfigFilePath()}`);
  if (config.project_root) {
    logger.info(`Active project root: ${config.project_root}`);
  } else {
    logger.warn('No project_root configured. POST /api/a2a/config/project-root to set one.');
  }
});
