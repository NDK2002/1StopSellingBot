-- Staff table
CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    telegram_chat_id TEXT UNIQUE,
    skills TEXT[] DEFAULT '{}',
    is_available BOOLEAN DEFAULT TRUE,
    max_concurrent INTEGER DEFAULT 5,
    current_load INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Escalations table
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    staff_id UUID REFERENCES staff(id),
    reason TEXT NOT NULL DEFAULT 'low_confidence',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'resolved', 'expired')),
    skill_required TEXT,
    priority INTEGER DEFAULT 0,
    customer_summary TEXT,
    staff_notes TEXT,
    assigned_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_staff_available ON staff(is_available);
CREATE INDEX idx_staff_skills ON staff USING gin(skills);
CREATE INDEX idx_escalations_status ON escalations(status);
CREATE INDEX idx_escalations_staff ON escalations(staff_id);
CREATE INDEX idx_escalations_session ON escalations(session_id);
CREATE INDEX idx_escalations_created ON escalations(created_at);

-- Triggers
CREATE TRIGGER trigger_staff_updated_at BEFORE UPDATE ON staff FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trigger_escalations_updated_at BEFORE UPDATE ON escalations FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Grant access
GRANT ALL ON staff TO anon, authenticated;
GRANT ALL ON escalations TO anon, authenticated;

NOTIFY pgrst, 'reload schema';
