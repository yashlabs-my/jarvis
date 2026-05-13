"""
OpenRouter LLM Integration Module
Async LLM client for OpenRouter API with streaming support.
"""

import asyncio
import json
from typing import AsyncGenerator, List, Dict, Optional
from datetime import datetime
import httpx

from config.settings import Config


class Message:
    """Represents a chat message."""
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class OpenRouterLLM:
    """
    Async OpenRouter LLM client with streaming support.
    Handles conversation history and API communication.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = model or Config.OPENROUTER_MODEL
        self.base_url = Config.OPENROUTER_BASE_URL
        self.conversation_history: List[Message] = []
        self.system_prompt = Config.get_system_prompt()
        
        # Initialize with system prompt
        self._add_system_message()
    
    def _add_system_message(self) -> None:
        """Add system prompt to conversation history."""
        self.conversation_history.append(Message("system", self.system_prompt))
    
    def clear_history(self) -> None:
        """Clear conversation history except system prompt."""
        self.conversation_history = [self.conversation_history[0]]
    
    def add_user_message(self, content: str) -> None:
        """Add user message to history."""
        self.conversation_history.append(Message("user", content))
    
    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to history."""
        self.conversation_history.append(Message("assistant", content))
    
    async def chat(self, message: str, stream: bool = True) -> AsyncGenerator[str, None]:
        """
        Send message to LLM and yield response chunks.
        
        Args:
            message: User input message
            stream: Whether to stream the response
            
        Yields:
            Response text chunks
        """
        self.add_user_message(message)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jarvis-assistant",
            "X-Title": "Jarvis AI Assistant"
        }
        
        payload = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in self.conversation_history],
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            async with httpx.AsyncClient(timeout=Config.RESPONSE_TIMEOUT) as client:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    ) as response:
                        response.raise_for_status()
                        
                        full_response = ""
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data.strip() == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                        
                        if full_response:
                            self.add_assistant_message(full_response)
                else:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    content = result["choices"][0]["message"]["content"]
                    self.add_assistant_message(content)
                    yield content
                    
        except httpx.HTTPError as e:
            error_msg = f"API Error: {str(e)}"
            print(f"[LLM ERROR] {error_msg}")
            yield error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[LLM ERROR] {error_msg}")
            yield error_msg
    
    async def generate_response(self, message: str) -> str:
        """Generate complete response without streaming."""
        full_response = ""
        async for chunk in self.chat(message, stream=False):
            full_response += chunk
        return full_response
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history as list of dicts."""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def trim_history(self, max_messages: int = Config.MAX_CONVERSATION_HISTORY) -> None:
        """Trim history to max messages while keeping system prompt."""
        if len(self.conversation_history) > max_messages + 1:
            # Keep system prompt and last N messages
            self.conversation_history = [self.conversation_history[0]] + \
                                       self.conversation_history[-max_messages:]
