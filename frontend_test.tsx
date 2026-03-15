import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, ShieldAlert, Network, Activity, Terminal, 
  Cpu, Database, Server, Clock, Lock, ChevronRight, 
  Maximize2, Fingerprint, Play, Pause, FileText, ArrowLeft, X,
  Search, BrainCircuit, Save, Sliders, ToggleRight
} from 'lucide-react';

// --- MOCK DATA & GENERATORS ---

const DEMO_CASE = {
  id: "TXN-892-441-A",
  timestamp: new Date().toISOString(),
  latency: "142ms",
  customer: {
    id: "CUST_99182A", name: "Arthur Pendelton", age: 82,
    kyc_status: "VERIFIED_TIER_2", segment: "VULNERABLE_ELDERLY",
    device_hash: "sha256:8f4a...2b1c", ip_asn: "AS7018 (AT&T Services)",
  },
  transaction: {
    uuid: "req_9f8b2210a", amount: 15500.00, currency: "USD",
    destination_wallet: "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    exchange: "BINANCE_INTL", protocol: "WIRE_SWIFT",
  },
  status: "SYS_HOLD", riskScore: 94.2, confidence: "HIGH",
  model_version: "sentinel-core-v4.2.1",
  rules: [
    { id: "R_VEL_01", desc: "Daily Velocity Anomaly", exec_ms: 12.4, status: "FAIL", val: "+400%" },
    { id: "R_GEO_08", desc: "Geo-Velocity Impossibility", exec_ms: 4.1, status: "PASS", val: "Δ 0km/h" },
    { id: "R_AML_03", desc: "OFAC/SDN Blacklist", exec_ms: 18.9, status: "PASS", val: "CLEAN" },
    { id: "R_LIQ_02", desc: "Liquid Asset Drain", exec_ms: 7.2, status: "FAIL", val: "84.2%" },
  ],
  aiAnalysis: {
    model: "gpt-oss-120b-q4_K_M", prompt_tokens: 1402, completion_tokens: 210,
    output: "CLASSIFICATION: ELDER_EXPLOITATION_COACHING\nREASONING: Transaction baseline deviation (+400%). Support transcript indicates active adversarial coaching. Entity 'Scammer' explicitly instructing evasion of bank protocols ('dont tell the bank'). Destination topology mapped to Tier-2 mule cluster (Confidence: 0.89).",
    markers: ["dont tell the bank", "emergency flight"]
  },
  transcript: [
    { t: "12:42:01", src: "USER", msg: "I am trying to send the money but the app is warning me." },
    { t: "12:42:15", src: "ADV", msg: "Arthur, please hurry. The bank will try to stop you. Dont tell the bank it's for my flight, tell them it's for a home repair.", flag: true },
    { t: "12:43:02", src: "USER", msg: "Okay, I will tell them it's for the roof." }
  ]
};

const generateRandomCase = () => {
  const risk = Math.random() * 100;
  let status = "ALLOW";
  if (risk > 85) status = "SYS_HOLD";
  else if (risk > 60) status = "DELAY_REVIEW";

  return {
    id: `TXN-${Math.floor(100 + Math.random() * 900)}-${Math.floor(100 + Math.random() * 900)}-${['A','B','C','D'][Math.floor(Math.random()*4)]}`,
    timestamp: new Date().toISOString(),
    latency: `${Math.floor(40 + Math.random() * 120)}ms`,
    customer: {
      id: `CUST_${Math.floor(10000 + Math.random() * 90000)}`,
      name: ['John Doe', 'Sarah Smith', 'Michael Chen', 'Emma Davis', 'James Wilson'][Math.floor(Math.random()*5)],
      segment: "STANDARD", device_hash: "sha256:...", ip_asn: "AS_GENERIC"
    },
    transaction: { amount: Math.floor(Math.random() * 5000) + 10, currency: "USD", protocol: "ACH" },
    status,
    riskScore: risk.toFixed(1),
    confidence: risk > 80 ? "HIGH" : "MEDIUM",
    rules: [ { id: "R_VEL_01", desc: "Velocity", exec_ms: 5, status: risk > 70 ? "FAIL" : "PASS", val: "N/A" } ],
    aiAnalysis: { 
      model: "gpt-oss-small", 
      output: risk > 85 ? "CLASSIFICATION: SUSPICIOUS. Multiple rule triggers." : "CLASSIFICATION: NORMAL. No anomalies detected.",
      markers: []
    },
    transcript: []
  };
};

// --- SUB-COMPONENTS ---

