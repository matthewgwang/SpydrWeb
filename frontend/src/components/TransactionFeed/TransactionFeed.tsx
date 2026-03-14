import { useTransactionFeed } from "../../hooks/useTransactionFeed";
import TransactionCard from "./TransactionCard";

export default function TransactionFeed() {
  const { transactions } = useTransactionFeed();

  return (
    <div className="p-3 space-y-2">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
        Live Feed
      </h2>
      {transactions.length === 0 && (
        <p className="text-gray-600 text-xs">Waiting for transactions...</p>
      )}
      {transactions.map((tx) => (
        <TransactionCard key={tx.id} tx={tx} />
      ))}
    </div>
  );
}
