class Patient {
  final String id;
  final String pseudonymId;
  final String villageId;
  final int age;
  final String gender;
  final String primaryLanguage;
  final bool isActive;
  final Map<String, dynamic>? pii;

  Patient({
    required this.id,
    required this.pseudonymId,
    required this.villageId,
    required this.age,
    required this.gender,
    this.primaryLanguage = 'hi',
    this.isActive = true,
    this.pii,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'] ?? '',
      pseudonymId: json['pseudonym_id'] ?? '',
      villageId: json['village_id'] ?? '',
      age: json['age'] ?? 0,
      gender: json['gender'] ?? 'Unknown',
      primaryLanguage: json['primary_language'] ?? 'hi',
      isActive: json['is_active'] ?? true,
      pii: json['pii'],
    );
  }
}
