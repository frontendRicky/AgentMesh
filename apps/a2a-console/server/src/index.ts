import cors from 'cors';
import express from 'express';

import { createApp } from './app.js';
import { logger } from './lib/logger.js';
import { loadConfig, getConfigFilePath } from './config/config-store.js';
import { runsRouter } from './routes/runs.js';

const PORT = Number(process.env.A2A_CONSOLE_PORT ?? 5174);

const app = express();
const config = loadConfig();

app.use(cors({ origin: ['http://localhost:5173'] }));
app.use(express.json({ limit: '64kb' }));
app.use('/api/a2a/runs', runsRouter);
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
