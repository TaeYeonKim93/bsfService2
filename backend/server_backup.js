import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';
import dotenv from 'dotenv';
import { ChromaClient } from 'chromadb';

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
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
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
    model: "gpt-3.5-turbo"
  });
  console.log('Assistant created:', assistant.id);
}
createAssistant();

// Thread 저장소
const userThreads = new Map();

// ChromaDB 클라이언트 추가
const chroma = new ChromaClient({
  path: "http://chromadb:8000"  // Docker 서비스 이름으로 수정
});
app.post('/api/chat', async (req, res) => {
  console.log('=== Chat API Request Started ===');
  console.log(`Timestamp: ${new Date().toISOString()}`);
  
  try {
    const { message } = req.body;
    console.log('Received message:', message);
    
    // 컬렉션 존재 여부 확인
    console.log('Checking for collection existence...');
    const collections = await chroma.listCollections();
    const collectionExists = collections.some(c => c.name === "bokjiro_welfare");
    console.log('Collection exists:', collectionExists);
    
    if (!collectionExists) {
      console.error('Collection not found: bokjiro_welfare');
      throw new Error("Collection 'bokjiro_welfare' not found");
    }
    
    // 컬렉션 가져오기
    console.log('Attempting to get collection...');
    const collection = await chroma.getCollection({
      name: "bokjiro_welfare"
    });
    console.log('Successfully retrieved collection');

   // 임베딩 생성 부분 수정
    console.log('Generating embeddings for message...');
    const embeddingText = `복지서비스 검색: ${message}`;  // 검색 의도를 명시적으로 포함
    const embedding = await openai.embeddings.create({ 
      input: embeddingText,
      model: "text-embedding-ada-002" 
    });
    console.log('Successfully generated embeddings');
    
    
    // 벡터 검색 부분 수정
    console.log('Performing vector search...');
    const searchResults = await collection.query({
      queryEmbeddings: embedding.data[0].embedding,
      nResults: 30,  // 더 많은 결과를 가져옴
      minScore: 1  // 임계값을 낮춰서 더 많은 결과를 포함
    });
    console.log('Search completed. Number of results:', searchResults.documents[0].length);

    
    // 컨텍스트 구성 부분 수정
    console.log('Building context from search results...');
    const results = searchResults.documents[0].map((doc, idx) => ({
      text: doc,
      metadata: searchResults.metadatas[0][idx],
      score: searchResults.distances[0][idx]
    }));

    
    // 검색 결과 정렬 및 필터링
    const sortedResults = results
    .sort((a, b) => b.score - a.score)  // 유사도 점수로 정렬
    .slice(0, 10);  // 상위 10개 결과만 선택


    const context = sortedResults.map(result => {
      const contextString = result.metadata.gu 
        ? `${result.metadata.title} (${result.metadata.sido} ${result.metadata.gu})`
        : `${result.metadata.title} (${result.metadata.sido})`;
      console.log('Added context item:', contextString);
      return contextString;
    }).join('\n');

    // Thread 관리
    console.log('Managing user thread...');
    let thread;
    if (!userThreads.has('default')) {
      console.log('Creating new thread...');
      thread = await openai.beta.threads.create();
      userThreads.set('default', thread.id);
      console.log('New thread created with ID:', thread.id);
    } else {
      thread = { id: userThreads.get('default') };
      console.log('Using existing thread with ID:', thread.id);
    }
    
// Assistant 메시지 개선
const messageContent = `
사용자 질문: ${message}
추천 복지정보:
${context}
`;
    
    await openai.beta.threads.messages.create(
      thread.id,
      { 
        role: "assistant", 
        content: messageContent
      }
    );
    console.log('Message successfully added to thread');
    
    // Run 생성 및 실행
    console.log('Creating and starting run...');
    const run = await openai.beta.threads.runs.create(
      thread.id,
      { assistant_id: assistant.id }
    );
    console.log('Run created with ID:', run.id);
    
    // Run 상태 모니터링
    console.log('Monitoring run status...');
    let runStatus = await openai.beta.threads.runs.retrieve(
      thread.id,
      run.id
    );
    
    while (runStatus.status !== 'completed') {
      console.log('Current run status:', runStatus.status);
      await new Promise(resolve => setTimeout(resolve, 1000));
      runStatus = await openai.beta.threads.runs.retrieve(
        thread.id,
        run.id
      );
    }
    console.log('Run completed successfully');
    
    // 응답 메시지 조회
    console.log('Retrieving response message...');
    const messages = await openai.beta.threads.messages.list(thread.id);
    const lastMessage = messages.data[0];
    console.log('Retrieved response:', lastMessage.content[0].text.value);

    console.log('=== Chat API Request Completed Successfully ===');
    res.json({ 
      response: lastMessage.content[0].text.value 
    });
  
  } catch (error) {
    console.error('=== Chat API Error ===');
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    res.status(500).json({ error: error.message });
  }
});

// 정적 파일 서빙
app.use(express.static(path.join(__dirname, '../dist')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../dist/index.html'));
});

// ChromaDB 연결 함수
// ChromaDB 연결 함수
async function connectToChroma(retries = 5, delay = 5000) {
  const collectionName = "bokjiro_welfare";
  
  for (let i = 0; i < retries; i++) {
    try {
      // 먼저 모든 컬렉션 목록을 가져옴
      const collections = await chroma.listCollections();
      console.log('Available collections:', collections);
      
      // 기존 컬렉션 찾기
      const existingCollection = collections.find(c => c.name === collectionName);
      
      let collection;
      if (existingCollection) {
        console.log('Found existing collection:', existingCollection.name);
        collection = await chroma.getCollection({
          name: collectionName
        });
      } else {
        console.log('Creating new collection:', collectionName);
        collection = await chroma.createCollection({
          name: collectionName,
          metadata: { "description": "복지로 복지서비스 정보" }
        });
      }
      
      console.log('Successfully connected to ChromaDB');
      return collection;
      
    } catch (error) {
      console.log(`Failed to connect to ChromaDB (attempt ${i + 1}/${retries}):`, error.message);
      console.error('Full error:', error);
      
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  throw new Error('Failed to connect to ChromaDB after multiple attempts');
}

// 서버 시작 전에 ChromaDB 연결 확인
app.listen(port, '0.0.0.0', async () => {
  try {
    await connectToChroma();
    console.log(`Server running at http://0.0.0.0:${port}`);
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
});
