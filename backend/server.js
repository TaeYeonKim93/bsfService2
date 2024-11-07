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
const ASSISTANT_IDS = {
  RESOURCE: 'asst_vNHtPk1wDYvRprgiF0rbrifY',
  CRISIS: 'asst_UwUD33RMWSw2ZsJwQzv5itYU'
};

// Assistant 초기화 수정
async function initialize() {
  try {
    // 두 어시스턴트 모두 초기화
    const resourceAssistant = await openai.beta.assistants.retrieve(ASSISTANT_IDS.RESOURCE);
    const crisisAssistant = await openai.beta.assistants.retrieve(ASSISTANT_IDS.CRISIS);
    console.log('Assistants retrieved:', {
      resource: resourceAssistant.id,
      crisis: crisisAssistant.id
    });
  } catch (error) {
    console.error('Assistant 초기화 실패:', error);
    throw error;
  }
}

// Thread 저장소
const userThreads = new Map();

// checkRunStatus 함수 추가
async function checkRunStatus(threadId, runId) {
    try {
        const run = await openai.beta.threads.runs.retrieve(threadId, runId);
        console.log('Run status check:', {
            status: run.status,
            threadId: threadId,
            runId: runId,
            startTime: run.started_at,
            completionTime: run.completed_at
        });
        return run;
    } catch (error) {
        console.error('Run status check failed:', {
            error: error.message,
            type: error.type,
            threadId: threadId,
            runId: runId,
            stack: error.stack
        });
        throw error;
    }
}

// 채팅 API 엔드포인트 수정
app.post('/api/chat', async (req, res) => {
  console.log('=== Chat API Request Started ===');
  console.log('Request body:', req.body);
  
  try {
    const { message, assistantId } = req.body;
    console.log('Received message:', message);
    console.log('Selected Assistant ID:', assistantId);

    // assistantId 유효성 검사
    if (!Object.values(ASSISTANT_IDS).includes(assistantId)) {
      throw new Error('Invalid Assistant ID');
    }

    let thread;
    if (!userThreads.has('default')) {
      console.log('Creating new thread...');
      thread = await openai.beta.threads.create();
      userThreads.set('default', thread.id);
      console.log('Created new thread:', thread.id);
    } else {
      thread = { id: userThreads.get('default') };
      console.log('Using existing thread:', thread.id);
    }

    console.log('Creating user message...');
    await openai.beta.threads.messages.create(
      thread.id,
      { role: "user", content: message }
    );
    
    console.log('Creating new run with assistant:', assistantId);
    const run = await openai.beta.threads.runs.create(
      thread.id,
      { assistant_id: assistantId }  // 선택된 어시스턴트 ID 사용
    );
    console.log('New run created:', run.id);
    
    let runStatus = await openai.beta.threads.runs.retrieve(
      thread.id,
      run.id
    );
    console.log('Initial run status:', runStatus.status);
    
    let functionCallData = null;
    
    while (runStatus.status !== 'completed') {
      console.log('Current run status:', runStatus.status);
      
      if (runStatus.status === 'requires_action') {
        console.log('Action required:', runStatus.required_action);
        const toolCalls = runStatus.required_action.submit_tool_outputs.tool_calls;
        console.log('Tool calls:', toolCalls);
        
        if (toolCalls[0].function) {
          functionCallData = {
            name: toolCalls[0].function.name,
            arguments: JSON.parse(toolCalls[0].function.arguments)
          };
          console.log('Function call data:', functionCallData);
          
          if (functionCallData.name === 'focusLocation') {
            console.log('Processing focusLocation...');
            const toolOutputs = [{
              tool_call_id: toolCalls[0].id,
              output: JSON.stringify({
                success: true,
                location: functionCallData.arguments
              })
            }];
            
            console.log('Submitting tool outputs:', toolOutputs);
            await openai.beta.threads.runs.submitToolOutputs(
              thread.id,
              run.id,
              { tool_outputs: toolOutputs }
            );
            console.log('Tool outputs submitted');
          }
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Retrieving updated run status...');
      runStatus = await checkRunStatus(thread.id, run.id);
    }
    
    console.log('Run completed. Getting messages...');
    const messages = await openai.beta.threads.messages.list(thread.id);
    const lastMessage = messages.data[0];
    console.log('Last message:', lastMessage);

    const response = {
      response: lastMessage.content[0].text.value,
      functionCall: functionCallData
    };
    console.log('Sending response:', response);
    
    res.json(response);

  } catch (error) {
    console.error('Chat API Error:', {
        message: error.message,
        type: error.type,
        status: error.status,
        code: error.code, 
        stack: error.stack
    });

    // 구체적인 에러 타입에 따른 처리
    if (error.code === 'rate_limit_exceeded') {
        res.status(429).json({ error: 'Rate limit exceeded. Please try again later.' });
    } else if (error.code === 'invalid_api_key') {
        res.status(401).json({ error: 'Invalid API key.' });
    } else if (error.code === 'insufficient_quota') {
        res.status(402).json({ error: 'OpenAI quota exceeded.' });
    } else if (error.code === 'context_length_exceeded') {
        res.status(400).json({ error: 'Prompt too long.' });
    } else {
        res.status(500).json({ 
            error: 'An error occurred with the chat service.',
            details: error.message 
        });
    }
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
