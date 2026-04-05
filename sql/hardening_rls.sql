-- ALGOCOMPILER — DATABASE HARDENING SCRIPT (SUPABASE / POSTGRESQL)
-- This script enables Row Level Security (RLS) and defines restrictive policies.

-- 1. Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_attempt_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_votes ENABLE ROW LEVEL SECURITY;

-- 2. Define Policies

-- USERS: Users can only see and update their own profile.
-- Admin can see all (if 'is_admin' column is used in policy or via service_role)
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = oauth_id OR id::text = auth.uid()::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = oauth_id OR id::text = auth.uid()::text);

-- CHALLENGE SUBMISSIONS: Users can only see their own submissions.
CREATE POLICY "Users can view own submissions" ON challenge_submissions
    FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert own submissions" ON challenge_submissions
    FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

-- QA MODULE: Everyone can read, only authors can edit/delete.
CREATE POLICY "Anyone can view QA questions" ON qa_questions FOR SELECT USING (true);
CREATE POLICY "Authors can update own QA questions" ON qa_questions 
    FOR UPDATE USING (user_id::text = auth.uid()::text);
CREATE POLICY "Authors can delete own QA questions" ON qa_questions 
    FOR DELETE USING (user_id::text = auth.uid()::text);

CREATE POLICY "Anyone can view QA answers" ON qa_answers FOR SELECT USING (true);
CREATE POLICY "Authors can update own QA answers" ON qa_answers 
    FOR UPDATE USING (user_id::text = auth.uid()::text);
CREATE POLICY "Authors can delete own QA answers" ON qa_answers 
    FOR DELETE USING (user_id::text = auth.uid()::text);

-- 3. Restrict Direct Postgres Access
-- If using a shared DATABASE_URL with the 'postgres' superuser, RLS is bypassed.
-- It is STRONGLY RECOMMENDED to use a restricted role (e.g., 'authenticated' or 'anon')
-- for the web application's database connection.

-- WARNING: These policies assume you are using Supabase Auth or a similar mechanism 
-- that sets the 'auth.uid()' request variable. If using standard Flask-Login, 
-- you may need to adjust the policies to match your application's user identification.
