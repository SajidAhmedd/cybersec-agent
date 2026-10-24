-- =============================================================================
-- CyberSecAgent - PostgreSQL Initialization Script
-- Run this to set up the initial database schema and seed data
-- =============================================================================

-- Create tables
-- Note: SQLAlchemy will also create these, this is for direct DB setup

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    expert_count INTEGER DEFAULT 0
);

-- Certifications table
CREATE TABLE IF NOT EXISTS certifications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    issuer VARCHAR(255),
    description TEXT,
    level VARCHAR(50)
);

-- Experts table
CREATE TABLE IF NOT EXISTS experts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    password_hash VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    bio TEXT,
    years_experience INTEGER DEFAULT 0,
    specializations JSONB DEFAULT '[]',
    hourly_rate FLOAT,
    currency VARCHAR(10) DEFAULT 'USD',
    availability BOOLEAN DEFAULT TRUE,
    response_time VARCHAR(50),
    location VARCHAR(255),
    timezone VARCHAR(100),
    languages JSONB DEFAULT '["English"]',
    rating FLOAT DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    total_cases INTEGER DEFAULT 0,
    whatsapp VARCHAR(50),
    linkedin VARCHAR(255),
    website VARCHAR(255),
    profile_image VARCHAR(500),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- External freelancer profiles (listed with a link only; no email/phone stored)
ALTER TABLE experts ALTER COLUMN email DROP NOT NULL;
ALTER TABLE experts ADD COLUMN IF NOT EXISTS is_external BOOLEAN DEFAULT FALSE;
ALTER TABLE experts ADD COLUMN IF NOT EXISTS profile_platform VARCHAR(50);
ALTER TABLE experts ADD COLUMN IF NOT EXISTS profile_url VARCHAR(500);

-- Featured experts are always listed first; public_contact experts agreed to show
-- their email/WhatsApp on the site
ALTER TABLE experts ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;
ALTER TABLE experts ADD COLUMN IF NOT EXISTS public_contact BOOLEAN DEFAULT FALSE;

