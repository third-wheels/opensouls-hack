import {
  ContextChatEngine,
  LLM,
  serviceContextFromDefaults,
  SimpleDocumentStore,
  storageContextFromDefaults,
  OpenAIEmbedding,
  VectorStoreIndex,
} from 'llamaindex';
import { CHUNK_OVERLAP, CHUNK_SIZE, STORAGE_CACHE_DIR } from './constants.mjs';

const systemPrompt = `
  You are a relationship mediator helping a remote couple strengthen their relationship. Your main goal is to listen to the user, comfort them, and provide supportive advice without giving too many suggestions. Your responses should be concise, limited to two sentences each, and focused on fostering a positive and understanding environment. Do not ask too many questions as this can exhaust users. Your tone is wam and fuzzy with a sense of humor and sassiness. Use an informal tone with a bit of Gen Z slang to make the conversation more relatable. Always start the conversation and talk like you are the user's friend.
  Start the conversation by asking users like:
  Hi there! How was your day?
  Hey, how are you feeling today?
  Hi there, how is your day going so far?
  Heyhey, anything fun lately?

  Backgroudn info: user's name is Jill, her boyfriend's name is Alex
`;

async function getDataSource(llm: LLM) {
  const serviceContext = serviceContextFromDefaults({
    llm,
    chunkSize: CHUNK_SIZE,
    chunkOverlap: CHUNK_OVERLAP,
    embedModel: new OpenAIEmbedding(),
  });
  let storageContext = await storageContextFromDefaults({
    persistDir: `${STORAGE_CACHE_DIR}`,
  });

  const numberOfDocs = Object.keys(
    (storageContext.docStore as SimpleDocumentStore).toDict()
  ).length;
  if (numberOfDocs === 0) {
    throw new Error(
      `StorageContext is empty - call 'npm run generate' to generate the storage first`
    );
  }
  return await VectorStoreIndex.init({
    storageContext,
    serviceContext,
  });
}

export async function createChatEngine(llm: LLM) {
  const index = await getDataSource(llm);
  const retriever = index.asRetriever();
  retriever.similarityTopK = 5;

  return new ContextChatEngine({
    chatModel: llm,
    retriever,
    systemPrompt: systemPrompt,
  });
}
