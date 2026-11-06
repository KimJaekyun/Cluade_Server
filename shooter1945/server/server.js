'use strict';
require('dotenv').config();
const path = require('path');
const crypto = require('crypto');
const express = require('express');
const rateLimit = require('express-rate-limit');
const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const { DB_HOST = 'localhost', DB_PORT = 3306, DB_USER, DB_PASSWORD, DB_NAME = '1945game', JWT_SECRET, PORT = 3000 } = process.env;
if (!DB_USER || !JWT_SECRET || JWT_SECRET.length < 24) {
  console.error('환경변수 DB_USER / DB_PASSWORD / JWT_SECRET(24자 이상)을 .env 에 설정하세요.');
  process.exit(1);
}

const pool = mysql.createPool({
  host: DB_HOST, port: Number(DB_PORT), user: DB_USER, password: DB_PASSWORD, database: DB_NAME,
  waitForConnections: true, connectionLimit: 10, charset: 'utf8mb4',
});

const app = express();
app.set('trust proxy', 1); // nginx 뒤에서 실행
app.disable('x-powered-by');
app.use(express.json({ limit: '10kb' }));

const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, limit: 30, standardHeaders: true, legacyHeaders: false });
const runLimiter = rateLimit({ windowMs: 60 * 1000, limit: 20, standardHeaders: true, legacyHeaders: false });

const wrap = fn => (req, res) => fn(req, res).catch(err => {
  console.error(err);
  res.status(500).json({ error: '서버 오류가 발생했습니다.' });
});

// ---------- 인증 ----------
const sign = p => jwt.sign({ id: p.id, username: p.username }, JWT_SECRET, { expiresIn: '30d' });
function auth(required) {
  return (req, res, next) => {
    const h = req.headers.authorization || '';
    const token = h.startsWith('Bearer ') ? h.slice(7) : null;
    if (token) {
      try { req.user = jwt.verify(token, JWT_SECRET); } catch (e) {
        if (required) return res.status(401).json({ error: '로그인이 만료되었습니다.' });
      }
    }
    if (required && !req.user) return res.status(401).json({ error: '로그인이 필요합니다.' });
    next();
  };
}
const USER_RE = /^[A-Za-z0-9가-힣_]{2,12}$/;

app.post('/api/register', authLimiter, wrap(async (req, res) => {
  const { username, password } = req.body || {};
  if (typeof username !== 'string' || !USER_RE.test(username))
    return res.status(400).json({ error: '닉네임은 2~12자 (한글/영문/숫자/_) 입니다.' });
  if (typeof password !== 'string' || password.length < 6 || password.length > 72)
    return res.status(400).json({ error: '비밀번호는 6~72자여야 합니다.' });
  const hash = await bcrypt.hash(password, 10);
  try {
    const [r] = await pool.execute('INSERT INTO players (username, password_hash, last_login) VALUES (?, ?, NOW())', [username, hash]);
    const p = { id: r.insertId, username };
    res.json({ token: sign(p), username });
  } catch (e) {
    if (e.code === 'ER_DUP_ENTRY') return res.status(409).json({ error: '이미 사용 중인 닉네임입니다.' });
    throw e;
  }
}));

app.post('/api/login', authLimiter, wrap(async (req, res) => {
  const { username, password } = req.body || {};
  if (typeof username !== 'string' || typeof password !== 'string')
    return res.status(400).json({ error: '닉네임과 비밀번호를 입력하세요.' });
  const [rows] = await pool.execute('SELECT id, username, password_hash FROM players WHERE username = ?', [username]);
  const p = rows[0];
  if (!p || !(await bcrypt.compare(password, p.password_hash)))
    return res.status(401).json({ error: '닉네임 또는 비밀번호가 올바르지 않습니다.' });
  await pool.execute('UPDATE players SET last_login = NOW() WHERE id = ?', [p.id]);
  res.json({ token: sign(p), username: p.username });
}));

// ---------- 게임 설정 ----------
app.get('/api/config', wrap(async (req, res) => {
  const [rows] = await pool.query('SELECT cfg_key, cfg_value FROM game_config');
  const cfg = {};
  for (const r of rows) cfg[r.cfg_key] = typeof r.cfg_value === 'string' ? JSON.parse(r.cfg_value) : r.cfg_value;
  res.set('Cache-Control', 'public, max-age=60').json(cfg);
}));

// ---------- 플레이 기록 / 랭킹 ----------
const int = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
const CAUSES = ['clear', 'enemy_bullet', 'collision', 'quit'];

