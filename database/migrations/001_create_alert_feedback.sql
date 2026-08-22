CREATE TABLE IF NOT EXISTS alert_feedback (
  id INT PRIMARY KEY AUTO_INCREMENT,
  alert_id VARCHAR(128) NOT NULL,
  gestionnaire_id VARCHAR(128),
  decision ENUM('valide','ajuste','rejette'),
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
