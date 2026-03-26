import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // TODO: change this to your Railway.app URL once deployed
  // For local testing on your phone, use your PC's local network IP e.g. http://192.168.1.x:8000
  static const String baseUrl = 'http://127.0.0.1:8000';
  // --- Auth helpers ---

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  static Future<Map<String, String>> authHeaders() async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // --- Auth endpoints ---

  static Future<Map<String, dynamic>> register({
    required String email,
    required String username,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'username': username, 'password': password}),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    return jsonDecode(response.body);
  }

  // --- Reports endpoints ---

  static Future<List<dynamic>> getMapReports({
    required double lat,
    required double lng,
    double radiusKm = 10.0,
  }) async {
    final headers = await authHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/reports/map?lat=$lat&lng=$lng&radius_km=$radiusKm'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  static Future<bool> submitReport({
    required int categoryId,
    required String title,
    String? description,
    required double latitude,
    required double longitude,
    String severity = 'low',
  }) async {
    final headers = await authHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/reports/'),
      headers: headers,
      body: jsonEncode({
        'category_id': categoryId,
        'title': title,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'severity': severity,
      }),
    );
    return response.statusCode == 201;
  }

  static Future<List<dynamic>> getCategories() async {
    final response = await http.get(Uri.parse('$baseUrl/reports/categories'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  static Future<bool> voteOnReport(int reportId) async {
    final headers = await authHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/reports/$reportId/vote'),
      headers: headers,
    );
    return response.statusCode == 200;
  }
}
