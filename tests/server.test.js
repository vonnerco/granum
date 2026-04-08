const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const request = require('supertest');
const { createApp } = require('../server');

function createTempDbPath(name) {
  const file = `${name}-${Date.now()}-${Math.random().toString(16).slice(2)}.db`;
  return path.join(__dirname, '..', 'data', file);
}

test('POST /enhance returns enhanced text and stores success interaction', async (t) => {
  const dbPath = createTempDbPath('success');
  const app = createApp({
    dbPath,
    enhanceText: async (text) => ({
      enhancedText: `Enhanced: ${text}`,
      modelUsed: 'mock-model',
      promptTokens: 12,
      completionTokens: 7
    })
  });

  await app.locals.ready;

  t.after(async () => {
    await app.locals.db?.close();
    if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
  });

  const enhanceResponse = await request(app)
    .post('/enhance')
    .send({ text: 'fix hvac leak, cleaned area' })
    .expect(200);

  assert.equal(enhanceResponse.body.model_used, 'mock-model');
  assert.equal(enhanceResponse.body.token_usage.prompt_tokens, 12);
  assert.equal(enhanceResponse.body.token_usage.completion_tokens, 7);

  const historyResponse = await request(app).get('/history?limit=1').expect(200);
  assert.equal(historyResponse.body.history.length, 1);
  assert.equal(historyResponse.body.history[0].status, 'success');
  assert.match(historyResponse.body.history[0].input_text, /fix hvac leak/i);
});

test('POST /enhance validates missing text', async (t) => {
  const dbPath = createTempDbPath('validation');
  const app = createApp({
    dbPath,
    enhanceText: async () => ({
      enhancedText: 'unused',
      modelUsed: 'mock-model',
      promptTokens: 0,
      completionTokens: 0
    })
  });

  await app.locals.ready;

  t.after(async () => {
    await app.locals.db?.close();
    if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
  });

  const response = await request(app).post('/enhance').send({}).expect(400);
  assert.match(response.body.error, /missing or empty/i);
});

test('POST /enhance logs failures when LLM call throws', async (t) => {
  const dbPath = createTempDbPath('failure');
  const app = createApp({
    dbPath,
    enhanceText: async () => {
      throw new Error('LLM timeout');
    }
  });

  await app.locals.ready;

  t.after(async () => {
    await app.locals.db?.close();
    if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
  });

  const response = await request(app)
    .post('/enhance')
    .send({ text: 'customer unreachable' })
    .expect(500);

  assert.match(response.body.error, /failed to enhance/i);

  const historyResponse = await request(app).get('/history?limit=1').expect(200);
  assert.equal(historyResponse.body.history.length, 1);
  assert.equal(historyResponse.body.history[0].status, 'failure');
  assert.match(historyResponse.body.history[0].error_message, /timeout/i);
});
