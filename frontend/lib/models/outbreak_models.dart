class OutbreakAlert {
  final String id;
  final String villageId;
  final String villageName;
  final String syndrome;
  final String alertLevel; // NORMAL, WATCH, WARNING, OUTBREAK
  final double zScore;
  final int observedCases;
  final double baselineCases;
  final double percentAboveBaseline;
  final List<String> fusedSignals;
  final String recommendedIntervention;
  final DateTime detectedAt;
  final double latitude;
  final double longitude;
  final int populationAtRisk;
  final List<String> rrtChecklist;

  OutbreakAlert({
    required this.id,
    required this.villageId,
    required this.villageName,
    required this.syndrome,
    required this.alertLevel,
    required this.zScore,
    required this.observedCases,
    required this.baselineCases,
    required this.percentAboveBaseline,
    required this.fusedSignals,
    required this.recommendedIntervention,
    required this.detectedAt,
    required this.latitude,
    required this.longitude,
    required this.populationAtRisk,
    required this.rrtChecklist,
  });

  factory OutbreakAlert.fromJson(Map<String, dynamic> json) {
    return OutbreakAlert(
      id: json['id'] ?? '',
      villageId: json['village_id'] ?? '',
      villageName: json['village_name'] ?? json['village_id'] ?? 'Village',
      syndrome: json['syndrome'] ?? 'ADD',
      alertLevel: json['alert_level'] ?? 'NORMAL',
      zScore: (json['z_score'] ?? 0.0).toDouble(),
      observedCases: json['observed_cases'] ?? 0,
      baselineCases: (json['baseline_cases'] ?? 0.0).toDouble(),
      percentAboveBaseline: (json['percent_above_baseline'] ?? 0.0).toDouble(),
      fusedSignals: List<String>.from(json['fused_signals'] ?? []),
      recommendedIntervention: json['recommended_intervention'] ?? '',
      detectedAt: json['detected_at'] != null ? DateTime.parse(json['detected_at']) : DateTime.now(),
      latitude: (json['latitude'] ?? 25.3176).toDouble(),
      longitude: (json['longitude'] ?? 82.9739).toDouble(),
      populationAtRisk: json['population_at_risk'] ?? 1200,
      rrtChecklist: List<String>.from(json['rrt_checklist'] ?? [
        'Dispatch Rapid Response Team with Chlorine tablets (halazone)',
        'Establish village ORS corner at Anganwadi / Sub-centre',
        'Collect 5 stool and 3 source water samples for lab culture',
        'Boil water public advisory broadcast via village loudspeaker'
      ]),
    );
  }
}
