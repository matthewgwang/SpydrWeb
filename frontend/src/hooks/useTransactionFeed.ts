import { useCallback, useEffect, useRef, useState } from "react";
import type { AlertFeedItem, TransactionFeedItem } from "../types";
import { FeedSocket } from "../services/websocket";

export function useTransactionFeed() {
  const [transactions, setTransactions] = useState<TransactionFeedItem[]>([]);
  const [alerts, setAlerts] = useState<AlertFeedItem[]>([]);
  const [alertFlash, setAlertFlash] = useState(false);
  const [recentAlertTxIds, setRecentAlertTxIds] = useState<Set<string>>(new Set());
  const socketRef = useRef<FeedSocket | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerFlash = useCallback((txId: string) => {
    setAlertFlash(true);
    setRecentAlertTxIds((prev) => new Set(prev).add(txId));

    if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    flashTimerRef.current = setTimeout(() => setAlertFlash(false), 600);

    setTimeout(() => {
      setRecentAlertTxIds((prev) => {
        const next = new Set(prev);
        next.delete(txId);
        return next;
      });
    }, 2000);
  }, []);

  useEffect(() => {
    const socket = new FeedSocket();
    socketRef.current = socket;

    socket.subscribe((msg) => {
      if (msg.type === "transaction") {
        setTransactions((prev) => [msg.data, ...prev].slice(0, 200));
      } else if (msg.type === "alert") {
        setAlerts((prev) => [msg.data, ...prev].slice(0, 50));
        const action = msg.data.recommended_action;
        if (action === "hold" || action === "refer") {
          triggerFlash(msg.data.transaction_id);
        }
      }
    });

    socket.connect();
    return () => {
      socket.disconnect();
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    };
  }, [triggerFlash]);

  return { transactions, alerts, alertFlash, recentAlertTxIds };
}