const TopologyGraph = () => (
  <div className="relative w-full h-full min-h-[220px] bg-slate-50 border border-slate-200 rounded-md flex items-center justify-center overflow-hidden">
    <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)', backgroundSize: '20px 20px', opacity: 0.6 }}></div>
    <svg viewBox="0 0 500 250" className="w-full h-full z-10">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
        </marker>
        <marker id="arrow-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#dc2626" />
        </marker>
      </defs>
      <line x1="100" y1="125" x2="250" y2="125" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="4 4" markerEnd="url(#arrow)" />
      <line x1="250" y1="125" x2="400" y2="60" stroke="#fca5a5" strokeWidth="2" markerEnd="url(#arrow-red)" />
      <line x1="250" y1="125" x2="400" y2="125" stroke="#fca5a5" strokeWidth="2" markerEnd="url(#arrow-red)" />
      <line x1="250" y1="125" x2="400" y2="190" stroke="#fca5a5" strokeWidth="2" markerEnd="url(#arrow-red)" />

      <g transform="translate(100, 125)">
        <circle r="8" fill="#3b82f6" />
        <circle r="16" fill="none" stroke="#3b82f6" strokeWidth="2" opacity="0.2" className="animate-pulse" />
        <text y="-20" fill="#475569" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">SRC: CUST_99182A</text>
      </g>
      <g transform="translate(250, 125)">
        <rect x="-10" y="-10" width="20" height="20" fill="#f59e0b" rx="4" />
        <text y="-20" fill="#b45309" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">DST: bc1qx...x0wlh</text>
      </g>
      <g transform="translate(400, 60)"><circle r="6" fill="#dc2626" /><text x="12" y="3" fill="#991b1b" fontSize="9" fontFamily="monospace" fontWeight="bold">NODE_A1 (MULE)</text></g>
      <g transform="translate(400, 125)"><circle r="6" fill="#dc2626" /><text x="12" y="3" fill="#991b1b" fontSize="9" fontFamily="monospace" fontWeight="bold">NODE_A2 (MULE)</text></g>
      <g transform="translate(400, 190)"><circle r="6" fill="#dc2626" /><text x="12" y="3" fill="#991b1b" fontSize="9" fontFamily="monospace" fontWeight="bold">NODE_A3 (MULE)</text></g>
    </svg>
    <div className="absolute top-2 left-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Local Graph Matrix</div>
  </div>
);

const TimeSeriesChart = () => (
  <div className="relative w-full h-[140px] bg-white border border-slate-200 rounded-md p-3 flex flex-col justify-end">
    <div className="absolute top-2 left-3 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Velocity Disruption</div>
    <div className="absolute top-2 right-3 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-100 animate-pulse">σ = +4.2 (ANOMALY)</div>
    <svg viewBox="0 0 300 80" className="w-full h-full mt-4">
      <path d="M 0 60 L 50 55 L 100 58 L 150 50 L 200 55 L 250 10 L 300 10" fill="none" stroke="#2563eb" strokeWidth="2" />
      <path d="M 0 80 L 250 80 L 250 10 L 200 55 L 150 50 L 100 58 L 50 55 L 0 60 Z" fill="rgba(37, 99, 235, 0.05)" />
      <line x1="250" y1="0" x2="250" y2="80" stroke="#dc2626" strokeWidth="1.5" strokeDasharray="4 4" />
      <circle cx="250" cy="10" r="4" fill="#dc2626" />
      <line x1="0" y1="79" x2="300" y2="79" stroke="#cbd5e1" strokeWidth="1" />
    </svg>
    <div className="flex justify-between text-[9px] font-medium text-slate-400 mt-2">
      <span>T-12M</span><span>T-6M</span><span>T-3M</span><span className="text-red-600 font-bold">T-0 (NOW)</span>
    </div>
  </div>
);

const ReportModal = ({ caseData, onClose }) => {
  if (!caseData) return null;
  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl border border-slate-200 flex flex-col max-h-[90vh]">
        <div className="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 rounded-t-lg">
          <div className="flex items-center gap-2 text-slate-800 font-bold">
            <FileText size={18} className="text-blue-600" />
            SYSTEM GENERATED SAR REPORT (PREVIEW)
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-800 transition-colors"><X size={20}/></button>
        </div>
        <div className="p-6 overflow-y-auto font-mono text-xs text-slate-700 space-y-4">
          <div className="bg-slate-50 p-3 rounded border border-slate-200">
            <strong>DOCUMENT ID:</strong> SAR-GEN-{caseData.id}-{Date.now()}<br/>
            <strong>DATE GENERATED:</strong> {new Date().toUTCString()}<br/>
            <strong>FILING INSTITUTION:</strong> SENTINEL CORE SEC-OPS<br/>
            <strong>RISK SCORE:</strong> {caseData.riskScore} / 100 ({caseData.confidence} CONFIDENCE)
          </div>
          <div>
            <h3 className="font-bold text-slate-900 border-b border-slate-300 pb-1 mb-2">PART I: SUBJECT INFORMATION</h3>
            Name: {caseData.customer.name} (ID: {caseData.customer.id})<br/>
            Segment: {caseData.customer.segment}<br/>
            Device Hash: {caseData.customer.device_hash}
          </div>
          <div>
            <h3 className="font-bold text-slate-900 border-b border-slate-300 pb-1 mb-2">PART II: SUSPICIOUS ACTIVITY</h3>
            Amount: ${caseData.transaction.amount.toFixed(2)} {caseData.transaction.currency}<br/>
            Routing Protocol: {caseData.transaction.protocol}<br/>
            Destination: {caseData.transaction?.destination_wallet || 'N/A'}<br/>
            System Action Taken: <span className="text-red-600 font-bold">{caseData.status}</span>
          </div>
          <div>
            <h3 className="font-bold text-slate-900 border-b border-slate-300 pb-1 mb-2">PART III: NARRATIVE & AI SYNTHESIS</h3>
            <p className="whitespace-pre-wrap leading-relaxed">
              {caseData.aiAnalysis.output}
            </p>
          </div>
        </div>
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-3 rounded-b-lg">
          <button onClick={onClose} className="px-4 py-2 border border-slate-300 rounded text-slate-700 font-semibold text-xs hover:bg-slate-100">Close Preview</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded font-semibold text-xs hover:bg-blue-700 shadow-sm flex items-center gap-2">
             <FileText size={14} /> Submit to Compliance
          </button>
        </div>
      </div>
    </div>
  );
};

