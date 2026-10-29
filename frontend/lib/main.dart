import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'providers/theme_provider.dart';
import 'providers/triage_provider.dart';
import 'providers/chronic_provider.dart';

import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/voice_triage_screen.dart';
import 'screens/chronic_care_screen.dart';
import 'screens/asha_action_roster_screen.dart';
import 'screens/outbreak_surveillance_screen.dart';
import 'screens/patient_registration_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Prefer portrait orientation with tablet landscape capability
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ]);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => TriageProvider()),
        ChangeNotifierProvider(create: (_) => ChronicProvider()),
      ],
      child: const ArogyaSaathiApp(),
    ),
  );
}

class ArogyaSaathiApp extends StatelessWidget {
  const ArogyaSaathiApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return MaterialApp(
      title: 'ArogyaSaathi (आरोग्य साथी)',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProvider.themeMode,
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/': (context) => const HomeScreen(),
        '/triage': (context) => const VoiceTriageScreen(),
        '/chronic': (context) => const ChronicCareScreen(),
        '/roster': (context) => const AshaActionRosterScreen(),
        '/outbreak': (context) => const OutbreakSurveillanceScreen(),
        '/register': (context) => const PatientRegistrationScreen(),
      },
    );
  }
}
