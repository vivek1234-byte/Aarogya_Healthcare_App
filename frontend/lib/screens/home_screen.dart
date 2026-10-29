import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import 'voice_triage_screen.dart';
import 'chronic_care_screen.dart';
import 'asha_action_roster_screen.dart';
import 'outbreak_surveillance_screen.dart';
import 'patient_registration_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'ArogyaSaathi (आरोग्य साथी)',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 19),
            ),
            Text(
              'Rampur Sub-Centre • ASHA Gateway',
              style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
            ),
          ],
        ),
        actions: [
          // Emergency 108 Quick Call Button
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: ElevatedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Calling National Emergency Ambulance (108)...'),
                    backgroundColor: AppColors.emergencyRed,
                  ),
                );
              },
              icon: const Icon(Icons.emergency, color: Colors.white, size: 18),
              label: const Text('108 SOS', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.emergencyRed,
                minimumSize: const Size(90, 36),
                padding: const EdgeInsets.symmetric(horizontal: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Theme Toggle (Dark / Light White Mode)
          IconButton(
            tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode, size: 24),
            onPressed: () => themeProvider.toggleTheme(),
          ),
          // Logout / Switch User
          IconButton(
            tooltip: 'Logout / Switch User',
            icon: const Icon(Icons.logout_rounded, size: 22),
            onPressed: () {
              Navigator.pushReplacementNamed(context, '/login');
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isTabletOrWide = constraints.maxWidth > 650;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Quick Operational Status Banner
                _buildOperationalStatusCard(context, isDark),
                const SizedBox(height: 20),

                Text(
                  'Clinical Decision Support & Actions',
                  style: textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 6),
                Text(
                  'Select a tool to assist village health evaluations',
                  style: textTheme.bodyMedium,
                ),
                const SizedBox(height: 14),

                // 4 Main Feature Cards in Responsive Grid
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: isTabletOrWide ? 2 : 1,
                  childAspectRatio: isTabletOrWide ? 1.6 : 2.1,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  children: [
                    // 1. Voice Triage (Microphone Checklist UI)
                    _buildFeatureCard(
                      context: context,
                      title: 'Voice Triage & Danger Signs',
                      subtitle: 'Hands-free speech symptom check (Chest pain, child danger signs, fever)',
                      icon: Icons.mic_rounded,
                      accentColor: AppColors.primaryGreen,
                      badgeText: 'Zero-Prescription Safe',
                      isDark: isDark,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const VoiceTriageScreen()));
                      },
                    ),

                    // 2. Chronic Care Trends & Vitals
                    _buildFeatureCard(
                      context: context,
                      title: 'Chronic Care & Vitals Curves',
                      subtitle: 'BP & blood glucose trend curves with 7-day early deterioration alert',
                      icon: Icons.show_chart_rounded,
                      accentColor: AppColors.secondaryBlue,
                      badgeText: 'BP & Sugar Trends',
                      isDark: isDark,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const ChronicCareScreen()));
                      },
                    ),

                    // 3. ASHA Priority Action Roster
                    _buildFeatureCard(
                      context: context,
                      title: 'ASHA Daily Priority Roster',
                      subtitle: 'Targeted home visits ranked by clinical urgency (Critical / High / Moderate)',
                      icon: Icons.assignment_late_rounded,
                      accentColor: AppColors.urgentOrange,
                      badgeText: '3 Visits Due Today',
                      isDark: isDark,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const AshaActionRosterScreen()));
                      },
                    ),

                    // 4. Village Outbreak Surveillance
                    _buildFeatureCard(
                      context: context,
                      title: 'Village Outbreak Warning',
                      subtitle: 'Spatio-temporal anomaly map uniting clinic visits, pharmacy ORS & schools',
                      icon: Icons.map_rounded,
                      accentColor: AppColors.warningAmber,
                      badgeText: '1 Village Watch',
                      isDark: isDark,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const OutbreakSurveillanceScreen()));
                      },
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                // Register New Patient with Voice Consent
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 24,
                          backgroundColor: AppColors.primaryGreen.withOpacity(0.15),
                          child: const Icon(Icons.person_add_alt_1, color: AppColors.primaryGreen, size: 26),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Onboard Patient & Voice Consent',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Verbal DPDP consent recording with encrypted PII',
                                style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                              ),
                            ],
                          ),
                        ),
                        ElevatedButton(
                          onPressed: () {
                            Navigator.push(context, MaterialPageRoute(builder: (_) => const PatientRegistrationScreen()));
                          },
                          style: ElevatedButton.styleFrom(
                            minimumSize: const Size(80, 42),
                            padding: const EdgeInsets.symmetric(horizontal: 14),
                          ),
                          child: const Text('Register'),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildOperationalStatusCard(BuildContext context, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder, width: 1.2),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primaryGreen.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.health_and_safety_rounded, color: AppColors.primaryGreen, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(color: AppColors.stableGreen, shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 6),
                    const Text('OFFLINE-READY & ENCRYPTED', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.stableGreen, letterSpacing: 0.5)),
                  ],
                ),
                const SizedBox(height: 3),
                const Text('Rampur Sub-Centre Health Post', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text(
                  'DPDP 2023 Compliant • Multi-source Early Warning Active',
                  style: TextStyle(fontSize: 12, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Color accentColor,
    required String badgeText,
    required bool isDark,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: accentColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(icon, color: accentColor, size: 26),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: accentColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      badgeText,
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: accentColor),
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, letterSpacing: -0.2),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    subtitle,
                    style: TextStyle(fontSize: 13, color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary, height: 1.3),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
