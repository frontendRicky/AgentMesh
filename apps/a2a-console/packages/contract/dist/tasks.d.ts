import { z } from 'zod';
export declare const parsedMarkdownSchema: z.ZodObject<{
    frontmatter: z.ZodNullable<z.ZodRecord<z.ZodString, z.ZodUnknown>>;
    body: z.ZodString;
    parse_error: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    frontmatter: Record<string, unknown> | null;
    body: string;
    parse_error: string | null;
}, {
    frontmatter: Record<string, unknown> | null;
    body: string;
    parse_error: string | null;
}>;
export declare const taskSummarySchema: z.ZodObject<{
    task_id: z.ZodString;
    task_title: z.ZodNullable<z.ZodString>;
    task_type: z.ZodNullable<z.ZodString>;
    priority: z.ZodNullable<z.ZodString>;
    current_status: z.ZodNullable<z.ZodString>;
    current_agent: z.ZodNullable<z.ZodString>;
    human_review_status: z.ZodNullable<z.ZodString>;
    final_review_status: z.ZodNullable<z.ZodString>;
    blocker_count: z.ZodNumber;
    produced_artifacts_count: z.ZodNumber;
    token_total_estimate: z.ZodNumber;
    created_at: z.ZodNullable<z.ZodString>;
    updated_at: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    task_id: string;
    task_title: string | null;
    task_type: string | null;
    priority: string | null;
    current_status: string | null;
    current_agent: string | null;
    human_review_status: string | null;
    final_review_status: string | null;
    blocker_count: number;
    produced_artifacts_count: number;
    token_total_estimate: number;
    created_at: string | null;
    updated_at: string | null;
}, {
    task_id: string;
    task_title: string | null;
    task_type: string | null;
    priority: string | null;
    current_status: string | null;
    current_agent: string | null;
    human_review_status: string | null;
    final_review_status: string | null;
    blocker_count: number;
    produced_artifacts_count: number;
    token_total_estimate: number;
    created_at: string | null;
    updated_at: string | null;
}>;
export declare const taskDetailResponseSchema: z.ZodObject<{
    task: z.ZodObject<{
        frontmatter: z.ZodNullable<z.ZodRecord<z.ZodString, z.ZodUnknown>>;
        body: z.ZodString;
        parse_error: z.ZodNullable<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    }, {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    }>;
    state: z.ZodObject<{
        frontmatter: z.ZodNullable<z.ZodRecord<z.ZodString, z.ZodUnknown>>;
        body: z.ZodString;
        parse_error: z.ZodNullable<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    }, {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    }>;
    summary: z.ZodNullable<z.ZodObject<{
        task_id: z.ZodString;
        task_title: z.ZodNullable<z.ZodString>;
        task_type: z.ZodNullable<z.ZodString>;
        priority: z.ZodNullable<z.ZodString>;
        current_status: z.ZodNullable<z.ZodString>;
        current_agent: z.ZodNullable<z.ZodString>;
        human_review_status: z.ZodNullable<z.ZodString>;
        final_review_status: z.ZodNullable<z.ZodString>;
        blocker_count: z.ZodNumber;
        produced_artifacts_count: z.ZodNumber;
        token_total_estimate: z.ZodNumber;
        created_at: z.ZodNullable<z.ZodString>;
        updated_at: z.ZodNullable<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        task_id: string;
        task_title: string | null;
        task_type: string | null;
        priority: string | null;
        current_status: string | null;
        current_agent: string | null;
        human_review_status: string | null;
        final_review_status: string | null;
        blocker_count: number;
        produced_artifacts_count: number;
        token_total_estimate: number;
        created_at: string | null;
        updated_at: string | null;
    }, {
        task_id: string;
        task_title: string | null;
        task_type: string | null;
        priority: string | null;
        current_status: string | null;
        current_agent: string | null;
        human_review_status: string | null;
        final_review_status: string | null;
        blocker_count: number;
        produced_artifacts_count: number;
        token_total_estimate: number;
        created_at: string | null;
        updated_at: string | null;
    }>>;
}, "strip", z.ZodTypeAny, {
    task: {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    };
    state: {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    };
    summary: {
        task_id: string;
        task_title: string | null;
        task_type: string | null;
        priority: string | null;
        current_status: string | null;
        current_agent: string | null;
        human_review_status: string | null;
        final_review_status: string | null;
        blocker_count: number;
        produced_artifacts_count: number;
        token_total_estimate: number;
        created_at: string | null;
        updated_at: string | null;
    } | null;
}, {
    task: {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    };
    state: {
        frontmatter: Record<string, unknown> | null;
        body: string;
        parse_error: string | null;
    };
    summary: {
        task_id: string;
        task_title: string | null;
        task_type: string | null;
        priority: string | null;
        current_status: string | null;
        current_agent: string | null;
        human_review_status: string | null;
        final_review_status: string | null;
        blocker_count: number;
        produced_artifacts_count: number;
        token_total_estimate: number;
        created_at: string | null;
        updated_at: string | null;
    } | null;
}>;
export type ParsedMarkdownPayload = z.infer<typeof parsedMarkdownSchema>;
export type TaskSummary = z.infer<typeof taskSummarySchema>;
export type TaskDetailResponse = z.infer<typeof taskDetailResponseSchema>;
export declare const taskDownloadErrorCodeSchema: z.ZodEnum<["TASK_NOT_FOUND", "TASK_PACKAGE_TOO_LARGE", "PATH_TRAVERSAL", "PROJECT_ROOT_MISSING"]>;
export type TaskDownloadErrorCode = z.infer<typeof taskDownloadErrorCodeSchema>;