// --- VIEWS ---

const DashboardView = ({ queue, isStreaming, toggleStream, injectDemo, onInspect, onReport }) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 gap-4">
      <div className="grid grid-cols-4 gap-4 shrink-0">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center">
          <span className="text-[10px] uppercase font-bold text-slate-500 mb-1">Total Scanned (24h)</span>
          <span className="text-2xl font-bold text-slate-900">4,192,804</span>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center">
          <span className="text-[10px] uppercase font-bold text-slate-500 mb-1">Active Threats Blocked</span>
          <span className="text-2xl font-bold text-red-600">$12.4M</span>
        </div>
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-center">
          <span className="text-[10px] uppercase font-bold text-slate-500 mb-1">Avg Pipeline Latency</span>
          <span className="text-2xl font-bold text-emerald-600">142ms</span>
        </div>
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 shadow-sm flex flex-col justify-center gap-2">
          <span className="text-[10px] uppercase font-bold text-slate-400 mb-1">Demo God Mode</span>
          <div className="flex gap-2">
            <button onClick={toggleStream} className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-2 rounded text-xs font-semibold ${isStreaming ? 'bg-amber-500/20 text-amber-500 border border-amber-500/50 hover:bg-amber-500/30' : 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/50 hover:bg-emerald-500/30'}`}>
              {isStreaming ? <><Pause size={12}/> Pause</> : <><Play size={12}/> Resume</>}
            </button>
            <button onClick={injectDemo} className="flex-1 flex items-center justify-center gap-1 py-1.5 px-2 rounded text-xs font-semibold bg-blue-600 text-white hover:bg-blue-500 transition-colors">
              <ShieldAlert size={12} /> Inject Target
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 bg-white border border-slate-200 rounded-lg shadow-sm flex flex-col min-h-0 overflow-hidden">
        <div className="p-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
          <h2 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Activity size={16} className={isStreaming ? "text-emerald-500 animate-pulse" : "text-slate-400"} /> 
            Live Transaction Stream
          </h2>
          <span className="text-[10px] font-mono text-slate-500">POLLING: {isStreaming ? 'ACTIVE (4000ms)' : 'PAUSED'}</span>
        </div>
        
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-white sticky top-0 shadow-sm z-10">
              <tr>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">Timestamp</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">TXN ID</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">Entity</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">Amount</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">Risk Score</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200">Status</th>
                <th className="p-3 font-semibold text-slate-500 uppercase text-[10px] border-b border-slate-200 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[11px]">
              {queue.map((caseData) => (
                <tr key={caseData.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors group">
                  <td className="p-3 text-slate-500">{new Date(caseData.timestamp).toLocaleTimeString()}</td>
                  <td className="p-3 text-slate-800 font-medium">{caseData.id}</td>
                  <td className="p-3 text-slate-600 font-sans">{caseData.customer.name}</td>
                  <td className="p-3 text-slate-800">${caseData.transaction.amount.toFixed(2)}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded font-bold ${caseData.riskScore > 80 ? 'bg-red-100 text-red-700' : caseData.riskScore > 50 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {caseData.riskScore}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-[10px] font-bold ${caseData.status === 'SYS_HOLD' ? 'text-red-600' : caseData.status === 'ALLOW' ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {caseData.status}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-2">
                    <button onClick={() => onInspect(caseData)} className="px-3 py-1.5 bg-white border border-slate-300 rounded text-slate-700 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-colors shadow-sm font-sans font-medium text-xs">
                      Reasoning
                    </button>
                    <button onClick={() => onReport(caseData)} className="px-3 py-1.5 bg-white border border-slate-300 rounded text-slate-700 hover:bg-slate-100 transition-colors shadow-sm font-sans font-medium text-xs">
                      Report
                    </button>
                  </td>
                </tr>
              ))}
              {queue.length === 0 && (
                <tr><td colSpan="7" className="p-8 text-center text-slate-400 font-sans">Awaiting stream connection...</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const InvestigationView = ({ caseData, onBack }) => {
  const [consoleLogs, setConsoleLogs] = useState([
    `[SYS] LOADING INVESTIGATION KERNEL FOR ${caseData.id}...`,
    `[ROUTER] LATENCY MEASURED: ${caseData.latency}`,
  ]);

  const runAction = (cmd) => {
    setConsoleLogs(prev => [...prev, `[CMD] EXEC: ${cmd} ON ${caseData.id}... AWAITING ACK.`]);
    setTimeout(() => {
      setConsoleLogs(prev => [...prev, `[CMD] SUCCESS: ${cmd} APPLIED.`]);
    }, 600);
  };

  return (
    <div className="flex-1 flex flex-col p-4 gap-4 overflow-y-auto relative h-full">
      <div className="flex items-center gap-4 shrink-0">
        <button onClick={onBack} className="flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 rounded text-slate-600 hover:bg-slate-50 transition-colors shadow-sm text-xs font-semibold">
          <ArrowLeft size={14} /> Back to Queue
        </button>
        <div className="text-slate-400 text-xs font-medium">Deep Dive Investigation</div>
      </div>

      <div className={`border flex p-4 gap-6 shrink-0 rounded-lg shadow-sm items-center ${caseData.riskScore > 80 ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
        <div className={`flex-col flex items-center justify-center px-4 border-r ${caseData.riskScore > 80 ? 'border-red-200' : 'border-slate-300'}`}>
          <span className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${caseData.riskScore > 80 ? 'text-red-600' : 'text-slate-500'}`}>Threat Score</span>
          <span className={`text-4xl font-bold leading-none ${caseData.riskScore > 80 ? 'text-red-700' : 'text-slate-800'}`}>{caseData.riskScore}</span>
        </div>
        
        <div className="flex-1 grid grid-cols-4 gap-4 text-xs">
          <div><div className="text-slate-500 uppercase tracking-wider text-[10px] font-semibold mb-1">Event ID</div><div className="text-slate-900 font-mono font-medium">{caseData.id}</div></div>
          <div><div className="text-slate-500 uppercase tracking-wider text-[10px] font-semibold mb-1">Timestamp</div><div className="text-slate-900 font-mono font-medium">{new Date(caseData.timestamp).toLocaleTimeString()}</div></div>
          <div><div className="text-slate-500 uppercase tracking-wider text-[10px] font-semibold mb-1">System Action</div><div className={`font-bold px-2 py-0.5 rounded inline-block ${caseData.status === 'SYS_HOLD' ? 'bg-red-100 text-red-700' : 'bg-slate-200 text-slate-800'}`}>{caseData.status}</div></div>
          <div><div className="text-slate-500 uppercase tracking-wider text-[10px] font-semibold mb-1">Confidence</div><div className="text-slate-900 font-medium">{caseData.confidence}</div></div>
        </div>
        
        <div className="shrink-0 flex gap-3">
          <button onClick={() => runAction('ALLOW_TXN')} className="px-4 py-2 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded hover:bg-slate-50 transition-colors shadow-sm">Override & Allow</button>
          <button onClick={() => runAction('LOCK_ACCOUNT')} className="px-4 py-2 bg-red-600 border border-red-700 text-white text-xs font-semibold rounded hover:bg-red-700 transition-colors flex items-center gap-1.5 shadow-sm">
            <Lock size={14} /> Execute Lock
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4 flex-1 min-h-0">
        <div className="col-span-3 flex flex-col gap-4 min-h-0">
          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col">
            <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100 pb-2 mb-3 flex items-center justify-between">
              <span>Entity Profile</span><Fingerprint size={14} className="text-slate-400" />
            </div>
            <table className="w-full text-xs">
              <tbody>
                <tr className="border-b border-slate-50"><td className="py-1.5 text-slate-500 w-24">UUID</td><td className="text-slate-900 font-mono">{caseData.customer.id}</td></tr>
                <tr className="border-b border-slate-50"><td className="py-1.5 text-slate-500">Name</td><td className="text-slate-900 font-medium">{caseData.customer.name}</td></tr>
                <tr className="border-b border-slate-50"><td className="py-1.5 text-slate-500">Segment</td><td className="text-amber-600 font-medium">{caseData.customer.segment}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col">
            <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100 pb-2 mb-3 flex items-center justify-between">
              <span>TXN Payload</span><Database size={14} className="text-slate-400" />
            </div>
            <div className="text-xl font-medium text-slate-900 mb-3">${caseData.transaction.amount.toFixed(2)} <span className="text-sm text-slate-500">{caseData.transaction.currency}</span></div>
            <table className="w-full text-xs">
              <tbody>
                <tr className="border-b border-slate-50"><td className="py-1.5 text-slate-500 w-20">Protocol</td><td className="text-slate-900">{caseData.transaction.protocol}</td></tr>
                <tr><td className="py-1.5 text-slate-500 align-top">Dest</td><td className="text-blue-600 font-mono break-all">{caseData.transaction.destination_wallet || 'N/A'}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex-1 flex flex-col min-h-0">
             <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100 pb-2 mb-3 flex items-center justify-between shrink-0">
              <span>Rules Engine Output</span><Clock size={14} className="text-slate-400" />
            </div>
            <div className="overflow-y-auto pr-2 space-y-2">
              {caseData.rules.map(r => (
                <div key={r.id} className="bg-slate-50 border border-slate-200 rounded p-2 flex flex-col text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-slate-900 font-mono font-medium">{r.id}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${r.status === 'FAIL' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>{r.status}</span>
                  </div>
                  <div className="flex justify-between text-slate-600"><span className="truncate pr-2">{r.desc}</span><span className="font-mono">{r.val}</span></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-5 flex flex-col gap-4 min-h-0">
           {caseData.id === DEMO_CASE.id ? (
             <>
               <TopologyGraph />
               <TimeSeriesChart />
             </>
           ) : (
             <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-xs">
               Standard Baseline Transaction - No Topological Anomalies Visualized
             </div>
           )}
        </div>

        <div className="col-span-4 flex flex-col gap-4 min-h-0">
           <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex-1 flex flex-col">
             <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100 pb-2 mb-3 flex items-center justify-between shrink-0">
              <span>AI Synthesis <span className="text-slate-400 font-normal normal-case">({caseData.aiAnalysis.model})</span></span><Terminal size={14} className="text-slate-400" />
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded p-3 text-[11px] font-mono text-slate-700 overflow-y-auto space-y-3 flex-1">
              <div className="whitespace-pre-wrap leading-relaxed">{caseData.aiAnalysis.output}</div>
              {caseData.aiAnalysis.markers.length > 0 && (
                <>
                  <div className="text-slate-500 mt-2">&gt; EXTRACTED_MARKERS:</div>
                  <ul className="list-disc pl-5 text-amber-700 font-medium">
                    {caseData.aiAnalysis.markers.map((m, i) => <li key={i}>"{m}"</li>)}
                  </ul>
                </>
              )}
            </div>
           </div>

           {caseData.transcript.length > 0 && (
             <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex-1 flex flex-col min-h-[180px]">
               <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider border-b border-slate-100 pb-2 mb-3 flex items-center justify-between shrink-0">
                <span>Comms Intercept Log</span><Activity size={14} className="text-slate-400" />
              </div>
              <div className="overflow-y-auto space-y-2 text-xs">
                {caseData.transcript.map((msg, i) => (
                  <div key={i} className={`flex gap-3 p-2 rounded border-l-2 ${msg.flag ? 'bg-red-50 border-red-500' : 'bg-slate-50 border-slate-300'}`}>
                    <span className="text-slate-400 font-mono text-[10px] shrink-0 mt-0.5">[{msg.t}]</span>
                    <span className={`shrink-0 w-8 font-bold text-[10px] mt-0.5 ${msg.src === 'ADV' ? 'text-red-600' : 'text-blue-600'}`}>{msg.src}</span>
                    <span className={`leading-relaxed ${msg.flag ? 'text-red-900 font-medium' : 'text-slate-700'}`}>{msg.msg}</span>
                  </div>
                ))}
              </div>
             </div>
           )}
        </div>
      </div>

      <div className="h-28 bg-slate-900 rounded-lg p-3 font-mono text-[11px] flex flex-col shrink-0 shadow-inner">
        <div className="text-slate-400 border-b border-slate-800 pb-2 mb-2 flex justify-between items-center uppercase text-[10px] tracking-widest font-bold">
          <span>System Output Log</span><Maximize2 size={12} className="cursor-pointer hover:text-white" />
        </div>
        <div className="overflow-y-auto flex-1 flex flex-col justify-end space-y-1">
          {consoleLogs.map((log, i) => (
            <div key={i} className="text-slate-300"><span className="text-slate-500">[{new Date().toISOString()}]</span> {log}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

// --- NEW: GLOBAL GRAPH VIEW ---
const GlobalGraphView = () => (
  <div className="flex-1 flex flex-col h-full p-4 gap-4 overflow-hidden bg-slate-100">
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center justify-between shrink-0">
      <div>
        <h2 className="font-bold text-slate-800 flex items-center gap-2"><Network size={18} className="text-blue-600"/> Global Entity Graph (NetworkX)</h2>
        <p className="text-xs text-slate-500 mt-1">Macro-level topology visualization for clustering and mule ring detection.</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold rounded-full">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          LIVE SYNC: ACTIVE
        </div>
        <div className="relative w-72">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input type="text" placeholder="Search Entity or Wallet..." className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded text-sm focus:outline-none focus:border-blue-500" defaultValue="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh" />
        </div>
      </div>
    </div>

    <div className="flex-1 flex gap-4 min-h-0">
      <div className="flex-1 bg-white border border-slate-200 rounded-lg relative overflow-hidden flex items-center justify-center shadow-sm">
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)', backgroundSize: '30px 30px', opacity: 0.4 }}></div>
        <svg viewBox="0 0 800 600" className="w-full h-full z-10 drop-shadow-md">
          {/* Mock Global Topology Lines */}
          <g stroke="#cbd5e1" strokeWidth="1" opacity="0.6">
            <line x1="400" y1="300" x2="200" y2="150" />
            <line x1="400" y1="300" x2="150" y2="350" />
            <line x1="400" y1="300" x2="250" y2="500" />
            <line x1="400" y1="300" x2="600" y2="150" />
            <line x1="400" y1="300" x2="650" y2="400" stroke="#fca5a5" strokeWidth="2" />
            <line x1="400" y1="300" x2="500" y2="500" stroke="#fca5a5" strokeWidth="2" />
            
            {/* Cluster A */}
            <line x1="200" y1="150" x2="180" y2="100" />
            <line x1="200" y1="150" x2="250" y2="100" />
            <line x1="200" y1="150" x2="120" y2="180" />
            
            {/* Target Cluster (Red) */}
            <line x1="650" y1="400" x2="700" y2="350" stroke="#fca5a5" strokeWidth="1.5"/>
            <line x1="650" y1="400" x2="720" y2="420" stroke="#fca5a5" strokeWidth="1.5"/>
            <line x1="650" y1="400" x2="680" y2="480" stroke="#fca5a5" strokeWidth="1.5"/>
            <line x1="500" y1="500" x2="680" y2="480" stroke="#fca5a5" strokeWidth="1.5"/>

            {/* REAL-TIME INCOMING EDGE ANIMATION */}
            <line x1="400" y1="300" x2="450" y2="100" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="4 4" className="animate-pulse" />
          </g>
          
          {/* Mock Nodes */}
          <circle cx="400" cy="300" r="14" fill="#f59e0b" stroke="#fff" strokeWidth="2" />
          <text x="400" y="325" fill="#b45309" fontSize="12" fontFamily="monospace" textAnchor="middle" fontWeight="bold">TARGET_EXCHANGE</text>
          
          <circle cx="200" cy="150" r="8" fill="#3b82f6" /><circle cx="150" cy="350" r="8" fill="#3b82f6" /><circle cx="250" cy="500" r="8" fill="#3b82f6" /><circle cx="600" cy="150" r="8" fill="#3b82f6" />
          <circle cx="180" cy="100" r="6" fill="#94a3b8" /><circle cx="250" cy="100" r="6" fill="#94a3b8" /><circle cx="120" cy="180" r="6" fill="#94a3b8" />
          
          {/* High Risk Cluster */}
          <circle cx="650" cy="400" r="10" fill="#dc2626" />
          <text x="650" y="380" fill="#dc2626" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">KNOWN_MULE_HUB</text>
          <circle cx="500" cy="500" r="8" fill="#ef4444" />
          <circle cx="700" cy="350" r="6" fill="#f87171" /><circle cx="720" cy="420" r="6" fill="#f87171" /><circle cx="680" cy="480" r="6" fill="#f87171" />

          {/* REAL-TIME INCOMING NODE */}
          <g className="animate-pulse">
            <circle cx="450" cy="100" r="8" fill="#3b82f6" stroke="#bfdbfe" strokeWidth="4" />
            <text x="450" y="85" fill="#2563eb" fontSize="10" fontFamily="monospace" textAnchor="middle" fontWeight="bold">INCOMING_TXN...</text>
          </g>
        </svg>
      </div>

      <div className="w-80 bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col shrink-0">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 mb-4 text-sm uppercase tracking-wider">Cluster Analysis</h3>
        <div className="space-y-4">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Selected Node</div>
            <div className="font-mono text-xs text-slate-900 bg-slate-50 p-2 border border-slate-200 rounded break-all">
              bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
             <div className="bg-red-50 p-2 rounded border border-red-100">
               <div className="text-[10px] text-red-600 font-bold uppercase">Risk Index</div>
               <div className="text-lg font-bold text-red-700">0.89</div>
             </div>
             <div className="bg-slate-50 p-2 rounded border border-slate-200">
               <div className="text-[10px] text-slate-500 font-bold uppercase">Degree</div>
               <div className="text-lg font-bold text-slate-700">
                 14 Links <span className="text-[10px] text-emerald-500 ml-1 animate-pulse">+1</span>
               </div>
             </div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Connected Entities (1st Degree)</div>
            <div className="space-y-2 font-mono text-[10px]">
              <div className="flex justify-between items-center p-1.5 bg-red-50 border border-red-100 text-red-700 rounded"><span>MULE_ACC_881</span><span>$14,200</span></div>
              <div className="flex justify-between items-center p-1.5 bg-red-50 border border-red-100 text-red-700 rounded"><span>MULE_ACC_912</span><span>$8,400</span></div>
              <div className="flex justify-between items-center p-1.5 bg-slate-50 border border-slate-200 text-slate-600 rounded"><span>CUST_99182A</span><span>$15,500</span></div>
              <div className="flex justify-between items-center p-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded animate-pulse"><span>NEW_INBOUND</span><span>$2,100</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// --- NEW: VLM / RULES CONFIG VIEW ---
const VlmConfigView = () => (
  <div className="flex-1 flex flex-col h-full p-4 gap-4 overflow-y-auto bg-slate-100">
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center justify-between shrink-0">
      <div>
        <h2 className="font-bold text-slate-800 flex items-center gap-2"><BrainCircuit size={18} className="text-purple-600"/> VLM & Rules Configuration Hub</h2>
        <p className="text-xs text-slate-500 mt-1">Manage underlying LLM prompts, model selection, and deterministic routing thresholds.</p>
      </div>
      <button className="px-4 py-2 bg-slate-200 text-slate-500 text-xs font-semibold rounded border border-slate-300 shadow-sm flex items-center gap-2 cursor-not-allowed">
        <Lock size={14} /> Unlock (Admin)
      </button>
    </div>

    {/* RUNTIME LOCK BANNER */}
    <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-lg flex items-center gap-3 shadow-sm shrink-0">
      <Lock size={18} className="text-amber-600" />
      <div>
        <strong className="text-sm">RUNTIME LOCK ACTIVE: System is currently processing live pipeline data.</strong>
        <p className="text-xs text-amber-700 mt-0.5">Parameters cannot be mutated without pausing the ingest stream. Authenticate as an Administrator to override.</p>
      </div>
    </div>

    <div className="grid grid-cols-2 gap-4 flex-1">
      {/* VLM Configuration */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col gap-5 opacity-80">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center justify-between text-sm uppercase tracking-wider">
          <span className="flex items-center gap-2"><Terminal size={14} className="text-slate-400" /> Language Model Settings</span>
          <Lock size={12} className="text-slate-400"/>
        </h3>
        
        <div>
          <label className="text-[10px] uppercase font-bold text-slate-500 mb-1 block">Active Model Pipeline</label>
          <select disabled className="w-full p-2 bg-slate-100 border border-slate-200 rounded text-sm text-slate-500 font-mono cursor-not-allowed">
            <option>gpt-oss-120b-q4_K_M (Primary)</option>
          </select>
        </div>

        <div className="flex-1 flex flex-col">
          <label className="text-[10px] uppercase font-bold text-slate-500 mb-1 block">System Context Prompt (Comms Intercept)</label>
          <textarea 
            disabled
            className="w-full flex-1 p-3 bg-slate-900 text-slate-400 font-mono text-xs rounded border border-slate-800 cursor-not-allowed leading-relaxed resize-none"
            defaultValue={`You are SENTINEL, a fraud-detection AI.
Analyze the following customer support transcript.
Identify markers of:
1. Elder coercion
2. Adversarial coaching ("don't tell the bank")
3. Account Takeover (ATO)

Output structured JSON strictly containing CLASSIFICATION, REASONING, and exact string MARKERS.`}
          />
        </div>
      </div>

      {/* Rules & Routing */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col gap-6 opacity-80">
        <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 flex items-center justify-between text-sm uppercase tracking-wider">
          <span className="flex items-center gap-2"><Sliders size={14} className="text-slate-400" /> Deterministic Rules & Routing</span>
          <Lock size={12} className="text-slate-400"/>
        </h3>

        <div>
           <div className="flex justify-between mb-1">
             <label className="text-[10px] uppercase font-bold text-slate-500 block">Global Action Thresholds (Risk Score 0-100)</label>
           </div>
           <div className="space-y-3 mt-3">
             <div className="flex items-center gap-4">
               <div className="w-24 text-xs font-bold text-slate-500 bg-slate-100 p-1.5 text-center rounded border border-slate-200">SYS_HOLD</div>
               <input type="range" min="0" max="100" defaultValue="85" disabled className="flex-1 accent-slate-400 cursor-not-allowed opacity-50" />
               <span className="text-xs font-mono font-bold text-slate-500 w-8">&gt; 85</span>
             </div>
             <div className="flex items-center gap-4">
               <div className="w-24 text-xs font-bold text-slate-500 bg-slate-100 p-1.5 text-center rounded border border-slate-200">DELAY_REV</div>
               <input type="range" min="0" max="100" defaultValue="60" disabled className="flex-1 accent-slate-400 cursor-not-allowed opacity-50" />
               <span className="text-xs font-mono font-bold text-slate-500 w-8">&gt; 60</span>
             </div>
           </div>
        </div>

        <div className="mt-4">
          <label className="text-[10px] uppercase font-bold text-slate-500 mb-3 block border-b border-slate-100 pb-2">Active Rules Engines</label>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded">
              <div>
                <div className="text-xs font-bold text-slate-600">R_VEL_01: Daily Velocity Anomaly</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Triggers on baseline deviation &gt; 200%</div>
              </div>
              <ToggleRight size={24} className="text-slate-400 cursor-not-allowed" />
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded">
              <div>
                <div className="text-xs font-bold text-slate-600">R_AML_03: OFAC/SDN Blacklist Lookup</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Checks entity details against Gov DBs</div>
              </div>
              <ToggleRight size={24} className="text-slate-400 cursor-not-allowed" />
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded opacity-50">
              <div>
                <div className="text-xs font-bold text-slate-500">R_GEO_08: Impossibility (Disabled)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Currently retraining model weights</div>
              </div>
              <ToggleRight size={24} className="text-slate-300 transform rotate-180 cursor-not-allowed" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// --- MAIN APPLICATION SHELL ---

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'investigation' | 'global_graph' | 'vlm_config'
  const [activeCase, setActiveCase] = useState(null);
  const [reportCase, setReportCase] = useState(null);
  
  const [queue, setQueue] = useState([]);
  const [isStreaming, setIsStreaming] = useState(true);

  // Initial dummy data load
  useEffect(() => {
    setQueue([generateRandomCase(), generateRandomCase(), generateRandomCase()]);
  }, []);

  // Data Streaming Engine
  useEffect(() => {
    let interval;
    if (isStreaming) {
      interval = setInterval(() => {
        setQueue(prev => [generateRandomCase(), ...prev].slice(0, 50)); 
      }, 4000); 
    }
    return () => clearInterval(interval);
  }, [isStreaming]);

  // Handlers
  const handleInjectDemo = () => {
    setQueue(prev => [{...DEMO_CASE, timestamp: new Date().toISOString()}, ...prev].slice(0, 50));
    setIsStreaming(false); 
  };

  const handleInspect = (caseData) => {
    setActiveCase(caseData);
    setCurrentView('investigation');
  };

  return (
    <div className="h-screen w-full bg-slate-100 text-slate-800 font-sans flex flex-col overflow-hidden selection:bg-blue-100 text-[13px]">
      
      {/* GLOBAL HEADER */}
      <header className="h-10 bg-white border-b border-slate-200 flex items-center justify-between px-4 shrink-0 shadow-sm z-10">
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-2 text-slate-900 font-bold tracking-tight">
            <ShieldAlert size={16} className="text-blue-600" /> 
            SENTINEL <span className="text-slate-400 font-normal">| Core</span>
          </div>
          <div className="h-4 w-px bg-slate-300"></div>
          <span className="text-slate-500 text-xs font-medium">ENV: PROD-US-EAST</span>
          <div className="h-4 w-px bg-slate-300"></div>
          <span className="text-emerald-600 text-xs font-medium flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div> SYS_UPTIME: 99.99%
          </span>
        </div>
        <div className="flex items-center gap-5 text-slate-500 text-xs font-medium">
          <span className="flex items-center gap-1.5"><Cpu size={14} /> CPU: 42%</span>
          <span className="flex items-center gap-1.5"><Database size={14} /> DB: 1.2ms</span>
          <span className="flex items-center gap-1.5"><Server size={14} /> KAFKA: 0 lag</span>
        </div>
      </header>

      {/* APP WORKSPACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* NARROW SIDEBAR */}
        <aside className="w-14 bg-white border-r border-slate-200 flex flex-col items-center py-3 gap-4 shrink-0 shadow-sm z-0">
          {/* Dashboard Icon */}
          <button 
            onClick={() => setCurrentView('dashboard')} 
            className={`p-2.5 rounded-md transition-colors ${currentView === 'dashboard' || currentView === 'investigation' ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-50'}`} 
            title="Live Queue"
          >
            <Activity size={18} />
          </button>
          
          {/* Global Graph Icon */}
          <button 
            onClick={() => setCurrentView('global_graph')} 
            className={`p-2.5 rounded-md transition-colors ${currentView === 'global_graph' ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-50'}`} 
            title="Global Entity Graph"
          >
            <Network size={18} />
          </button>
          
          {/* VLM Config Icon */}
          <button 
            onClick={() => setCurrentView('vlm_config')} 
            className={`p-2.5 rounded-md transition-colors ${currentView === 'vlm_config' ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-50'}`} 
            title="VLM & Rules Config"
          >
            <BrainCircuit size={18} />
          </button>

          {/* Spacer */}
          <div className="flex-1"></div>

          {/* Settings Icon */}
          <button className="p-2.5 text-slate-400 hover:text-slate-700 hover:bg-slate-50 rounded-md transition-colors" title="System Settings">
            <Lock size={18} />
          </button>
        </aside>

        {/* MAIN CONTENT AREA ROUTING */}
        {currentView === 'dashboard' && (
          <DashboardView 
            queue={queue} 
            isStreaming={isStreaming} 
            toggleStream={() => setIsStreaming(!isStreaming)} 
            injectDemo={handleInjectDemo}
            onInspect={handleInspect}
            onReport={setReportCase}
          />
        )}
        
        {currentView === 'investigation' && (
          <InvestigationView 
            caseData={activeCase} 
            onBack={() => setCurrentView('dashboard')} 
          />
        )}

        {currentView === 'global_graph' && (
          <GlobalGraphView />
        )}

        {currentView === 'vlm_config' && (
          <VlmConfigView />
        )}

      </div>

      {/* REPORT OVERLAY */}
      <ReportModal caseData={reportCase} onClose={() => setReportCase(null)} />
    </div>
  );
}