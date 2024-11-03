import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 8000;

// JSON 파싱을 위한 미들웨어
app.use(express.json());

// CORS 설정
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// OpenAI 설정
console.log('OPENAI_API_KEY:', process.env.OPENAI_API_KEY ? 'exists' : 'not found');
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Assistant ID 상수 정의
const ASSISTANT_ID = 'asst_vNHtPk1wDYvRprgiF0rbrifY';
let assistant;

// Assistant 초기화
async function initialize() {
  try {
    assistant = await openai.beta.assistants.retrieve(ASSISTANT_ID);
    console.log('Assistant retrieved:', assistant.id);
  } catch (error) {
    console.error('Assistant 초기화 실패:', error);
    throw error;
  }
}

// Thread 저장소
const userThreads = new Map();

// 채팅 API 엔드포인트
app.post('/api/chat', async (req, res) => {
  console.log('=== Chat API Request Started ===');
  
  try {
    const { message } = req.body;
    console.log('Received message:', message);

    let thread;
    if (!userThreads.has('default')) {
      thread = await openai.beta.threads.create();
      userThreads.set('default', thread.id);
    } else {
      thread = { id: userThreads.get('default') };
    }

    await openai.beta.threads.messages.create(
      thread.id,
      { role: "user", content: message }
    );
    
    const run = await openai.beta.threads.runs.create(
      thread.id,
      { assistant_id: ASSISTANT_ID }
    );
    
    let runStatus = await openai.beta.threads.runs.retrieve(
      thread.id,
      run.id
    );
    
    while (runStatus.status !== 'completed') {
      await new Promise(resolve => setTimeout(resolve, 1000));
      runStatus = await openai.beta.threads.runs.retrieve(
        thread.id,
        run.id
      );
    }
    
    const messages = await openai.beta.threads.messages.list(thread.id);
    const lastMessage = messages.data[0];

    res.json({ 
      response: lastMessage.content[0].text.value 
    });
    
  } catch (error) {
    console.error('Chat API Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// 서버 시작
app.listen(port, '0.0.0.0', async () => {
  try {
    console.log(`Server running at http://0.0.0.0:${port}`);
    await initialize();
  } catch (error) {
    console.error('Failed to start server:', error);
  }
});
