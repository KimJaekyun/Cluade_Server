-- 1945game 데이터베이스 스키마 (MySQL 8 / utf8mb4)
-- 실행: mysql -u <관리자계정> -p < schema.sql
CREATE DATABASE IF NOT EXISTS `1945game`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `1945game`;

-- 플레이어 계정
CREATE TABLE IF NOT EXISTS players (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(20)  NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login    DATETIME     NULL,
  UNIQUE KEY uq_players_username (username)
) ENGINE=InnoDB;

-- 플레이 1판 = 1행 (랭킹 + 통계 겸용). 비로그인 플레이도 통계용으로 기록(player_id NULL)
CREATE TABLE IF NOT EXISTS play_logs (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  player_id     INT UNSIGNED NULL,
  score         INT UNSIGNED NOT NULL,
  stage_reached TINYINT UNSIGNED NOT NULL,
  cleared       TINYINT(1)   NOT NULL DEFAULT 0,
  duration_sec  INT UNSIGNED NOT NULL,
  kills         INT UNSIGNED NOT NULL DEFAULT 0,
  bombs_used    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  cause         VARCHAR(20)  NOT NULL DEFAULT 'unknown', -- clear / enemy_bullet / collision / quit
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_logs_score (score DESC),
  KEY idx_logs_player (player_id, score),
  KEY idx_logs_created (created_at),
  CONSTRAINT fk_logs_player FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 게임 설정(밸런스) : key -> JSON
CREATE TABLE IF NOT EXISTS game_config (
  cfg_key    VARCHAR(40) NOT NULL PRIMARY KEY,
  cfg_value  JSON        NOT NULL,
  updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO game_config (cfg_key, cfg_value) VALUES
 ('player', JSON_OBJECT('lives', 3, 'bombs', 3)),
 ('enemies', JSON_OBJECT(
    'small',  JSON_OBJECT('hp', 2,  'score', 100, 'drop', 0.10),
    'zigzag', JSON_OBJECT('hp', 3,  'score', 200, 'drop', 0.15),
    'swoop',  JSON_OBJECT('hp', 3,  'score', 200, 'drop', 0.15),
    'medium', JSON_OBJECT('hp', 16, 'score', 700, 'drop', 0.90))),
 ('boss', JSON_OBJECT('baseHp', 260, 'hpPerStage', 160, 'scorePerStage', 5000))
ON DUPLICATE KEY UPDATE cfg_key = cfg_key;

-- 앱 전용 계정 (비밀번호는 직접 바꿔서 실행하세요). 이 DB에만 권한 부여.
-- CREATE USER IF NOT EXISTS 'game1945'@'localhost' IDENTIFIED BY '여기에_강한_비밀번호';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON `1945game`.* TO 'game1945'@'localhost';
-- FLUSH PRIVILEGES;
