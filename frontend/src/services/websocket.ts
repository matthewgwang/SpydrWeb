import type { AlertFeedItem, TransactionFeedItem } from "../types";

export type FeedMessage =
  | { type: "transaction"; data: TransactionFeedItem }
  | { type: "alert"; data: AlertFeedItem };

type MessageHandler = (msg: FeedMessage) => void;

export class FeedSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<MessageHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;
  private url: string;

  constructor(url = `ws://${window.location.host}/ws/feed`) {
    this.url = url;
  }

  connect() {
    if (this.disposed) return;
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as FeedMessage;
        this.handlers.forEach((h) => h(msg));
      } catch {
        /* ignore malformed frames */
      }
    };

    this.ws.onclose = () => {
      if (!this.disposed) {
        this.reconnectTimer = setTimeout(() => this.connect(), 2000);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect() {
    this.disposed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  subscribe(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}
