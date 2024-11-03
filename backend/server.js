import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import dotenv from 'dotenv';
import fs from 'fs';

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
  
  // preflight 요청 처리
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

// Assistant 생성
let assistant;
async function createAssistant() {
  assistant = await openai.beta.assistants.create({
    name: "복지자원 안내 가이드",
    instructions: "당신은 복지자원 안내 가이드입니다. 반드시 제공된 복지 정보를 바탕으로 답변하시고 친절하게 답변하세요.",
    model: "gpt-4o-mini",
    tools: [{ type: "file_search" }],
  });
  console.log('Assistant created:', assistant.id);
}

// JSON 파일 읽기 함수
async function readJsonFile() {
  const jsonFilePath = path.join(__dirname, 'data/bokjiro_content.json');
  if (!fs.existsSync(jsonFilePath)) {
    throw new Error('JSON file not found: ' + jsonFilePath);
  }
  return jsonFilePath;
}

// Vector Store 생성 및 파일 업로드
// Vector Store 생성 및 파일 업로드
async function setupVectorStore() {
  try {
    // Vector Store 생성
    const vectorStore = await openai.beta.vectorStores.create({
      name: "Bokjiro Content"
    });
    console.log('Vector Store created:', vectorStore.id);

    // JSON 파일 읽기
    const jsonFilePath = await readJsonFile();
    const fileStream = fs.createReadStream(jsonFilePath);
    
    // 파일 업로드
    const file = await openai.files.create({
      file: fileStream,
      purpose: "assistants"
    });
    console.log('File uploaded:', file.id);

    // Vector Store에 파일 추가
    await openai.beta.vectorStores.fileBatches.createAndPoll(
      vectorStore.id,
      { file_ids: [file.id] }
    );
    console.log('File added to Vector Store');

    // Assistant 업데이트 - Vector Store 연결
    await openai.beta.assistants.update(assistant.id, {
      tool_resources: { 
        file_search: { 
          vector_store_ids: [vectorStore.id] 
        } 
      }
    });
    console.log('Assistant updated with Vector Store');

    return vectorStore;
  } catch (error) {
    console.error('Error in setupVectorStore:', error);
    throw error;
  }
}

// 초기화 함수
async function initialize() {
  try {
    await createAssistant();
    await setupVectorStore();
    console.log('Initialization completed successfully');
  } catch (error) {
    console.error('Initialization failed:', error);
    throw error;
  }
}

// 서버 시작
app.listen(port, '0.0.0.0', async () => {
  try {
    console.log(`Server running at http://0.0.0.0:${port}`);
    await initialize();
  } catch (error) {
    console.error('Failed to start server:', error);
  }
});

// Thread 저장소
const userThreads = new Map();

// 채팅 API 엔드포인트
app.post('/api/chat', async (req, res) => {
  console.log('=== Chat API Request Started ===');
  
  try {
    const { message } = req.body;
    console.log('Received message:', message);

    // Thread 관리
    let thread;
    if (!userThreads.has('default')) {
      thread = await openai.beta.threads.create();
      userThreads.set('default', thread.id);
    } else {
      thread = { id: userThreads.get('default') };
    }

    // 사용자 메시지 생성
    await openai.beta.threads.messages.create(
      thread.id,
      { role: "user", content: message }
    );
    
    // Run 생성 및 실행
    const run = await openai.beta.threads.runs.create(
      thread.id,
      { assistant_id: assistant.id }
    );
    
    // Run 상태 모니터링
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
    
    // 응답 메시지 조회
    const messages = await openai.beta.threads.messages.list(thread.id);
    const lastMessage = messages.data[0];

    res.json({ 
      response: lastMessage.content[0].text.value 
    });

  } catch (error) {
    console.error('Error in chat endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

async function sendMessage(message) {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message })
    });
    
    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

// 정적 파일 서빙 설정
app.use('/images', express.static(path.join(__dirname, 'public/images')));

// CSV 파일 읽기 API
app.get('/api/poverty-data', (req, res) => {
  try {
    const filePath = path.join(__dirname, '../public/data/result1_merge_index_cd_wido_korean.csv');
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const rows = fileContent.split('\n').slice(1); // 헤더 제외
    
    const data = rows.map(row => {
      const cols = row.split(',');
      return {
        시도: cols[3],
        시군구: cols[4],
        경도: cols[28],
        위도: cols[29],
        일반가구수: cols[30],
        일반가구_기준미달비율: cols[31],
        전체가구_주거빈곤가구_비율: cols[33]
      };
    }).filter(item => item.위도 && item.경도);

    res.json(data);
  } catch (error) {
    console.error('Error reading poverty data:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});
