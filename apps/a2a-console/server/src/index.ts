import { createApp } from './app.js';
import { logger } from './lib/logger.js';
import { loadConfig, getConfigFilePath } from './config/config-store.js';

const PORT = Number(process.env.A2A_CONSOLE_PORT ?? 5174);

const app = createApp();
const config = loadConfig();

app.listen(PORT, () => {
  logger.info(`A2A Console server listening on http://localhost:${PORT}`);
  logger.info(`Config file: ${getConfigFilePath()}`);
  if (config.project_root) {
    logger.info(`Active project root: ${config.project_root}`);
  } else {
    logger.warn('No project_root configured. POST /api/a2a/config/project-root to set one.');
  }
});
