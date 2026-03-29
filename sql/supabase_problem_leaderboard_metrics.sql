BEGIN;

CREATE TABLE IF NOT EXISTS public.challenge_attempt_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES public.problems(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

ALTER TABLE public.challenge_submissions
    ADD COLUMN IF NOT EXISTS test_cases_total INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS test_cases_passed INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS avg_execution_time_ms NUMERIC(12, 3) NULL,
    ADD COLUMN IF NOT EXISTS avg_memory_kb NUMERIC(12, 2) NULL,
    ADD COLUMN IF NOT EXISTS test_case_metrics_json JSONB NULL,
    ADD COLUMN IF NOT EXISTS attempt_session_id BIGINT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'challenge_submissions_attempt_session_id_fkey'
    ) THEN
        ALTER TABLE public.challenge_submissions
            ADD CONSTRAINT challenge_submissions_attempt_session_id_fkey
            FOREIGN KEY (attempt_session_id)
            REFERENCES public.challenge_attempt_sessions(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_challenge_attempt_sessions_lookup
    ON public.challenge_attempt_sessions (user_id, problem_id, completed_at, started_at);

CREATE INDEX IF NOT EXISTS idx_challenge_submissions_problem_passed_timestamp
    ON public.challenge_submissions (problem_id, passed, timestamp);

CREATE INDEX IF NOT EXISTS idx_challenge_submissions_problem_user_passed
    ON public.challenge_submissions (problem_id, user_id, passed);

UPDATE public.challenge_submissions
SET test_cases_total = 0
WHERE test_cases_total IS NULL;

UPDATE public.challenge_submissions
SET test_cases_passed = 0
WHERE test_cases_passed IS NULL;

COMMIT;
