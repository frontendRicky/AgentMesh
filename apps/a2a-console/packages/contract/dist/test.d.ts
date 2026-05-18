import { z } from 'zod';
export declare const testSuiteSchema: z.ZodEnum<["typecheck", "lint", "build"]>;
export declare const testStatusSchema: z.ZodEnum<["pass", "fail", "timeout"]>;
export declare const testRunRequestSchema: z.ZodObject<{
    run_id: z.ZodString;
    project_id: z.ZodString;
    suites: z.ZodArray<z.ZodEnum<["typecheck", "lint", "build"]>, "many">;
}, "strict", z.ZodTypeAny, {
    run_id: string;
    project_id: string;
    suites: ("typecheck" | "lint" | "build")[];
}, {
    run_id: string;
    project_id: string;
    suites: ("typecheck" | "lint" | "build")[];
}>;
export declare const testResultSchema: z.ZodObject<{
    suite: z.ZodEnum<["typecheck", "lint", "build"]>;
    status: z.ZodEnum<["pass", "fail", "timeout"]>;
    exit_code: z.ZodNumber;
    duration_ms: z.ZodNumber;
    summary_lines: z.ZodArray<z.ZodString, "many">;
    log_path: z.ZodString;
    toolchain: z.ZodDefault<z.ZodString>;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    status: "pass" | "fail" | "timeout";
    created_at: string;
    suite: "typecheck" | "lint" | "build";
    exit_code: number;
    duration_ms: number;
    summary_lines: string[];
    log_path: string;
    toolchain: string;
}, {
    status: "pass" | "fail" | "timeout";
    created_at: string;
    suite: "typecheck" | "lint" | "build";
    exit_code: number;
    duration_ms: number;
    summary_lines: string[];
    log_path: string;
    toolchain?: string | undefined;
}>;
export declare const testRunResponseSchema: z.ZodObject<{
    run_id: z.ZodString;
    project_id: z.ZodString;
    results: z.ZodArray<z.ZodObject<{
        suite: z.ZodEnum<["typecheck", "lint", "build"]>;
        status: z.ZodEnum<["pass", "fail", "timeout"]>;
        exit_code: z.ZodNumber;
        duration_ms: z.ZodNumber;
        summary_lines: z.ZodArray<z.ZodString, "many">;
        log_path: z.ZodString;
        toolchain: z.ZodDefault<z.ZodString>;
        created_at: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        status: "pass" | "fail" | "timeout";
        created_at: string;
        suite: "typecheck" | "lint" | "build";
        exit_code: number;
        duration_ms: number;
        summary_lines: string[];
        log_path: string;
        toolchain: string;
    }, {
        status: "pass" | "fail" | "timeout";
        created_at: string;
        suite: "typecheck" | "lint" | "build";
        exit_code: number;
        duration_ms: number;
        summary_lines: string[];
        log_path: string;
        toolchain?: string | undefined;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    run_id: string;
    project_id: string;
    results: {
        status: "pass" | "fail" | "timeout";
        created_at: string;
        suite: "typecheck" | "lint" | "build";
        exit_code: number;
        duration_ms: number;
        summary_lines: string[];
        log_path: string;
        toolchain: string;
    }[];
}, {
    run_id: string;
    project_id: string;
    results: {
        status: "pass" | "fail" | "timeout";
        created_at: string;
        suite: "typecheck" | "lint" | "build";
        exit_code: number;
        duration_ms: number;
        summary_lines: string[];
        log_path: string;
        toolchain?: string | undefined;
    }[];
}>;
export type TestSuite = z.infer<typeof testSuiteSchema>;
export type TestStatus = z.infer<typeof testStatusSchema>;
export type TestRunRequest = z.infer<typeof testRunRequestSchema>;
export type TestResult = z.infer<typeof testResultSchema>;
export type TestRunResponse = z.infer<typeof testRunResponseSchema>;
