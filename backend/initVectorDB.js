import { ChromaClient } from 'chromadb';
import pkg from 'xlsx';
const { readFile } = pkg;
import { OpenAI } from 'openai';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

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
    let collection;
    const collections = await client.listCollections();
    console.log('Available collections:', collections);

    const existingCollection = collections.find(c => c.name === "bokjiro_welfare");
    console.log('Existing collection:', existingCollection);

    if (existingCollection) {
      console.log('Using existing collection');
      collection = await client.getCollection({ name: "bokjiro_welfare" });
      console.log('Skipping data processing as collection already exists');
      return;
    } else {
      console.log('No existing collection found, creating a new one');
      collection = await client.createCollection({
        name: "bokjiro_welfare",
        metadata: { "description": "복지로 복지서비스 정보" }
      });
    }

    const workbook = readFile(path.join(__dirname, 'data/bokjiro_content.xlsx'));
    const sheetName = workbook.SheetNames[0];
    const rawData = pkg.utils.sheet_to_json(workbook.Sheets[sheetName]);

    const validData = rawData.filter(row => row.title && row.sido);
    console.log(`Found ${validData.length} valid entries out of ${rawData.length}`);

    const BATCH_SIZE = 100;
    const MAX_RETRIES = 3;
    const CONCURRENT_BATCHES = 5;

    async function processBatch(batchData, batchIndex) {
      const contents = batchData.map(row => 
        row.gu ? `${row.title} - ${row.sido} ${row.gu}` : `${row.title} - ${row.sido}`
      );

      let retries = 0;
      while (retries < MAX_RETRIES) {
        try {
          const embeddingResponse = await openai.embeddings.create({
            input: contents,
            model: "text-embedding-ada-002"
          });

          await collection.add({
            ids: batchData.map((_, i) => `${batchIndex * BATCH_SIZE + i}`),
            embeddings: embeddingResponse.data.map(e => e.embedding),
            metadatas: batchData.map(row => ({
              title: row.title,
              sido: row.sido,
              gu: row.gu || null
            })),
            documents: contents
          });

          console.log(`Processed batch ${batchIndex + 1}`);
          return true;
        } catch (error) {
          retries++;
          console.error(`Batch ${batchIndex + 1} failed (attempt ${retries}):`, error);
          await new Promise(resolve => setTimeout(resolve, 1000 * retries));
        }
      }
      throw new Error(`Failed to process batch ${batchIndex + 1} after ${MAX_RETRIES} attempts`);
    }

    for (let i = 0; i < validData.length; i += BATCH_SIZE * CONCURRENT_BATCHES) {
      const batchPromises = [];
      
      for (let j = 0; j < CONCURRENT_BATCHES; j++) {
        const startIdx = i + (j * BATCH_SIZE);
        const batchData = validData.slice(startIdx, startIdx + BATCH_SIZE);
        
        if (batchData.length > 0) {
          batchPromises.push(processBatch(batchData, Math.floor(startIdx / BATCH_SIZE)));
        }
      }

      await Promise.all(batchPromises);
    }

    console.log('Vector DB initialization completed successfully');
  } catch (error) {
    console.error('Fatal error initializing vector DB:', error);
    throw error;
  }
}

initializeVectorDB();
