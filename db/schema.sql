-- PostgreSQL schema for React + Node.js hierarchy automation service

CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE api_sessions (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  customer_id TEXT NOT NULL,
  -- 민감정보는 암호화 저장 또는 인메모리 토큰 참조 권장
  encrypted_access_license TEXT,
  encrypted_secret_key TEXT,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE hierarchy_templates (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('BRAND_GENERAL', 'DEVICE_SPECIFIC', 'SHOPPING_FOCUS')),
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE hierarchy_runs (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  template_id UUID REFERENCES hierarchy_templates(id) ON DELETE SET NULL,
  status TEXT NOT NULL CHECK (status IN ('PREVIEWED', 'RUNNING', 'COMPLETED', 'FAILED', 'PARTIAL_FAILED')),
  preview_tree JSONB,
  total_campaigns INT NOT NULL DEFAULT 0,
  total_adgroups INT NOT NULL DEFAULT 0,
  total_keywords INT NOT NULL DEFAULT 0,
  error_summary JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);

CREATE TABLE campaigns (
  id UUID PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES hierarchy_runs(id) ON DELETE CASCADE,
  external_campaign_id TEXT,
  campaign_name TEXT NOT NULL,
  category TEXT,
  device_type TEXT CHECK (device_type IN ('PC', 'MOBILE', 'ALL')),
  keyword_intent TEXT CHECK (keyword_intent IN ('BRAND', 'GENERAL', 'MIXED')),
  budget_daily NUMERIC(14,2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE adgroups (
  id UUID PRIMARY KEY,
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  external_adgroup_id TEXT,
  adgroup_name TEXT NOT NULL,
  media_type TEXT,
  gender_target TEXT CHECK (gender_target IN ('MALE', 'FEMALE', 'ALL')),
  age_include JSONB,
  age_exclude JSONB,
  region_include JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE keywords (
  id UUID PRIMARY KEY,
  adgroup_id UUID NOT NULL REFERENCES adgroups(id) ON DELETE CASCADE,
  external_keyword_id TEXT,
  keyword TEXT NOT NULL,
  match_type TEXT,
  bid_amount NUMERIC(14,2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_runs_workspace_created_at ON hierarchy_runs(workspace_id, created_at DESC);
CREATE INDEX idx_campaigns_run_id ON campaigns(run_id);
CREATE INDEX idx_adgroups_campaign_id ON adgroups(campaign_id);
CREATE INDEX idx_keywords_adgroup_id ON keywords(adgroup_id);
