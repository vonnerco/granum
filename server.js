require('dotenv').config();
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3');
const { open } = require('sqlite');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const DEFAULT_MODEL = 'gemini-1.5-flash';
const DEFAULT_DB_PATH = path.join('data', 'text_enhancer.db');

function buildPrompt(text) {
  return `Polish these raw technician notes into a professional, structured format.\nUse bullet points with sections like:\n- Work completed: [list tasks]\n- Cleanup\n- Outcome/Follow-up: [customer notes, next steps]\n\nKeep concise, fix grammar/spelling. Raw notes: "${text}"`;
}

async function initDb(dbPath) {
  fs.mkdirSync(path.dirname(dbPath), { recursive: true });

  const db = await open({
    filename: dbPath,
    driver: sqlite3.Database
  });

  await db.exec(`
    CREATE TABLE IF NOT EXISTS interactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      input_text TEXT NOT NULL,
      enhanced_text TEXT,
      model_used TEXT,
      prompt_tokens INTEGER DEFAULT 0,
      completion_tokens INTEGER DEFAULT 0,
      latency_ms INTEGER,
      status TEXT NOT NULL,
      error_message TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);

  return db;
}

async function logInteraction(db, interaction) {
  await db.run(
    `
      INSERT INTO interactions (
        input_text,
        enhanced_text,
        model_used,
        prompt_tokens,
        completion_tokens,
        latency_ms,
        status,
        error_message
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `,
    [
      interaction.inputText,
      interaction.enhancedText,
      interaction.modelUsed,
      interaction.promptTokens,
      interaction.completionTokens,
      interaction.latencyMs,
      interaction.status,
      interaction.errorMessage
    ]
  );
}

function createGeminiEnhancer(apiKey, modelName = DEFAULT_MODEL) {
  if (!apiKey) {
    throw new Error('Missing GOOGLE_GENERATIVE_AI_API_KEY in environment');
  }

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: modelName });

  return async function enhanceText(text) {
    const prompt = buildPrompt(text);
    const result = await model.generateContent(prompt);
    const response = result.response;
    const usage = response.usageMetadata || {};

    return {
      enhancedText: response.text().trim(),
      modelUsed: modelName,
      promptTokens: usage.promptTokenCount || 0,
      completionTokens: usage.candidatesTokenCount || 0
    };
  };
}

function parseLimit(rawLimit) {
  const limit = Number.parseInt(rawLimit, 10);
  if (Number.isNaN(limit)) {
    return 10;
  }
  return Math.max(1, Math.min(limit, 100));
}

function createApp(options = {}) {
  const app = express();
  const dbPath = options.dbPath || DEFAULT_DB_PATH;
  const enhanceText =
    options.enhanceText ||
    createGeminiEnhancer(process.env.GOOGLE_GENERATIVE_AI_API_KEY, DEFAULT_MODEL);

  app.use(express.json());
  app.use(cors());

  const dbReady = initDb(dbPath);
  app.locals.ready = dbReady;
  dbReady.then((db) => {
    app.locals.db = db;
  });

  app.get('/health', async (_req, res) => {
    await dbReady;
    res.json({ status: 'ok' });
  });

  app.post('/enhance', async (req, res) => {
    const inputText = req.body?.text;

    if (typeof inputText !== 'string' || inputText.trim().length === 0) {
      return res.status(400).json({ error: 'Missing or empty "text" in request body' });
    }

    const text = inputText.trim();
    const startedAt = Date.now();

    try {
      const db = await dbReady;
      const result = await enhanceText(text);
      const latencyMs = Date.now() - startedAt;

      await logInteraction(db, {
        inputText: text,
        enhancedText: result.enhancedText,
        modelUsed: result.modelUsed,
        promptTokens: result.promptTokens,
        completionTokens: result.completionTokens,
        latencyMs,
        status: 'success',
        errorMessage: null
      });

      return res.json({
        enhanced_text: result.enhancedText,
        model_used: result.modelUsed,
        token_usage: {
          prompt_tokens: result.promptTokens,
          completion_tokens: result.completionTokens
        },
        latency_ms: latencyMs
      });
    } catch (error) {
      const latencyMs = Date.now() - startedAt;
      const message = error instanceof Error ? error.message : 'Unknown error';

      try {
        const db = await dbReady;
        await logInteraction(db, {
          inputText: text,
          enhancedText: null,
          modelUsed: DEFAULT_MODEL,
          promptTokens: 0,
          completionTokens: 0,
          latencyMs,
          status: 'failure',
          errorMessage: message
        });
      } catch (logError) {
        console.error('Failed to log interaction:', logError);
      }

      return res.status(500).json({ error: 'Failed to enhance text', details: message });
    }
  });

  app.get('/history', async (req, res) => {
    try {
      const db = await dbReady;
      const limit = parseLimit(req.query.limit);
      const rows = await db.all(
        `
          SELECT
            id,
            input_text,
            enhanced_text,
            model_used,
            prompt_tokens,
            completion_tokens,
            latency_ms,
            status,
            error_message,
            created_at
          FROM interactions
          ORDER BY datetime(created_at) DESC, id DESC
          LIMIT ?
        `,
        [limit]
      );

      return res.json({ history: rows });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      return res.status(500).json({ error: 'Failed to fetch history', details: message });
    }
  });

  return app;
}

async function startServer() {
  const app = createApp();
  const port = Number.parseInt(process.env.PORT || '8000', 10);

  await app.locals.ready;

  return app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
  });
}

if (require.main === module) {
  startServer().catch((error) => {
    console.error('Failed to start server:', error);
    process.exit(1);
  });
}

module.exports = {
  buildPrompt,
  createApp,
  createGeminiEnhancer,
  startServer
};
