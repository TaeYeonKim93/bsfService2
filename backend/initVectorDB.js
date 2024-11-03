import { ChromaClient } from 'chromadb';
import { OpenAI } from 'openai';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const client = new ChromaClient({
  path: "http://chromadb:8000"  // Docker 서비스 이름으로 수정
});
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

async function initializeVectorDB() {
  try {
    // ChromaDB 컬렉션 초기화 부분은 동일
    let collection;
    const collections = await client.listCollections();
    const existingCollection = collections.find(c => c.name === "bokjiro_welfare");

    if (existingCollection) {
      console.log('기존 컬렉션 사용');
      collection = await client.getCollection({ name: "bokjiro_welfare" });
      return;
    }

    console.log('새 컬렉션 생성');
    collection = await client.createCollection({
      name: "bokjiro_welfare",
      metadata: { "description": "복지로 복지서비스 정보" }
    });

    // 분할된 JSON 파일들 읽기
    const dataDir = path.join(__dirname, 'data');
    const files = fs.readdirSync(dataDir)
      .filter(file => file.startsWith('bokjiro_content_part') && file.endsWith('.json'));

    console.log(`총 ${files.length}개의 파일 처리 예정`);

    // 설정
    const BATCH_SIZE = 100;
    const MAX_RETRIES = 3;
    const CONCURRENT_BATCHES = 5;

    // 각 파일 처리
    for (const file of files) {
      const filePath = path.join(dataDir, file);
      const fileData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
      console.log(`${file} 처리 중... (${fileData.length}개 항목)`);

      // 기존 배치 처리 로직 사용
      for (let i = 0; i < fileData.length; i += BATCH_SIZE * CONCURRENT_BATCHES) {
        const batchPromises = [];
        
        for (let j = 0; j < CONCURRENT_BATCHES; j++) {
          const startIdx = i + (j * BATCH_SIZE);
          const batchData = fileData.slice(startIdx, startIdx + BATCH_SIZE);
          
          if (batchData.length > 0) {
            batchPromises.push(processBatch(batchData, Math.floor(startIdx / BATCH_SIZE)));
          }
        }

        await Promise.all(batchPromises);
      }
    }

    console.log('Vector DB 초기화 완료');
  } catch (error) {
    console.error('Vector DB 초기화 오류:', error);
    throw error;
  }
}

// 함수 실행
initializeVectorDB();
