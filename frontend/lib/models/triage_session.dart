class TriageTurnResponse {
  final String sessionId;
  final String transcription;
  final String detectedLanguage;
  final List<String> extractedSymptoms;
  final List<String> dangerSigns;
  final bool isFinal;
  final String? triageLevel; // EMERGENCY, REFER, TREAT_LOCALLY, HOME_CARE
  final String? decisionRationale;
  final String? nextQuestion;
  final List<String> checklist;
  final String? doctorSummaryUrl;
  final bool isRedFlagOverridden;

  TriageTurnResponse({
    required this.sessionId,
    required this.transcription,
    required this.detectedLanguage,
    required this.extractedSymptoms,
    required this.dangerSigns,
    required this.isFinal,
    this.triageLevel,
    this.decisionRationale,
    this.nextQuestion,
    this.checklist = const [],
    this.doctorSummaryUrl,
    this.isRedFlagOverridden = false,
  });

  factory TriageTurnResponse.fromJson(Map<String, dynamic> json) {
    return TriageTurnResponse(
      sessionId: json['session_id'] ?? '',
      transcription: json['transcription'] ?? '',
      detectedLanguage: json['detected_language'] ?? 'hi',
      extractedSymptoms: (json['extracted_symptoms'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      dangerSigns: (json['danger_signs'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      isFinal: json['is_final'] ?? false,
      triageLevel: json['triage_level'],
      decisionRationale: json['decision_rationale'],
      nextQuestion: json['next_question'],
      checklist: (json['checklist'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      doctorSummaryUrl: json['doctor_summary_url'],
      isRedFlagOverridden: json['is_red_flag_overridden'] ?? false,
    );
  }
}
