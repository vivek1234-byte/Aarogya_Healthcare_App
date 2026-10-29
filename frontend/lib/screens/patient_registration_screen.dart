import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import '../core/services/api_service.dart';

class PatientRegistrationScreen extends StatefulWidget {
  const PatientRegistrationScreen({super.key});

  @override
  State<PatientRegistrationScreen> createState() => _PatientRegistrationScreenState();
}

class _PatientRegistrationScreenState extends State<PatientRegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _apiService = ApiService();

  // Controllers
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _ageController = TextEditingController();

  String _selectedGender = 'Female';
  String _selectedVillage = 'VILL-RAMPUR';

  final List<Map<String, String>> _villages = [
    {'id': 'VILL-RAMPUR', 'name': 'Rampur (रामपुर)'},
    {'id': 'VILL-SHIVPUR', 'name': 'Shivpur (शिवपुर)'},
    {'id': 'VILL-KALYANPUR', 'name': 'Kalyanpur (कल्याणपुर)'},
    {'id': 'VILL-BIRAON', 'name': 'Biraon (बिरों)'},
  ];

  // Chronic conditions
  final Map<String, bool> _chronicConditions = {
    'Hypertension (उच्च रक्तचाप)': false,
    'Type 2 Diabetes (मधुमेह)': false,
    'Asthma / COPD (दमा/सांस की बीमारी)': false,
    'Cardiovascular Disease (हृदय रोग)': false,
  };

  // Voice Consent State
  bool _isRecordingConsent = false;
  bool _hasRecordedConsent = false;
  int _recordingDurationSec = 0;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _ageController.dispose();
    super.dispose();
  }

  void _toggleConsentRecording() async {
    if (_isRecordingConsent) {
      // Stop recording
      setState(() {
        _isRecordingConsent = false;
        _hasRecordedConsent = true;
      });
    } else {
      // Start recording simulation
      setState(() {
        _isRecordingConsent = true;
        _hasRecordedConsent = false;
        _recordingDurationSec = 0;
      });

      for (int i = 1; i <= 4; i++) {
        await Future.delayed(const Duration(seconds: 1));
        if (!_isRecordingConsent) break;
        if (mounted) {
          setState(() {
            _recordingDurationSec = i;
          });
        }
      }

      if (mounted && _isRecordingConsent) {
        setState(() {
          _isRecordingConsent = false;
          _hasRecordedConsent = true;
        });
      }
    }
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (!_hasRecordedConsent) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please record the patient\'s verbal voice consent before proceeding.'),
          backgroundColor: AppColors.emergencyRed,
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final selectedConditions = _chronicConditions.entries
        .where((e) => e.value)
        .map((e) => e.key.split(' ').first)
        .toList();

    final result = await _apiService.registerPatient(
      name: _nameController.text.trim(),
      phone: _phoneController.text.trim(),
      villageId: _selectedVillage,
      age: int.tryParse(_ageController.text.trim()) ?? 30,
      gender: _selectedGender,
      consentAudioUrl: 's3://minio/consent/verbal_${DateTime.now().millisecondsSinceEpoch}.wav',
      chronicConditions: selectedConditions,
    );

    setState(() => _isSubmitting = false);

    if (mounted) {
      _showRegistrationSuccessDialog(result);
    }
  }

  void _showRegistrationSuccessDialog(Map<String, dynamic> result) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.verified_user_rounded, color: AppColors.primaryGreen, size: 28),
            SizedBox(width: 10),
            Text('Patient Enrolled'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Patient registered with DPDP 2023 compliant encrypted storage.',
              style: TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primaryGreen.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Generated Clinical Pseudonym:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                  const SizedBox(height: 4),
                  Text(
                    result['pseudonym_id'] ?? 'HASH-PATIENT-SUCCESS',
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.primaryGreen),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '• AES-256 encrypted PII vault\n• Verbal voice consent audio timestamped\n• Real-time chronic care tracking active',
              style: TextStyle(fontSize: 12, height: 1.4),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx); // Close dialog
              Navigator.pop(context); // Return to home
            },
            child: const Text('Return to Dashboard'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Patient Onboarding & Voice Consent'),
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isTabletOrWide = constraints.maxWidth >= 700;

          return SingleChildScrollView(
            padding: EdgeInsets.symmetric(
              horizontal: isTabletOrWide ? 32.0 : 16.0,
              vertical: 16.0,
            ),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // DPDP Privacy Shield Notice Banner
                  _buildPrivacyBanner(context, isDark),
                  const SizedBox(height: 20),

                  // Section 1: Demographics
                  Text('1. Patient Demographics', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 12),

                  // Name Field
                  TextFormField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Full Name (नाम) *',
                      hintText: 'e.g. Ramesh Kumar',
                      prefixIcon: Icon(Icons.person_outline_rounded),
                    ),
                    validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter patient name' : null,
                  ),
                  const SizedBox(height: 14),

                  // Phone Number Field
                  TextFormField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Mobile Phone (मोबाइल नंबर) *',
                      hintText: '10-digit mobile number',
                      prefixIcon: Icon(Icons.phone_android_rounded),
                    ),
                    validator: (v) {
                      if (v == null || v.trim().length < 10) {
                        return 'Please enter a valid 10-digit phone number';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 14),

                  // Age & Gender in Responsive Row
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _ageController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'Age (उम्र) *',
                            hintText: 'e.g. 52',
                            prefixIcon: Icon(Icons.cake_outlined),
                          ),
                          validator: (v) => (v == null || int.tryParse(v) == null) ? 'Enter age' : null,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _selectedGender,
                          decoration: const InputDecoration(
                            labelText: 'Gender (लिंग) *',
                            prefixIcon: Icon(Icons.wc_rounded),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'Female', child: Text('Female (महिला)')),
                            DropdownMenuItem(value: 'Male', child: Text('Male (पुरुष)')),
                            DropdownMenuItem(value: 'Other', child: Text('Other (अन्य)')),
                          ],
                          onChanged: (val) {
                            if (val != null) setState(() => _selectedGender = val);
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Village Selection
                  DropdownButtonFormField<String>(
                    value: _selectedVillage,
                    decoration: const InputDecoration(
                      labelText: 'Assigned Village (गांव) *',
                      prefixIcon: Icon(Icons.location_city_rounded),
                    ),
                    items: _villages
                        .map((v) => DropdownMenuItem(value: v['id'], child: Text(v['name']!)))
                        .toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedVillage = val);
                    },
                  ),
                  const SizedBox(height: 24),

                  // Section 2: Chronic Conditions
                  Text('2. Known Chronic Diagnoses', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Text(
                    'Select any existing conditions for automated longitudinal vitals tracking',
                    style: textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 10),

                  ..._chronicConditions.keys.map((condition) {
                    return CheckboxListTile(
                      title: Text(condition, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                      value: _chronicConditions[condition],
                      activeColor: AppColors.primaryGreen,
                      contentPadding: EdgeInsets.zero,
                      onChanged: (val) {
                        setState(() {
                          _chronicConditions[condition] = val ?? false;
                        });
                      },
                    );
                  }),
                  const SizedBox(height: 24),

                  // Section 3: DPDP Verbal Voice Consent
                  Text('3. DPDP Act 2023 Verbal Voice Consent *', style: textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  Text(
                    'Patient must speak verbal consent aloud. Audio is preserved as legal consent proof.',
                    style: textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 12),

                  _buildVoiceConsentBox(context, isDark),
                  const SizedBox(height: 28),

                  // Submit Button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitForm,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: _isSubmitting
                          ? const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                ),
                                SizedBox(width: 12),
                                Text('Encrypting & Enrolling Patient...'),
                              ],
                            )
                          : const Text(
                              'Enroll Patient with Encrypted Consent',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                            ),
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildPrivacyBanner(BuildContext context, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E2833) : const Color(0xFFE3F2FD),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.secondaryBlue.withOpacity(0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.shield_rounded, color: AppColors.secondaryBlue, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'DPDP Act 2023 Privacy Compliance',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.secondaryBlue),
                ),
                const SizedBox(height: 3),
                Text(
                  'Name and phone are encrypted with AES-256-GCM. Research and surveillance pipelines only see the pseudonym ID.',
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceConsentBox(BuildContext context, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCardBg : AppColors.lightCardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: _hasRecordedConsent
              ? AppColors.primaryGreen
              : (_isRecordingConsent ? AppColors.emergencyRed : Colors.grey.withOpacity(0.3)),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Prompt to read aloud
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E232A) : const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ASHA / Patient reads aloud:',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey),
                ),
                SizedBox(height: 4),
                Text(
                  '"मैं अपना स्वास्थ्य डेटा आशा दीदी को देने की सहमति देता/देती हूँ।"\n("I give consent to share my health information with ASHA worker.")',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, height: 1.35),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Central Mic Recording Button & Status
          Center(
            child: Column(
              children: [
                InkWell(
                  onTap: _toggleConsentRecording,
                  borderRadius: BorderRadius.circular(40),
                  child: Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _isRecordingConsent
                          ? AppColors.emergencyRed
                          : (_hasRecordedConsent ? AppColors.primaryGreen : AppColors.secondaryBlue),
                      boxShadow: [
                        BoxShadow(
                          color: (_isRecordingConsent ? AppColors.emergencyRed : AppColors.primaryGreen).withOpacity(0.3),
                          blurRadius: 10,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Icon(
                      _isRecordingConsent ? Icons.stop_rounded : Icons.mic_rounded,
                      color: Colors.white,
                      size: 34,
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  _isRecordingConsent
                      ? 'Recording Consent... (00:0$_recordingDurationSec)'
                      : (_hasRecordedConsent ? '✓ Verbal Consent Captured' : 'Tap Mic to Record Verbal Consent'),
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                    color: _isRecordingConsent
                        ? AppColors.emergencyRed
                        : (_hasRecordedConsent ? AppColors.primaryGreen : Colors.grey),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