app.post('/api/runs', runLimiter, auth(false), wrap(async (req, res) => {
  const { score, stage, cleared, duration, kills, bombs, cause } = req.body || {};
  if (!int(score, 0, 2000000) || !int(stage, 1, 4) || !int(duration, 0, 7200) ||
      !int(kills, 0, 5000) || !int(bombs, 0, 100) || !CAUSES.includes(cause) || typeof cleared !== 'boolean')
    return res.status(400).json({ error: '잘못된 기록입니다.' });
  // 간단한 부정 기록 방지: 시간 대비 비현실적 점수 거부
  if (score > 0 && (duration < 10 || score > duration * 2500))
    return res.status(400).json({ error: '유효하지 않은 기록입니다.' });
  const playerId = req.user ? req.user.id : null;
  const [r] = await pool.execute(
    'INSERT INTO play_logs (player_id, score, stage_reached, cleared, duration_sec, kills, bombs_used, cause) VALUES (?,?,?,?,?,?,?,?)',
    [playerId, score, stage, cleared ? 1 : 0, duration, kills, bombs, cause]);
  let rank = null;
  if (playerId) {
    const [rk] = await pool.execute(
      `SELECT COUNT(*) + 1 AS r FROM (SELECT player_id, MAX(score) s FROM play_logs WHERE player_id IS NOT NULL GROUP BY player_id) t
       WHERE t.s > (SELECT MAX(score) FROM play_logs WHERE player_id = ?)`, [playerId]);
    rank = Number(rk[0].r);
  }
  res.json({ id: r.insertId, rank });
}));

app.get('/api/ranking', wrap(async (req, res) => {
  const limit = Math.min(50, Math.max(1, parseInt(req.query.limit, 10) || 10));
  const [rows] = await pool.query(
    `SELECT p.username, t.best AS score,
            (SELECT MAX(l.stage_reached) FROM play_logs l WHERE l.player_id = p.id AND l.score = t.best) AS stage
     FROM (SELECT player_id, MAX(score) best FROM play_logs WHERE player_id IS NOT NULL GROUP BY player_id) t
     JOIN players p ON p.id = t.player_id
     ORDER BY t.best DESC, p.id ASC LIMIT ?`, [limit]);
  res.set('Cache-Control', 'no-store').json(rows.map((r, i) => ({ rank: i + 1, username: r.username, score: r.score, stage: r.stage })));
}));

app.get('/api/me', auth(true), wrap(async (req, res) => {
  const [rows] = await pool.execute(
    `SELECT COUNT(*) AS plays, COALESCE(MAX(score),0) AS best, COALESCE(SUM(duration_sec),0) AS total_sec,
            COALESCE(SUM(kills),0) AS kills, COALESCE(SUM(cleared),0) AS clears
     FROM play_logs WHERE player_id = ?`, [req.user.id]);
  const s = rows[0];
  res.set('Cache-Control', 'no-store').json({
    username: req.user.username, plays: Number(s.plays), best: Number(s.best),
    totalSec: Number(s.total_sec), kills: Number(s.kills), clears: Number(s.clears),
  });
}));

// ---------- 관리자 대시보드 ----------
// ADMIN_PASSWORD 가 .env 에 없으면 관리자 기능은 꺼져 있음
// 쉼표(,)로 여러 개 지정 가능: ADMIN_PASSWORD=비번1,비번2  (비밀번호 자체에는 쉼표를 쓸 수 없음)
const ADMIN_PASSWORDS = (process.env.ADMIN_PASSWORD || '').split(',').map(s => s.trim()).filter(Boolean);
const adminLimiter = rateLimit({ windowMs: 15 * 60 * 1000, limit: 10, standardHeaders: true, legacyHeaders: false });
const sha = s => crypto.createHash('sha256').update(String(s)).digest();

app.post('/api/admin/login', adminLimiter, (req, res) => {
  if (!ADMIN_PASSWORDS.length) return res.status(503).json({ error: '관리자 기능이 설정되지 않았습니다.' });
  const pw = (req.body || {}).password;
  // 모든 후보를 끝까지 비교해 어느 것이 맞는지 응답 시간으로 드러나지 않게 함
  const ok = typeof pw === 'string' && ADMIN_PASSWORDS.map(a => crypto.timingSafeEqual(sha(pw), sha(a))).some(Boolean);
  if (!ok) return res.status(401).json({ error: '비밀번호가 올바르지 않습니다.' });
  res.json({ token: jwt.sign({ admin: true }, JWT_SECRET, { expiresIn: '12h' }) });
});

function adminAuth(req, res, next) {
  const h = req.headers.authorization || '';
  try {
    const p = jwt.verify(h.startsWith('Bearer ') ? h.slice(7) : '', JWT_SECRET);
    if (p && p.admin === true) return next();
  } catch (e) { /* fallthrough */ }
  res.status(401).json({ error: '관리자 로그인이 필요합니다.' });
}

