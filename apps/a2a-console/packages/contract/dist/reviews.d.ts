import { z } from 'zod';
export declare const reviewItemSchema: z.ZodObject<{
    review_id: z.ZodNullable<z.ZodString>;
    review_type: z.ZodNullable<z.ZodString>;
    reviewer: z.ZodNullable<z.ZodString>;
    reviewed_at: z.ZodNullable<z.ZodString>;
    verdict: z.ZodNullable<z.ZodString>;
    followup_required: z.ZodNullable<z.ZodBoolean>;
    notes: z.ZodNullable<z.ZodString>;
    file_path: z.ZodEffects<z.ZodString, string, string>;
}, "strip", z.ZodTypeAny, {
    file_path: string;
    review_id: string | null;
    review_type: string | null;
    reviewer: string | null;
    reviewed_at: string | null;
    verdict: string | null;
    followup_required: boolean | null;
    notes: string | null;
}, {
    file_path: string;
    review_id: string | null;
    review_type: string | null;
    reviewer: string | null;
    reviewed_at: string | null;
    verdict: string | null;
    followup_required: boolean | null;
    notes: string | null;
}>;
export declare const reviewsResponseSchema: z.ZodObject<{
    items: z.ZodArray<z.ZodObject<{
        review_id: z.ZodNullable<z.ZodString>;
        review_type: z.ZodNullable<z.ZodString>;
        reviewer: z.ZodNullable<z.ZodString>;
        reviewed_at: z.ZodNullable<z.ZodString>;
        verdict: z.ZodNullable<z.ZodString>;
        followup_required: z.ZodNullable<z.ZodBoolean>;
        notes: z.ZodNullable<z.ZodString>;
        file_path: z.ZodEffects<z.ZodString, string, string>;
    }, "strip", z.ZodTypeAny, {
        file_path: string;
        review_id: string | null;
        review_type: string | null;
        reviewer: string | null;
        reviewed_at: string | null;
        verdict: string | null;
        followup_required: boolean | null;
        notes: string | null;
    }, {
        file_path: string;
        review_id: string | null;
        review_type: string | null;
        reviewer: string | null;
        reviewed_at: string | null;
        verdict: string | null;
        followup_required: boolean | null;
        notes: string | null;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    items: {
        file_path: string;
        review_id: string | null;
        review_type: string | null;
        reviewer: string | null;
        reviewed_at: string | null;
        verdict: string | null;
        followup_required: boolean | null;
        notes: string | null;
    }[];
}, {
    items: {
        file_path: string;
        review_id: string | null;
        review_type: string | null;
        reviewer: string | null;
        reviewed_at: string | null;
        verdict: string | null;
        followup_required: boolean | null;
        notes: string | null;
    }[];
}>;
export type ReviewItem = z.infer<typeof reviewItemSchema>;
export type ReviewsResponse = z.infer<typeof reviewsResponseSchema>;
