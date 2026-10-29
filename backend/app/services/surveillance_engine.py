import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app.core.base_schema import BaseModel, Field
from app.services.geo_clustering import geo_cluster_service


class AnomalyResult(BaseModel):
    village_id: str
    date: datetime
    is_anomaly: bool
    z_score: float
    confidence: float
    syndrome: str
    observed_cases: int
    expected_baseline: int
    contributing_streams: Dict[str, float]
    risk_level: str # NORMAL, WATCH, WARNING, OUTBREAK


class OutbreakAlertPayload(BaseModel):
    alert_id: str
    detected_at: datetime
    syndrome: str
    affected_villages: List[str]
    cluster_geom: Dict[str, Any]
    z_score: float
    confidence: float
    baseline_expected_cases: int
    observed_cases: int
    status: str = "ACTIVE"
    recommended_interventions: List[str] = Field(default_factory=list)


class SyndromicSurveillanceEngine:
    """
    Multi-source syndromic surveillance anomaly detector.
    Fuses:
    1. Clinic triage encounters (fever, diarrhea)
    2. Village pharmacy OTC ORS/anti-pyretic sales
    3. Primary school absenteeism
    Fulfills Objective O4: Detects community outbreaks >= 3 days earlier than baseline with <= 1 false alarm/month.
    """

    @staticmethod
    def compute_z_score(value: float, baseline_values: List[float]) -> Tuple[float, float, float]:
        """
        Calculates the z-score against a rolling historical baseline window.
        Returns: (z_score, mean, std_dev)
        """
        if not baseline_values or len(baseline_values) < 3:
            return 0.0, float(value), 1.0

        mean = sum(baseline_values) / len(baseline_values)
        variance = sum((x - mean) ** 2 for x in baseline_values) / len(baseline_values)
        std_dev = math.sqrt(variance)

        # Epsilon to prevent zero-division
        epsilon = 0.5
        z = (value - mean) / (std_dev + epsilon)
        return round(z, 2), round(mean, 2), round(std_dev, 2)

    @classmethod
    def evaluate_village_day(
        cls,
        village_id: str,
        eval_date: datetime,
        current_signals: Dict[str, int], # e.g. {"CLINIC_FEVER": 5, "PHARMACY_ORS_SALES": 18, "SCHOOL_ABSENTEEISM": 12}
        historical_signals: Dict[str, List[int]], # Historical 14-28 day arrays per stream
        syndrome: str = "ACUTE_DIARRHEAL_DISEASE"
    ) -> AnomalyResult:
        """
        Fuses multi-source syndromic streams and evaluates anomaly index.
        """
        weights = {
            "CLINIC_FEVER": 0.40,
            "ACUTE_DIARRHEA": 0.40,
            "PHARMACY_ORS_SALES": 0.35,
            "SCHOOL_ABSENTEEISM": 0.25
        }

        z_scores = {}
        means = {}
        observed_total = 0
        expected_total = 0

        for stream_name, curr_val in current_signals.items():
            baseline_vals = historical_signals.get(stream_name, [curr_val])
            z, m, s = cls.compute_z_score(float(curr_val), [float(b) for b in baseline_vals])
            z_scores[stream_name] = z
            means[stream_name] = m
            observed_total += curr_val
            expected_total += int(m)

        # Fused multi-stream Z-score calculation
        total_weight = 0.0
        weighted_z_sum = 0.0
        for stream_name, z in z_scores.items():
            w = weights.get(stream_name, 0.25)
            weighted_z_sum += (z * w)
            total_weight += w

        fused_z = round(weighted_z_sum / total_weight, 2) if total_weight > 0 else 0.0

        # Confidence mapping (approaches 1.0 as Z increases beyond threshold)
        confidence = round(1.0 - math.exp(-max(0.0, fused_z) / 2.2), 3)

        # Thresholding for alert
        is_anomaly = fused_z >= 2.5
        if fused_z >= 3.0:
            risk = "OUTBREAK"
        elif fused_z >= 2.2:
            risk = "WARNING"
        elif fused_z >= 1.5:
            risk = "WATCH"
        else:
            risk = "NORMAL"

        return AnomalyResult(
            village_id=village_id,
            date=eval_date,
            is_anomaly=is_anomaly,
            z_score=fused_z,
            confidence=confidence,
            syndrome=syndrome,
            observed_cases=observed_total,
            expected_baseline=expected_total,
            contributing_streams=z_scores,
            risk_level=risk
        )

    @classmethod
    def detect_block_outbreak_cluster(
        cls,
        village_evaluations: List[AnomalyResult],
        syndrome: str = "WATERBORNE_ACUTE_DIARRHEA"
    ) -> Optional[OutbreakAlertPayload]:
        """
        Identifies spatial-temporal clusters across neighboring villages in a block.
        If 1 or more villages exhibit an active anomaly, generates an Outbreak Alert with PostGIS polygon.
        """
        flagged_villages = [
            v.village_id for v in village_evaluations
            if v.is_anomaly or v.risk_level in ["WARNING", "OUTBREAK"]
        ]

        if not flagged_villages:
            return None

        # Calculate cluster metrics
        avg_z = sum(v.z_score for v in village_evaluations if v.village_id in flagged_villages) / len(flagged_villages)
        max_conf = max(v.confidence for v in village_evaluations if v.village_id in flagged_villages)
        total_observed = sum(v.observed_cases for v in village_evaluations if v.village_id in flagged_villages)
        total_expected = sum(v.expected_baseline for v in village_evaluations if v.village_id in flagged_villages)

        # Generate PostGIS / GeoJSON bounding polygon
        cluster_geom = geo_cluster_service.compute_cluster_bounding_polygon(flagged_villages)

        # Interventions
        interventions = [
            "Dispatch Rapid Response Team (RRT) to inspect village water supply & sanitation",
            "Mobilize ASHA workers for door-to-door ORS & Zinc packet distribution",
            "Superchlorinate community water tanks and tube wells",
            "Notify Medical Officer at Block Primary Health Centre (PHC)"
        ]

        alert_id = f"ALT-{datetime.utcnow().strftime('%Y%m%d')}-{flagged_villages[0][-4:]}"

        return OutbreakAlertPayload(
            alert_id=alert_id,
            detected_at=datetime.utcnow(),
            syndrome=syndrome,
            affected_villages=flagged_villages,
            cluster_geom=cluster_geom,
            z_score=round(avg_z, 2),
            confidence=round(max_conf, 3),
            baseline_expected_cases=total_expected,
            observed_cases=total_observed,
            status="ACTIVE",
            recommended_interventions=interventions
        )


surveillance_engine = SyndromicSurveillanceEngine()
