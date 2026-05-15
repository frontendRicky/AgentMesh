import { z } from 'zod';

import { nullableStringSchema, taskRelativePathSchema } from './envelope.js';

export const reviewItemSchema = z.object({
  review_id: nullableStringSchema,
  review_type: nullableStringSchema,
  reviewer: nullableStringSchema,
  reviewed_at: nullableStringSchema,
  verdict: nullableStringSchema,
  followup_required: z.boolean().nullable(),
  notes: nullableStringSchema,
  file_path: taskRelativePathSchema,
});

export const reviewsResponseSchema = z.object({
  items: z.array(reviewItemSchema),
});

export type ReviewItem = z.infer<typeof reviewItemSchema>;
export type ReviewsResponse = z.infer<typeof reviewsResponseSchema>;
