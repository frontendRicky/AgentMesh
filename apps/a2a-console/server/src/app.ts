import cors from 'cors';
import express, { type Request, type Response, type NextFunction } from 'express';

import { logger } from './lib/logger.js';
import { activeTaskRouter } from './routes/active-task.js';
import { tasksRouter } from './routes/tasks.js';
import { taskDetailRouter } from './routes/task-detail.js';
import { artifactsRouter } from './routes/artifacts.js';
import { messagesRouter } from './routes/messages.js';
import { blockersRouter } from './routes/blockers.js';
import { humanReviewsRouter } from './routes/human-reviews.js';
import { metricsRouter } from './routes/metrics.js';
import { promptKeywordsRouter } from './routes/prompt-keywords.js';
import { modelPresetsRouter } from './routes/model-presets.js';
import { projectGeneratorRouter } from './routes/project-generator.js';
import { configRouter } from './routes/config.js';
import { fail } from './routes/_helpers.js';

export function createApp(): express.Express {
  const app = express();
  app.use(cors({ origin: ['http://localhost:5173'] }));
  app.use(express.json({ limit: '64kb' }));

  app.get('/api/a2a/health', (_req, res) => {
    res.json({ ok: true, data: { service: 'a2a-console-server', version: '0.1.0' } });
  });

  app.use('/api/a2a/active-task', activeTaskRouter);
  app.use('/api/a2a/tasks', tasksRouter);
  app.use('/api/a2a/tasks', taskDetailRouter);
  app.use('/api/a2a/tasks', artifactsRouter);
  app.use('/api/a2a/tasks', messagesRouter);
  app.use('/api/a2a/tasks', blockersRouter);
  app.use('/api/a2a/tasks', humanReviewsRouter);
  app.use('/api/a2a/tasks', metricsRouter);
  app.use('/api/a2a/tasks', promptKeywordsRouter);
  app.use('/api/a2a/model-presets', modelPresetsRouter);
  app.use('/api/a2a/project-generator', projectGeneratorRouter);
  app.use('/api/a2a/config', configRouter);

  app.use((_req, res) => {
    fail(res, 404, 'NOT_FOUND', 'Route not found');
  });

  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    const message = err instanceof Error ? err.message : String(err);
    logger.error('unhandled error', { message });
    fail(res, 500, 'INTERNAL_ERROR', message);
  });

  return app;
}
