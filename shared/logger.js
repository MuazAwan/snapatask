const fs = require('fs');
const path = require('path');

const LOG_DIR = '/opt/snapatask/logs';
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

function timestamp() {
  return new Date().toISOString();
}

function writeLog(level, agent, message, data = null) {
  const entry = {
    timestamp: timestamp(),
    level,
    agent,
    message,
    ...(data && { data })
  };
  const line = JSON.stringify(entry);
  console.log(line);
  const logFile = path.join(LOG_DIR, `${new Date().toISOString().split('T')[0]}.log`);
  fs.appendFileSync(logFile, line + '\n');
}

function createLogger(agentName) {
  return {
    info: (msg, data) => writeLog('INFO', agentName, msg, data),
    warn: (msg, data) => writeLog('WARN', agentName, msg, data),
    error: (msg, data) => writeLog('ERROR', agentName, msg, data),
    debug: (msg, data) => writeLog('DEBUG', agentName, msg, data),
  };
}

module.exports = { createLogger };