app.get('/api/admin/stats', adminAuth, wrap(async (req, res) => {
  // DB 서버 시간대와 상관없이 한국시간(KST)으로 날짜를 계산하기 위한 보정(분)
  const one = async (sql, params) => (await pool.query(sql, params))[0][0];
  const tz = await one('SELECT TIMESTAMPDIFF(MINUTE, UTC_TIMESTAMP(), NOW()) AS off');
  const sh = 540 - Number(tz.off);
  const s = await one(
    `SELECT COUNT(*) plays, COALESCE(SUM(player_id IS NULL),0) guest_plays, COALESCE(AVG(score),0) avg_score,
            COALESCE(MAX(score),0) max_score, COALESCE(AVG(cleared),0) clear_rate, COALESCE(AVG(duration_sec),0) avg_sec,
            COALESCE(SUM(DATE(created_at + INTERVAL ? MINUTE) = DATE(NOW() + INTERVAL ? MINUTE)),0) today
     FROM play_logs`, [sh, sh]);
  const pl = await one(
    `SELECT COUNT(*) registered,
            COALESCE(SUM(DATE(created_at + INTERVAL ? MINUTE) = DATE(NOW() + INTERVAL ? MINUTE)),0) new_today FROM players`, [sh, sh]);

  const [dailyPlays] = await pool.query(
    `SELECT DATE_FORMAT(created_at + INTERVAL ? MINUTE, '%Y-%m-%d') d, COUNT(*) c FROM play_logs
     WHERE created_at >= NOW() - INTERVAL 31 DAY GROUP BY d`, [sh]);
  const [dailyNew] = await pool.query(
    `SELECT DATE_FORMAT(created_at + INTERVAL ? MINUTE, '%Y-%m-%d') d, COUNT(*) c FROM players
     WHERE created_at >= NOW() - INTERVAL 31 DAY GROUP BY d`, [sh]);
  const pm = Object.fromEntries(dailyPlays.map(r => [r.d, Number(r.c)]));
  const nm = Object.fromEntries(dailyNew.map(r => [r.d, Number(r.c)]));
  const daily = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(Date.now() + 9 * 3600e3 - i * 86400e3).toISOString().slice(0, 10);
    daily.push({ date: d, plays: pm[d] || 0, newPlayers: nm[d] || 0 });
  }

  const [stages] = await pool.query('SELECT stage_reached s, COUNT(*) c FROM play_logs GROUP BY s ORDER BY s');
  const [causes] = await pool.query('SELECT cause, COUNT(*) c FROM play_logs GROUP BY cause');
  const [ranking] = await pool.query(
    `SELECT p.username, t.best AS score, t.plays,
            (SELECT MAX(l.stage_reached) FROM play_logs l WHERE l.player_id = p.id AND l.score = t.best) AS stage
     FROM (SELECT player_id, MAX(score) best, COUNT(*) plays FROM play_logs WHERE player_id IS NOT NULL GROUP BY player_id) t
     JOIN players p ON p.id = t.player_id ORDER BY t.best DESC, p.id ASC LIMIT 20`);
  const [recent] = await pool.query(
    `SELECT l.id, COALESCE(p.username, '') username, l.score, l.stage_reached stage, l.cleared, l.duration_sec,
            l.kills, l.bombs_used, l.cause, DATE_FORMAT(l.created_at + INTERVAL ? MINUTE, '%m-%d %H:%i') at
     FROM play_logs l LEFT JOIN players p ON p.id = l.player_id ORDER BY l.id DESC LIMIT 50`, [sh]);

  res.set('Cache-Control', 'no-store').json({
    summary: {
      plays: Number(s.plays), guestPlays: Number(s.guest_plays), avgScore: Math.round(Number(s.avg_score)),
      maxScore: Number(s.max_score), clearRate: Number(s.clear_rate), avgSec: Math.round(Number(s.avg_sec)),
      today: Number(s.today), registered: Number(pl.registered), newToday: Number(pl.new_today),
    },
    daily,
    stages: stages.map(r => ({ stage: r.s, count: Number(r.c) })),
    causes: causes.map(r => ({ cause: r.cause, count: Number(r.c) })),
    ranking: ranking.map((r, i) => ({ rank: i + 1, username: r.username, score: r.score, stage: r.stage, plays: Number(r.plays) })),
    recent: recent.map(r => ({ ...r, cleared: !!r.cleared })),
  });
}));

app.get('/dashboard', (req, res) => res.sendFile(path.join(__dirname, '..', 'web', 'dashboard.html')));

app.get('/api/health', wrap(async (req, res) => { await pool.query('SELECT 1'); res.json({ ok: true }); }));

// ---------- 정적 파일 (게임 클라이언트) ----------
app.use(express.static(path.join(__dirname, '..', 'web')));

app.listen(Number(PORT), () => console.log(`1945game server listening on :${PORT}`));
