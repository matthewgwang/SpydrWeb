import { useEffect, useRef, useState } from "react";
import type { AlertFeedItem, TransactionFeedItem } from "../types";
import { FeedSocket } from "../services/websocket";

export function useTransactionFeed() {
  const [transactions, setTransactions] = useState<TransactionFeedItem[]>([]);
  const [alerts, setAlerts] = useState<AlertFeedItem[]>([]);
  const socketRef = useRef<FeedSocket | null>(null);

  useEffect(() => {
    const socket = new FeedSocket();
    socketRef.current = socket;

    socket.subscribe((msg) => {
      if (msg.type === "transaction") {
        setTransactions((prev) => [msg.data, ...prev].slice(0, 200));
      } else if (msg.type === "alert") {
        setAlerts((prev) => [msg.data, ...prev].slice(0, 50));
      }
    });

    socket.connect();
    return () => socket.disconnect();
  }, []);

  return { transactions, alerts };
}
