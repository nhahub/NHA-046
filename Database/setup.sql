-- Flora Smart Farming - Complete Database Setup
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Crop recommendations table
CREATE TABLE crop_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    nitrogen FLOAT NOT NULL,
    phosphorus FLOAT NOT NULL,
    potassium FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT CHECK (humidity >= 0 AND humidity <= 100),
    ph_level FLOAT CHECK (ph_level >= 0 AND ph_level <= 14),
    rainfall FLOAT NOT NULL,
    recommended_crop VARCHAR(100),
    suitability_level VARCHAR(50),
    match_percentage FLOAT CHECK (match_percentage >= 0 AND match_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disease predictions table
CREATE TABLE disease_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    image_url TEXT NOT NULL,
    is_healthy BOOLEAN DEFAULT FALSE,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    disease_detected VARCHAR(255),
    treatment_recommendation TEXT,
    prevention_tips TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_disease_user ON disease_predictions(user_id);
CREATE INDEX idx_crop_user ON crop_recommendations(user_id);
CREATE INDEX idx_users_email ON users(email);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE disease_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE crop_recommendations ENABLE ROW LEVEL SECURITY;

-- Simple RLS policies (disable for testing, enable for production)
-- ALTER TABLE disease_predictions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE crop_recommendations DISABLE ROW LEVEL SECURITY;

-- Or use these permissive policies:
CREATE POLICY "Allow all operations" ON disease_predictions FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON crop_recommendations FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON users FOR ALL USING (true);

-- Create storage bucket for plant images
INSERT INTO storage.buckets (id, name, public) 
VALUES ('plant-images', 'plant-images', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Public can view images" ON storage.objects
FOR SELECT USING (bucket_id = 'plant-images');

CREATE POLICY "Anyone can upload images" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'plant-images');

-- Utility function for user stats
CREATE OR REPLACE FUNCTION get_user_stats(user_uuid UUID)
RETURNS TABLE(
    total_disease_predictions BIGINT,
    total_crop_recommendations BIGINT,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM disease_predictions WHERE user_id = user_uuid),
        (SELECT COUNT(*) FROM crop_recommendations WHERE user_id = user_uuid),
        (SELECT GREATEST(
            COALESCE(MAX(dp.created_at), '1970-01-01'::timestamp),
            COALESCE(MAX(cr.created_at), '1970-01-01'::timestamp)
        )
        FROM disease_predictions dp
        FULL OUTER JOIN crop_recommendations cr ON TRUE
        WHERE dp.user_id = user_uuid OR cr.user_id = user_uuid);
END;
$$ LANGUAGE plpgsql;
