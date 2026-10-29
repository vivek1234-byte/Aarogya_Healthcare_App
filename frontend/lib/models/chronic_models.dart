class VitalsPoint {
  final DateTime date;
  final double systolic;
  final double diastolic;
  final double? glucose;

  VitalsPoint({
    required this.date,
    required this.systolic,
    required this.diastolic,
    this.glucose,
  });
}

class ChronicActionItem {
  final String patientId;
  final String pseudonymId;
  final int age;
  final String gender;
  final String riskLevel; // CRITICAL, HIGH, MODERATE, LOW
  final int actionPriority; // 1=Immediate, 2=Within 24h, 3=Within 7 days
  final String recommendedAction;
  final List<String> flags;
  final double? latestSystolic;
  final double adherenceRatePct;

  ChronicActionItem({
    required this.patientId,
    required this.pseudonymId,
    required this.age,
    required this.gender,
    required this.riskLevel,
    required this.actionPriority,
    required this.recommendedAction,
    this.flags = const [],
    this.latestSystolic,
    this.adherenceRatePct = 100.0,
  });

  factory ChronicActionItem.fromJson(Map<String, dynamic> json) {
    return ChronicActionItem(
      patientId: json['patient_id'] ?? '',
      pseudonymId: json['pseudonym_id'] ?? '',
      age: json['age'] ?? 0,
      gender: json['gender'] ?? 'Unknown',
      riskLevel: json['risk_level'] ?? 'LOW',
      actionPriority: json['action_priority'] ?? 4,
      recommendedAction: json['recommended_action'] ?? '',
      flags: (json['flags'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      latestSystolic: (json['latest_systolic'] as num?)?.toDouble(),
      adherenceRatePct: (json['adherence_rate_pct'] as num?)?.toDouble() ?? 100.0,
    );
  }
}

class VoiceCheckinResult {
  final int? systolicBp;
  final int? diastolicBp;
  final double? bloodGlucose;
  final String? glucoseContext;
  final String? adherenceStatus;
  final String? missReason;
  final String riskLevel;
  final String voiceFeedbackTextHi;
  final String voiceFeedbackTextEn;

  VoiceCheckinResult({
    this.systolicBp,
    this.diastolicBp,
    this.bloodGlucose,
    this.glucoseContext,
    this.adherenceStatus,
    this.missReason,
    required this.riskLevel,
    required this.voiceFeedbackTextHi,
    required this.voiceFeedbackTextEn,
  });

  factory VoiceCheckinResult.fromJson(Map<String, dynamic> json) {
    final parsed = json['parsed'] ?? {};
    final eval = json['evaluation'] ?? {};
    return VoiceCheckinResult(
      systolicBp: parsed['systolic_bp'],
      diastolicBp: parsed['diastolic_bp'],
      bloodGlucose: (parsed['blood_glucose'] as num?)?.toDouble(),
      glucoseContext: parsed['glucose_context'],
      adherenceStatus: parsed['adherence_status'],
      missReason: parsed['miss_reason'],
      riskLevel: eval['risk_level'] ?? 'LOW',
      voiceFeedbackTextHi: json['voice_feedback_text_hi'] ?? '',
      voiceFeedbackTextEn: json['voice_feedback_text_en'] ?? '',
    );
  }
}
