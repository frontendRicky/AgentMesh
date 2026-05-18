import { z } from 'zod';
export const testSuiteSchema = z.enum(['typecheck', 'lint', 'build']);
export const testStatusSchema = z.enum(['pass', 'fail', 'timeout']);
export const testRunRequestSchema = z.object({
    run_id: z.string().min(1),
    project_id: z.string().min(1),
    suites: z.array(testSuiteSchema).min(1),
}).strict();
export const testResultSchema = z.object({
    suite: testSuiteSchema,
    status: testStatusSchema,
    exit_code: z.number().int(),
    duration_ms: z.number().int().nonnegative(),
    summary_lines: z.array(z.string()),
    log_path: z.string(),
    toolchain: z.string().default('nodejs'),
    created_at: z.string(),
});
export const testRunResponseSchema = z.object({
    run_id: z.string(),
    project_id: z.string(),
    results: z.array(testResultSchema),
});
//# sourceMappingURL=test.js.map