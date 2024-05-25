import { StreamingTextResponse } from 'ai';
import { ChatMessage, MessageContent, OpenAI, ALL_AVAILABLE_OPENAI_MODELS } from 'llamaindex';
import { NextRequest, NextResponse } from 'next/server';
import { createChatEngine } from './engine';
import { LlamaIndexStream } from './llamaindex-stream';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const convertMessageContent = (
  textMessage: string,
  imageUrl: string | undefined
): MessageContent => {
  if (!imageUrl) return textMessage;
  return [
    {
      type: 'text',
      text: textMessage,
    },
    {
      type: 'image_url',
      image_url: {
        url: imageUrl,
      },
    },
  ];
};

// third-wheels model
const url = "https://third-wheels--third-wheels-modal-app-thirdwheels-web-inference.modal.run";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messages, data }: { messages: ChatMessage[]; data: any } = body;
    const userMessage = messages.pop();
    if (!messages || !userMessage || userMessage.role !== 'user') {
      return NextResponse.json(
        {
          error:
            'messages are required in the request body and the last message must be from the user',
        },
        { status: 400 }
      );
    }

    const llm = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
      model: "gpt-4",
    });

    const chatEngine = await createChatEngine(llm);

    // Convert message content from Vercel/AI format to LlamaIndex/OpenAI format
    const userMessageContent = convertMessageContent(
      userMessage.content,
      data?.imageUrl
    );

    console.log('[LlamaIndex]', 'Sending message:', userMessageContent);

    const date = new Date();
    const currentTime = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    const user_data = {
      "data": {
        "conversation": {
          "bot": "Heyhey, Jill! How is your day going so far? Anything fun or exciting?",
          "user": userMessageContent
        },
        "facial expressions": "neutral", // FIXME hardcoded for now
        "Time of the day": currentTime, // FIXME hardcoded for now
        "tone": "neutral"
      }
    };

    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(user_data)
    })
    .then(response => response.json())
    .catch((error) => {
      console.error('Error:', error);
    });

    // Calling LlamaIndex's ChatEngine to get a streamed response
    const response = await chatEngine.chat({
      message: userMessageContent,
      chatHistory: messages,
      stream: true,
    });

    // Transform LlamaIndex stream to Vercel/AI format
    const { stream, data: streamData } = LlamaIndexStream(response, {
      parserOptions: {
        image_url: data?.imageUrl,
      },
    });

    // Return a StreamingTextResponse, which can be consumed by the Vercel/AI client
    return new StreamingTextResponse(stream, {}, streamData);
  } catch (error) {
    console.error('[LlamaIndex]', error);
    return NextResponse.json(
      {
        error: (error as Error).message,
      },
      {
        status: 500,
      }
    );
  }
}
