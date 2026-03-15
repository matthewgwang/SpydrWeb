// Mirrors backend sentinel.models — keep in sync with Pydantic definitions

export type EventType =
  | "transaction"
  | "login"
  | "password_reset"
  | "email_change"
  | "payee_added"
  | "device_change"
  | "support_chat"
  | "balance_check"
  | "branch_visit"
  | "phone_call"
  | "limit_inquiry"
  | "settings_change";

export interface Event {
  id: string;
  timestamp: string;
  step: number;
  event_type: EventType;
  account_id: string;
  payload: Record<string, unknown>;
}

export type TransactionType =
  | "CASH_IN"
  | "CASH_OUT"
  | "DEBIT"
  | "PAYMENT"
  | "TRANSFER";

export interface Transaction {
  id: string;
  step: number;
  timestamp: string;
  type: TransactionType;
  amount: number;
  sender_id: string;
  receiver_id: string;
  old_balance_sender: number;
  new_balance_sender: number;
  old_balance_receiver: number;
  new_balance_receiver: number;
  is_fraud: boolean;
  channel: string;
  description: string;
}

export interface BaselineStats {
  avg_amount: number;
  std_amount: number;
  avg_daily_frequency: number;
  avg_weekly_frequency: number;
  typical_hours: number[];
  typical_merchants: Record<string, number>;
  typical_channels: Record<string, number>;
  typical_transaction_types: Record<string, number>;
  login_frequency_daily: number;
  balance_check_frequency_daily: number;
  last_activity: string | null;
  decay_factor: number;
  days_of_history: number;
}

export interface CommunicationFingerprint {
  typical_vocabulary_level: string;
  typical_tone: string;
  typical_topics: string[];
  avg_interaction_frequency_monthly: number;
  avg_message_length_words: number;
  uses_technical_banking_terms: boolean;
  typical_channels: string[];
  baseline_sentiment: string;
  sample_phrases: string[];
}

export interface VulnerabilityFactor {
  factor: string;
  description: string;
  weight: number;
}

export interface VulnerabilityScore {
  score: number;
  factors: VulnerabilityFactor[];
  transaction_diversity_trend: number;
  social_spending_trend: number;
  digital_literacy_level: string;
  routine_rigidity: number;
  recent_life_disruption: boolean;
}

export interface RecipientRiskScore {
  first_time_sender_count_7d: number;
  avg_relationship_duration_days: number;
  receive_to_send_ratio: number;
  inbound_velocity_24h: number;
  is_receive_only: boolean;
  connected_to_other_vulnerable_customers: boolean;
  total_inbound_amount_7d: number;
}

export interface AccountProfile {
  account_id: string;
  name: string;
  age: number | null;
  location: string | null;
  account_created: string;
  account_type: string;
  summary_text: string;
  communication_fingerprint: CommunicationFingerprint | null;
  baseline: BaselineStats | null;
  vulnerability: VulnerabilityScore | null;
  recipient_risk: RecipientRiskScore | null;
  devices: string[];
  known_payees: string[];
  profile_confidence: number;
}

export type FraudType =
  | "ELDER_EXPLOITATION"
  | "ACCOUNT_TAKEOVER"
  | "MULE_NETWORK"
  | "CARD_TESTING"
  | "UNKNOWN";

export type ExploitationTactic =
  | "family_coercion"
  | "romance_scam"
  | "authority_impersonation"
  | "phone_coaching"
  | "unknown";

export interface LayerSignal {
  layer_id: number;
  layer_name: string;
  triggered: boolean;
  confidence: number;
  explanation: string;
  evidence: Record<string, unknown>;
  severity: string;
}

export interface InterventionRecommendation {
  action: string;
  reason: string;
  urgency: string;
  sensitivity_notes: string;
}

export interface TimelineEntry {
  timestamp: string;
  step: number;
  event_type: string;
  description: string;
  layer_source: string;
  significance: string;
}

export interface EvidenceBrief {
  narrative: string;
  timeline: TimelineEntry[];
  signals: LayerSignal[];
  exploitation_tactic: ExploitationTactic;
  manipulation_indicators: string[];
  interventions: InterventionRecommendation[];
  confidence_score: number;
  what_traditional_systems_missed: string;
}

export type Action = "allow" | "delay" | "hold" | "refer";

export interface CaseReport {
  id: string;
  transaction_id: string;
  transaction: Transaction | null;
  sender_profile: AccountProfile | null;
  receiver_profile: AccountProfile | null;
  layer_signals: LayerSignal[];
  evidence_brief: EvidenceBrief | null;
  brain_overlay: Record<string, unknown> | null;
  recommended_action: Action;
  confidence_score: number;
  fast_pathed: boolean;
  timestamp: string;
  analyst_feedback: Record<string, unknown> | null;
}

export interface AlertBundle {
  bundle_id: string;
  related_account_ids: string[];
  case_reports: CaseReport[];
  primary_fraud_type: FraudType;
  created_at: string;
  status: string;
}

export interface VelocityReport {
  entity_id: string;
  current_velocity: number;
  baseline_velocity: number;
  deviation_ratio: number;
  time_window_hours: number;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  risk?: number;
  vulnerable?: boolean;
  flagged?: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  amount?: number;
  flagged?: boolean;
  new?: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// WebSocket feed item shapes
export interface TransactionFeedItem {
  id: string;
  step: number;
  timestamp: string;
  type: TransactionType;
  tx_type?: string;
  amount: number;
  sender_id: string;
  sender_name: string;
  receiver_id: string;
  receiver_name: string;
  status: string;
  confidence_score: number;
  report_id?: string;
}

export interface AlertFeedItem {
  id: string;
  transaction_id: string;
  timestamp: string;
  sender_name: string;
  receiver_name: string;
  amount: number;
  confidence_score: number;
  exploitation_tactic: ExploitationTactic;
  recommended_action: Action;
  summary: string;
}