-- Expert-Skills junction table
CREATE TABLE IF NOT EXISTS expert_skills (
    expert_id INTEGER REFERENCES experts(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (expert_id, skill_id)
);

-- Expert-Certifications junction table
CREATE TABLE IF NOT EXISTS expert_certifications (
    expert_id INTEGER REFERENCES experts(id) ON DELETE CASCADE,
    certification_id INTEGER REFERENCES certifications(id) ON DELETE CASCADE,
    year_obtained INTEGER,
    PRIMARY KEY (expert_id, certification_id)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    expert_id INTEGER REFERENCES experts(id) ON DELETE CASCADE,
    rating FLOAT NOT NULL,
    title VARCHAR(255),
    content TEXT,
    reviewer_name VARCHAR(255),
    is_anonymous BOOLEAN DEFAULT FALSE,
    case_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    current_phase VARCHAR(50) DEFAULT 'greeting',
    problem_context JSONB,
    security_analysis JSONB,
    selected_expert_id INTEGER REFERENCES experts(id),
    is_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Conversation messages table
CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_experts_email ON experts(email);
CREATE INDEX IF NOT EXISTS idx_experts_availability ON experts(availability);
CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

-- =============================================================================
-- Seed Data - Skills
-- =============================================================================

INSERT INTO skills (name, category, description) VALUES
    ('incident_response', 'defensive', 'Responding to and managing security incidents'),
    ('digital_forensics', 'defensive', 'Investigating digital evidence and cyber crimes'),
    ('malware_analysis', 'defensive', 'Analyzing malicious software'),
    ('penetration_testing', 'offensive', 'Testing systems for vulnerabilities'),
    ('mobile_security', 'specialty', 'Securing mobile devices and applications'),
    ('ios_forensics', 'specialty', 'Forensic analysis of iOS devices'),
    ('android_forensics', 'specialty', 'Forensic analysis of Android devices'),
    ('cloud_security', 'specialty', 'Securing cloud infrastructure'),
    ('network_security', 'defensive', 'Protecting network infrastructure'),
    ('endpoint_security', 'defensive', 'Securing end-user devices'),
    ('security_consulting', 'advisory', 'General security consulting services'),
    ('compliance', 'advisory', 'Regulatory compliance and auditing'),
    ('ransomware_response', 'specialty', 'Handling ransomware incidents'),
    ('threat_intelligence', 'defensive', 'Analyzing threat actors and TTPs'),
    ('security_awareness', 'advisory', 'Security training and awareness programs'),
    ('red_team', 'offensive', 'Adversary simulation and red teaming'),
    ('blue_team', 'defensive', 'Security operations and defense'),
    ('soc_analysis', 'defensive', 'Security Operations Center analysis'),
    ('vulnerability_assessment', 'offensive', 'Identifying system vulnerabilities'),
    ('web_application_security', 'offensive', 'Securing web applications')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- Seed Data - Certifications
-- =============================================================================

INSERT INTO certifications (name, issuer, level) VALUES
    ('OSCP', 'Offensive Security', 'expert'),
    ('CISSP', '(ISC)2', 'expert'),
    ('CEH', 'EC-Council', 'intermediate'),
    ('GCIH', 'SANS/GIAC', 'expert'),
    ('GCFA', 'SANS/GIAC', 'expert'),
    ('GPEN', 'SANS/GIAC', 'expert'),
    ('GMOB', 'SANS/GIAC', 'expert'),
    ('CISM', 'ISACA', 'expert'),
    ('CompTIA Security+', 'CompTIA', 'beginner'),
    ('AWS Security Specialty', 'Amazon', 'intermediate'),
    ('Azure Security Engineer', 'Microsoft', 'intermediate'),
    ('CCSP', '(ISC)2', 'expert'),
    ('CISA', 'ISACA', 'expert'),
    ('CRISC', 'ISACA', 'expert'),
    ('OSWE', 'Offensive Security', 'expert')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- Seed Data - Sample Experts (for development/testing)
-- =============================================================================

INSERT INTO experts (name, email, phone, title, bio, years_experience, specializations, hourly_rate, currency, availability, response_time, location, timezone, languages, rating, total_reviews, total_cases, whatsapp, is_verified, is_active)
VALUES
    (
        'Priya Sharma',
        'priya@example.com',
        '+919876543210',
        'Mobile Security Specialist',
        '8 years experience specializing in iOS and Android security. Previously worked at a major fintech company. I help individuals and businesses recover from mobile device compromises and implement better mobile security practices.',
        8,
        '["mobile_security", "ios_forensics", "incident_response"]',
        150,
        'USD',
        TRUE,
        '2 hours',
        'Mumbai, India',
        'Asia/Kolkata',
        '["English", "Hindi"]',
        4.9,
        47,
        52,
        '+919876543210',
        TRUE,
        TRUE
    ),
    (
        'Alex Chen',
        'alex@example.com',
        '+14155551234',
        'Incident Response Lead',
        'Former FBI cyber division with 12 years in digital forensics and incident response. I specialize in complex investigations and have handled hundreds of cases ranging from personal device compromises to large-scale corporate breaches.',
        12,
        '["incident_response", "digital_forensics", "malware_analysis"]',
        200,
        'USD',
        TRUE,
        '1 hour',
        'San Francisco, USA',
        'America/Los_Angeles',
        '["English", "Mandarin"]',
        4.8,
        89,
        156,
        '+14155551234',
        TRUE,
        TRUE
    ),
    (
        'Sarah Johnson',
        'sarah@example.com',
        '+447700900123',
        'Cybersecurity Consultant',
        'I help individuals and small businesses understand and recover from cyber incidents. My approach is patient and thorough - I explain things in plain English and guide you through every step.',
        6,
        '["security_consulting", "incident_response", "security_awareness"]',
        120,
        'USD',
        TRUE,
        '4 hours',
        'London, UK',
        'Europe/London',
        '["English"]',
        4.95,
        34,
        41,
        '+447700900123',
        TRUE,
        TRUE
    )
ON CONFLICT (email) DO NOTHING;

-- Link experts to skills
INSERT INTO expert_skills (expert_id, skill_id)
SELECT e.id, s.id FROM experts e, skills s
WHERE e.email = 'priya@example.com' AND s.name IN ('mobile_security', 'ios_forensics', 'incident_response', 'android_forensics')
ON CONFLICT DO NOTHING;

INSERT INTO expert_skills (expert_id, skill_id)
SELECT e.id, s.id FROM experts e, skills s
WHERE e.email = 'alex@example.com' AND s.name IN ('incident_response', 'digital_forensics', 'malware_analysis', 'threat_intelligence')
ON CONFLICT DO NOTHING;

INSERT INTO expert_skills (expert_id, skill_id)
SELECT e.id, s.id FROM experts e, skills s
WHERE e.email = 'sarah@example.com' AND s.name IN ('security_consulting', 'incident_response', 'security_awareness', 'compliance')
ON CONFLICT DO NOTHING;

-- Link experts to certifications
INSERT INTO expert_certifications (expert_id, certification_id, year_obtained)
SELECT e.id, c.id, 2020 FROM experts e, certifications c
WHERE e.email = 'priya@example.com' AND c.name IN ('GMOB', 'OSCP')
ON CONFLICT DO NOTHING;

INSERT INTO expert_certifications (expert_id, certification_id, year_obtained)
SELECT e.id, c.id, 2018 FROM experts e, certifications c
WHERE e.email = 'alex@example.com' AND c.name IN ('GCIH', 'GCFA', 'CISSP')
ON CONFLICT DO NOTHING;

INSERT INTO expert_certifications (expert_id, certification_id, year_obtained)
SELECT e.id, c.id, 2021 FROM experts e, certifications c
WHERE e.email = 'sarah@example.com' AND c.name IN ('CISSP', 'CISM')
ON CONFLICT DO NOTHING;

-- Done!
SELECT 'Database initialized successfully!' AS status;
