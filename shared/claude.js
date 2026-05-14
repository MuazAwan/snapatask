require('dotenv').config({ path: '/opt/snapatask/.env' });
const Anthropic = require('@anthropic-ai/sdk');

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

async function askSonnet(systemPrompt, userMessage, maxTokens = 1000) {
  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: maxTokens,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    });
    return response.content[0].text;
  } catch (err) {
    console.error('Claude Sonnet error:', err.message);
    throw err;
  }
}

async function askHaiku(systemPrompt, userMessage, maxTokens = 500) {
  try {
    const response = await client.messages.create({
      model: 'claude-haiku-4-5',
      max_tokens: maxTokens,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    });
    return response.content[0].text;
  } catch (err) {
    console.error('Claude Haiku error:', err.message);
    throw err;
  }
}

async function askForJSON(systemPrompt, userMessage, useHaiku = false) {
  const fn = useHaiku ? askHaiku : askSonnet;
  const raw = await fn(
    systemPrompt + '\n\nCRITICAL: Respond with valid JSON only. No markdown, no explanation, no backticks.',
    userMessage,
    1500
  );
  try {
    return JSON.parse(raw.trim());
  } catch (err) {
    console.error('Claude JSON parse error. Raw response:', raw.substring(0, 200));
    throw new Error('Claude did not return valid JSON');
  }
}

module.exports = { askSonnet, askHaiku, askForJSON };
