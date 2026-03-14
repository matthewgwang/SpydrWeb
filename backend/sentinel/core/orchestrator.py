"""Pipeline orchestrator — the 12-step process for every transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.models.events import Event, EventType
from sentinel.models.layers import LayerSignal
from sentinel.models.report import Action, CaseReport

if TYPE_CHECKING:
    from sentinel.accounts.store import AccountStore
    from sentinel.accounts.profile_builder import ProfileBuilder
    from sentinel.accounts.vulnerability import VulnerabilityScorer
    from sentinel.accounts.recipient_scoring import RecipientScorer
    from sentinel.ai.cache import ResponseCache
    from sentinel.ai.provider import LLMProvider
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.alert_manager import AlertManager
    from sentinel.core.event_stream import EventStream
    from sentinel.core.fast_path import FastPathFilter
    from sentinel.core.scoring import ScoreComputer
    from sentinel.layers.base import DetectionLayer
    from sentinel.models.transaction import Transaction


class PipelineOrchestrator:
    """Run a Transaction through all detection layers and produce a CaseReport."""

    def __init__(
        self,
        event_stream: EventStream,
        account_store: AccountStore,
        profile_builder: ProfileBuilder,
        vulnerability_scorer: VulnerabilityScorer,
        recipient_scorer: RecipientScorer,
        brain_graph: BrainGraph,
        brain_overlay,
        layers: list[DetectionLayer],
        fast_path: FastPathFilter,
        score_computer: ScoreComputer,
        alert_manager: AlertManager,
        llm_provider: LLMProvider,
        cache: ResponseCache,
    ) -> None:
        self.event_stream = event_stream
        self.account_store = account_store
        self.profile_builder = profile_builder
        self.vulnerability_scorer = vulnerability_scorer
        self.recipient_scorer = recipient_scorer
        self.brain_graph = brain_graph
        self.brain_overlay = brain_overlay
        self.layers = layers
        self.fast_path = fast_path
        self.score_computer = score_computer
        self.alert_manager = alert_manager
        self.llm_provider = llm_provider
        self.cache = cache
        self.case_reports: list[CaseReport] = []

    async def process(self, transaction: Transaction) -> CaseReport:
        # Step 1: Log to event stream
        self.event_stream.append(
            Event(
                step=transaction.step,
                timestamp=transaction.timestamp,
                event_type=EventType.TRANSACTION,
                account_id=transaction.sender_id,
                payload=transaction.model_dump(),
            )
        )

        # Step 2: Update graph
        self.brain_graph.add_transaction_edge(
            sender_id=transaction.sender_id,
            receiver_id=transaction.receiver_id,
            transaction=transaction,
        )

        # Step 3: Pull / build profiles
        sender_profile = self.account_store.get_profile(transaction.sender_id)
        if not sender_profile:
            sender_profile = await self.profile_builder.build_profile(
                transaction.sender_id, self.event_stream, self.brain_graph
            )
            self.account_store.save_profile(sender_profile)

        receiver_profile = self.account_store.get_profile(transaction.receiver_id)
        if not receiver_profile:
            receiver_profile = await self.profile_builder.build_profile(
                transaction.receiver_id, self.event_stream, self.brain_graph
            )
            self.account_store.save_profile(receiver_profile)

        # Step 3b: Vulnerability + recipient risk
        vulnerability = self.vulnerability_scorer.compute(
            transaction.sender_id, sender_profile, self.event_stream, transaction.timestamp
        )
        sender_profile.vulnerability = vulnerability

        recipient_risk = self.recipient_scorer.compute_risk(
            transaction.receiver_id, self.event_stream, self.brain_graph
        )
        receiver_profile.recipient_risk = recipient_risk

        # Step 4: Layer 1 (rules) always runs first
        layer_1_signals = await self.layers[0].analyze(
            transaction, sender_profile, receiver_profile,
            self.event_stream, self.brain_graph,
        )

        # Step 4.5: Fast-path check
        basic_graph_check = self.brain_graph.quick_check(
            transaction.sender_id, transaction.receiver_id
        )

        rules_list = (
            [layer_1_signals]
            if isinstance(layer_1_signals, LayerSignal)
            else layer_1_signals
        )

        if self.fast_path.should_fast_path(
            rules_signals=rules_list,
            sender_profile=sender_profile,
            receiver_profile=receiver_profile,
            transaction=transaction,
            graph_signals=basic_graph_check,
        ):
            report = CaseReport(
                transaction_id=transaction.id,
                transaction=transaction,
                sender_profile=sender_profile,
                receiver_profile=receiver_profile,
                recommended_action=Action.ALLOW,
                confidence_score=0.0,
                fast_pathed=True,
            )
            self.case_reports.append(report)
            return report

        # Step 5: AI predicts exploitation risk -> test plan
        from sentinel.ai.prediction import predict_exploitation_risk

        test_plan = await predict_exploitation_risk(
            sender_profile=sender_profile,
            receiver_profile=receiver_profile,
            transaction=transaction,
            recent_events=self.event_stream.get_window(
                transaction.sender_id, window_minutes=168 * 60
            ),
            vulnerability_score=vulnerability,
            provider=self.llm_provider,
            cache=self.cache,
        )

        # Step 6: Run remaining layers in priority order
        all_signals: list[LayerSignal] = []
        if isinstance(layer_1_signals, list):
            all_signals.extend(layer_1_signals)
        else:
            all_signals.append(layer_1_signals)

        layer_map = {2: self.layers[1], 3: self.layers[2], 4: self.layers[3]}
        for layer_id in test_plan.layer_priority:
            if layer_id in layer_map:
                signal = await layer_map[layer_id].analyze(
                    transaction, sender_profile, receiver_profile,
                    self.event_stream, self.brain_graph,
                )
                if isinstance(signal, list):
                    all_signals.extend(signal)
                else:
                    all_signals.append(signal)

        # Step 7: Brain overlay
        overlay_result = self.brain_overlay.analyze(
            transaction=transaction,
            sender_id=transaction.sender_id,
            receiver_id=transaction.receiver_id,
            vulnerability_scores={sender_profile.account_id: vulnerability.score},
        )

        # Step 8: Layer 5 synthesis (if any signals triggered)
        triggered_signals = [s for s in all_signals if s.triggered]
        evidence_brief = None

        if triggered_signals or overlay_result.get("elevated", False):
            relationship_timeline = None
            if transaction.receiver_id not in sender_profile.known_payees:
                relationship_timeline = (
                    self.brain_overlay.relationship_analyzer.reconstruct_timeline(
                        transaction.sender_id,
                        transaction.receiver_id,
                        self.event_stream,
                    )
                )

            evidence_brief = await self.layers[4].synthesize(
                all_signals=all_signals,
                sender_profile=sender_profile,
                receiver_profile=receiver_profile,
                transaction=transaction,
                graph_context=overlay_result,
                relationship_timeline=relationship_timeline,
                vulnerability=vulnerability,
                test_plan=test_plan,
            )

        # Step 9: Compute confidence score
        velocity_deviation = overlay_result.get("velocity_deviation", 1.0)
        confidence_score = self.score_computer.compute(
            layer_signals=all_signals,
            layer_weights=test_plan.layer_weights,
            vulnerability_score=vulnerability.score,
            velocity_deviation=velocity_deviation,
        )

        # Step 10: Determine recommended action
        recommended_action = self.score_computer.get_recommended_action(confidence_score)

        # Step 11: Build case report
        report = CaseReport(
            transaction_id=transaction.id,
            transaction=transaction,
            sender_profile=sender_profile,
            receiver_profile=receiver_profile,
            evidence_brief=evidence_brief,
            brain_overlay=overlay_result,
            recommended_action=recommended_action,
            confidence_score=confidence_score,
            fast_pathed=False,
        )

        # Step 12: Alert bundling
        if confidence_score >= settings.SCORE_THRESHOLD_ALLOW:
            self.alert_manager.create_alert(report)

        self.case_reports.append(report)
        return report

    def get_recent_reports(self, limit: int = 50) -> list[CaseReport]:
        return self.case_reports[-limit:]

    def get_report(self, report_id: str) -> CaseReport | None:
        return next((r for r in self.case_reports if r.id == report_id), None)


from sentinel.config import settings  # noqa: E402 — used by process()
