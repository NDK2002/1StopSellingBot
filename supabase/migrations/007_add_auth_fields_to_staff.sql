ALTER TABLE public.staff ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE public.staff ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'staff';

-- Set default role to admin for the first user
UPDATE public.staff SET role = 'admin' WHERE id = 'f3d29116-1d29-48c3-b589-bbcd7cfe12e5';

-- For convenience, 'admin123' bcrypt hash: $2b$12$KkQvwO3cItB4X/.92k3yHectq08cIot8cEwKRE2r/5O9Yy4x8y7T2
UPDATE public.staff SET password_hash = '$2b$12$KkQvwO3cItB4X/.92k3yHectq08cIot8cEwKRE2r/5O9Yy4x8y7T2' WHERE password_hash IS NULL;
