/**
 * WebSocket Client for Agent Chat Streaming
 * 
 * Handles real-time streaming responses from agents via WebSocket.
 */

export type MessageType = 'connected' | 'start' | 'stream' | 'end' | 'error';

export interface WebSocketMessage {
  type: MessageType;
  content?: string;
  agent_id?: string;
  agent_name?: string;
  error?: string;
}

export interface WebSocketConfig {
  agentId: string;
  token: string;
  onConnected?: (data: WebSocketMessage) => void;
  onStart?: () => void;
  onStream?: (content: string) => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

export class AgentChatWebSocket {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  
  constructor(config: WebSocketConfig) {
    this.config = config;
  }
  
  connect(): void {
    const wsUrl = this.getWebSocketUrl();
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.config.onError?.('WebSocket connection error');
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.config.onClose?.();
      this.attemptReconnect();
    };
  }
  
  private handleMessage(data: WebSocketMessage): void {
    switch (data.type) {
      case 'connected':
        this.config.onConnected?.(data);
        break;
      case 'start':
        this.config.onStart?.();
        break;
      case 'stream':
        if (data.content) {
          this.config.onStream?.(data.content);
        }
        break;
      case 'end':
        this.config.onEnd?.();
        break;
      case 'error':
        this.config.onError?.(data.error || 'Unknown error');
        break;
    }
  }
  
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
    return `${protocol}//${host}/ws/agent-chat/${this.config.agentId}?token=${this.config.token}`;
  }
  
  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      this.config.onError?.('Failed to reconnect after multiple attempts');
    }
  }
  
  sendMessage(content: string, conversationId?: string, projectId?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.config.onError?.('WebSocket is not connected');
      return;
    }
    
    const message = {
      type: 'message',
      content,
      conversation_id: conversationId,
      project_id: projectId,
    };
    
    this.ws.send(JSON.stringify(message));
  }
  
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
