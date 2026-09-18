-- Local-development roles only. Hosted credentials are provisioned outside source control.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'identity_service') THEN
    CREATE ROLE identity_service LOGIN PASSWORD 'identity_service';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'learning_service') THEN
    CREATE ROLE learning_service LOGIN PASSWORD 'learning_service';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'assessment_service') THEN
    CREATE ROLE assessment_service LOGIN PASSWORD 'assessment_service';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'competency_service') THEN
    CREATE ROLE competency_service LOGIN PASSWORD 'competency_service';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'content_service') THEN
    CREATE ROLE content_service LOGIN PASSWORD 'content_service';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'labs_service') THEN
    CREATE ROLE labs_service LOGIN PASSWORD 'labs_service';
  END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS identity AUTHORIZATION identity_service;
CREATE SCHEMA IF NOT EXISTS learning AUTHORIZATION learning_service;
CREATE SCHEMA IF NOT EXISTS assessment AUTHORIZATION assessment_service;
CREATE SCHEMA IF NOT EXISTS competency AUTHORIZATION competency_service;
CREATE SCHEMA IF NOT EXISTS content AUTHORIZATION content_service;
CREATE SCHEMA IF NOT EXISTS labs AUTHORIZATION labs_service;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA identity, learning, assessment, competency, content, labs FROM PUBLIC;

GRANT CONNECT ON DATABASE igot TO identity_service, learning_service, assessment_service, competency_service, content_service, labs_service;
GRANT USAGE, CREATE ON SCHEMA identity TO identity_service;
GRANT USAGE, CREATE ON SCHEMA learning TO learning_service;
GRANT USAGE, CREATE ON SCHEMA assessment TO assessment_service;
GRANT USAGE, CREATE ON SCHEMA competency TO competency_service;
GRANT USAGE, CREATE ON SCHEMA content TO content_service;
GRANT USAGE, CREATE ON SCHEMA labs TO labs_service;
