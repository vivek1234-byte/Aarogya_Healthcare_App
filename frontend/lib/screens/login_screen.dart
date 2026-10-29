import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme/app_theme.dart';
import '../providers/theme_provider.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _workerIdController = TextEditingController(text: 'ASHA-RAMPUR-7821');
  final _pinController = TextEditingController(text: '1234');
  
  bool _obscurePin = true;
  bool _isLoading = false;
  bool _isBiometricScanning = false;
  String _selectedRole = 'ASHA'; // ASHA, MO, ANM

  late AnimationController _animController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.95, end: 1.08).animate(
      CurvedAnimation(parent: _animController, curve: Curves.easeInOut),
    );

    _fadeAnimation = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeIn,
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    _workerIdController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  void _selectDemoProfile(String role, String id, String pin) {
    setState(() {
      _selectedRole = role;
      _workerIdController.text = id;
      _pinController.text = pin;
    });
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(milliseconds: 900));

    if (!mounted) return;
    setState(() => _isLoading = false);

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  Future<void> _handleBiometricLogin() async {
    setState(() => _isBiometricScanning = true);
    await Future.delayed(const Duration(milliseconds: 1200));

    if (!mounted) return;
    setState(() => _isBiometricScanning = false);

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✓ Biometric Verified: Sunita Sharma (ASHA Rampur)'),
        backgroundColor: AppColors.primaryGreen,
        duration: Duration(seconds: 2),
      ),
    );

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final isDark = themeProvider.isDarkMode;
    final size = MediaQuery.of(context).size;
    final isTablet = size.width >= 700;

    return Scaffold(
      body: Stack(
        children: [
          // 1. Ambient Animated Gradient Mesh Background
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: isDark
                      ? [
                          const Color(0xFF0A1017),
                          const Color(0xFF0F1E24),
                          const Color(0xFF09141A),
                        ]
                      : [
                          const Color(0xFFEFFBF5),
                          const Color(0xFFE6F4F1),
                          const Color(0xFFF0FDF4),
                        ],
                ),
              ),
            ),
          ),

          // Floating Ambient Glow Orbs
          Positioned(
            top: -60,
            right: -60,
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppColors.primaryGreen.withOpacity(isDark ? 0.35 : 0.25),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            bottom: -80,
            left: -60,
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppColors.secondaryBlue.withOpacity(isDark ? 0.30 : 0.20),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),

          // 2. Main Login Content Card
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: EdgeInsets.symmetric(
                  horizontal: isTablet ? 64.0 : 24.0,
                  vertical: 24.0,
                ),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 480),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Top Mode Toggle & Emergency Badge
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.primaryGreen.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: AppColors.primaryGreen.withOpacity(0.3),
                              ),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.shield_rounded, size: 14, color: AppColors.primaryGreen),
                                SizedBox(width: 5),
                                Text(
                                  'DPDP Act 2023 Secure',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.primaryGreen,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: Icon(
                              isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                              color: isDark ? Colors.amber : Colors.slate,
                            ),
                            tooltip: 'Toggle Theme',
                            onPressed: () => themeProvider.toggleTheme(),
                          ),
                        ],
                      ),
                      const SizedBox(height: 18),

                      // Animated Healthcare Glowing Emblem
                      ScaleTransition(
                        scale: _pulseAnimation,
                        child: Container(
                          width: 84,
                          height: 84,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(
                              colors: [Color(0xFF059669), Color(0xFF10B981)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF059669).withOpacity(0.4),
                                blurRadius: 28,
                                spreadRadius: 4,
                              ),
                            ],
                          ),
                          child: const Icon(
                            Icons.health_and_safety_rounded,
                            color: Colors.white,
                            size: 44,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Brand Titles
                      const Text(
                        'ArogyaSaathi',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w900,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'आरोग्य साथी • Frontline Clinical Gateway',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Glassmorphic Auth Card
                      Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF131D26).withOpacity(0.85) : Colors.white.withOpacity(0.90),
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(
                            color: isDark ? Colors.white.withOpacity(0.1) : Colors.black.withOpacity(0.06),
                            width: 1.5,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(isDark ? 0.35 : 0.08),
                              blurRadius: 30,
                              offset: const Offset(0, 10),
                            ),
                          ],
                        ),
                        child: Form(
                          key: _formKey,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Select Clinical Role',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.5,
                                ),
                              ),
                              const SizedBox(height: 10),

                              // Role Toggle Chips
                              Row(
                                children: [
                                  _buildRoleTab('ASHA', '👩‍⚕️ ASHA', 'ASHA-RAMPUR-7821', '1234'),
                                  const SizedBox(width: 8),
                                  _buildRoleTab('MO', '🩺 MO Doctor', 'MO-PHC-4091', '5678'),
                                  const SizedBox(width: 8),
                                  _buildRoleTab('ANM', '💉 ANM Lead', 'ANM-SUB-3105', '9012'),
                                ],
                              ),
                              const SizedBox(height: 20),

                              // Worker ID / Mobile Input
                              TextFormField(
                                controller: _workerIdController,
                                decoration: InputDecoration(
                                  labelText: 'Healthcare Worker ID / Mobile',
                                  hintText: 'e.g. ASHA-RAMPUR-7821',
                                  prefixIcon: const Icon(Icons.badge_outlined),
                                  filled: true,
                                  fillColor: isDark ? const Color(0xFF1A2633) : const Color(0xFFF8FAFC),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(14),
                                    borderSide: BorderSide.none,
                                  ),
                                ),
                                validator: (v) => (v == null || v.trim().isEmpty) ? 'Please enter your Worker ID' : null,
                              ),
                              const SizedBox(height: 14),

                              // Security PIN / Password Input
                              TextFormField(
                                controller: _pinController,
                                obscureText: _obscurePin,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                  labelText: 'Security PIN / Password',
                                  hintText: '••••',
                                  prefixIcon: const Icon(Icons.lock_outline_rounded),
                                  suffixIcon: IconButton(
                                    icon: Icon(
                                      _obscurePin ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                    ),
                                    onPressed: () => setState(() => _obscurePin = !_obscurePin),
                                  ),
                                  filled: true,
                                  fillColor: isDark ? const Color(0xFF1A2633) : const Color(0xFFF8FAFC),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(14),
                                    borderSide: BorderSide.none,
                                  ),
                                ),
                                validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your 4-digit PIN' : null,
                              ),
                              const SizedBox(height: 20),

                              // Primary Login Button
                              SizedBox(
                                width: double.infinity,
                                height: 50,
                                child: ElevatedButton(
                                  onPressed: _isLoading ? null : _handleLogin,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.primaryGreen,
                                    foregroundColor: Colors.white,
                                    elevation: 4,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(14),
                                    ),
                                  ),
                                  child: _isLoading
                                      ? const SizedBox(
                                          width: 22,
                                          height: 22,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2.5,
                                            color: Colors.white,
                                          ),
                                        )
                                      : const Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            Text(
                                              'Access Clinical Dashboard',
                                              style: TextStyle(
                                                fontSize: 15,
                                                fontWeight: FontWeight.w800,
                                              ),
                                            ),
                                            SizedBox(width: 8),
                                            Icon(Icons.arrow_forward_rounded, size: 18),
                                          ],
                                        ),
                                ),
                              ),
                              const SizedBox(height: 14),

                              // Biometric Fingerprint Auth Button
                              SizedBox(
                                width: double.infinity,
                                height: 46,
                                child: OutlinedButton.icon(
                                  onPressed: _isBiometricScanning ? null : _handleBiometricLogin,
                                  icon: _isBiometricScanning
                                      ? const SizedBox(
                                          width: 18,
                                          height: 18,
                                          child: CircularProgressIndicator(strokeWidth: 2),
                                        )
                                      : const Icon(Icons.fingerprint_rounded, size: 22),
                                  label: Text(
                                    _isBiometricScanning ? 'Scanning Fingerprint...' : 'Biometric Quick Login',
                                    style: const TextStyle(fontWeight: FontWeight.w700),
                                  ),
                                  style: OutlinedButton.styleFrom(
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(14),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Footer Security & Offline Notice
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.wifi_off_rounded,
                            size: 14,
                            color: isDark ? Colors.grey[500] : Colors.grey[600],
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'Offline-First Enabled • Local Sync Vault',
                            style: TextStyle(
                              fontSize: 12,
                              color: isDark ? Colors.grey[500] : Colors.grey[600],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRoleTab(String role, String label, String id, String pin) {
    final isSelected = _selectedRole == role;
    return Expanded(
      child: GestureDetector(
        onTap: () => _selectDemoProfile(role, id, pin),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected
                ? AppColors.primaryGreen
                : (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF1E2B38) : const Color(0xFFF1F5F9)),
            borderRadius: BorderRadius.circular(12),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: AppColors.primaryGreen.withOpacity(0.35),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : [],
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                color: isSelected
                    ? Colors.white
                    : (Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
