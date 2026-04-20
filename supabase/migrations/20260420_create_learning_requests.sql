CREATE TABLE IF NOT EXISTS learning_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  subject text NOT NULL,
  detail text,
  budget integer,
  format text DEFAULT 'any',
  status text DEFAULT 'open',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE learning_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view open requests" ON learning_requests
  FOR SELECT USING (status = 'open');

CREATE POLICY "Users can insert own requests" ON learning_requests
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own requests" ON learning_requests
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own requests" ON learning_requests
  FOR SELECT USING (auth.uid() = user_id);
