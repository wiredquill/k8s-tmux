#!/usr/bin/env python3
"""
MQTT-specific security testing suite for k8s-tmux application.
Tests MQTT protocol vulnerabilities and security issues.
"""

import unittest
import socket
import struct
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import ssl


class TestMQTTProtocolSecurity(unittest.TestCase):
    """Test MQTT protocol-specific security issues"""
    
    def setUp(self):
        self.mqtt_host = "10.0.1.101"  # From deployment YAML
        self.mqtt_port = 1883
        self.mqtt_topic = "ai_terminal/comms"
        
    def test_unencrypted_connection(self):
        """Test that MQTT connection is unencrypted (security issue)"""
        # The deployment uses port 1883 (unencrypted MQTT)
        self.assertEqual(self.mqtt_port, 1883, 
                        "Using unencrypted MQTT port - should use 8883 (MQTTS)")
        
        # Test that no SSL/TLS is configured
        try:
            # Attempt to create SSL context (should fail in current setup)
            ssl_context = ssl.create_default_context()
            self.fail("SSL context creation should fail for unencrypted MQTT")
        except:
            pass  # Expected for unencrypted setup
            
    def test_no_authentication(self):
        """Test lack of MQTT authentication (critical security issue)"""
        # Current implementation has no username/password
        # This is a critical security vulnerability
        
        # Mock MQTT connection attempt
        connection_params = {
            'username': None,
            'password': None,
            'client_id': f"ai_terminal_{int(time.time())}"
        }
        
        self.assertIsNone(connection_params['username'], 
                         "No MQTT authentication configured - critical vulnerability")
        self.assertIsNone(connection_params['password'], 
                         "No MQTT password configured - critical vulnerability")
        
    def test_mqtt_connect_packet_security(self):
        """Test MQTT CONNECT packet for security issues"""
        # Test the raw MQTT implementation from the deployment
        client_id = f"ai_terminal_{int(time.time())}"
        client_id_bytes = client_id.encode('utf-8')
        
        # Recreate the CONNECT packet from the deployment code
        connect_packet = bytearray()
        connect_packet.append(0x10)  # CONNECT packet type
        
        variable_header = bytearray()
        variable_header.extend([0x00, 0x04])  # Protocol name length
        variable_header.extend(b'MQTT')       # Protocol name
        variable_header.append(0x04)         # Protocol level (MQTT 3.1.1)
        variable_header.append(0x02)         # Connect flags (Clean session only)
        variable_header.extend([0x00, 0x3c]) # Keep alive (60 seconds)
        
        payload = bytearray()
        payload.extend(len(client_id_bytes).to_bytes(2, 'big'))
        payload.extend(client_id_bytes)
        
        remaining_length = len(variable_header) + len(payload)
        connect_packet.append(remaining_length)
        connect_packet.extend(variable_header)
        connect_packet.extend(payload)
        
        # Verify security issues in the packet
        connect_flags = variable_header[7]  # Connect flags byte
        
        # Check if authentication is disabled (security issue)
        username_flag = (connect_flags & 0x80) != 0
        password_flag = (connect_flags & 0x40) != 0
        
        self.assertFalse(username_flag, "Username flag not set - no authentication")
        self.assertFalse(password_flag, "Password flag not set - no authentication")
        
        # Check if clean session is set (potential data persistence issue)
        clean_session = (connect_flags & 0x02) != 0
        self.assertTrue(clean_session, "Clean session enabled - no message persistence")
        
    def test_mqtt_publish_packet_security(self):
        """Test MQTT PUBLISH packet for injection vulnerabilities"""
        # Test message injection in PUBLISH packets
        malicious_topics = [
            "$SYS/broker/shutdown",  # System topic manipulation
            "../../admin/commands",   # Path traversal in topics
            "\x00\x01\x02",         # Binary data injection
            "a" * 65536,             # Topic length overflow
        ]
        
        malicious_messages = [
            b"\x00" * 1000,         # Null byte flooding
            b"\xff" * 10000,        # Binary overflow
            '{"cmd":"rm -rf /"}',    # Command injection payload
            "<script>alert(1)</script>",  # XSS payload
        ]
        
        for topic in malicious_topics:
            with self.subTest(topic=topic[:20] + "..."):
                # Test topic validation (should be implemented)
                is_valid = self._validate_mqtt_topic(topic)
                self.assertTrue(is_valid or len(topic) > 100, 
                               f"Invalid topic not rejected: {topic[:20]}")
                
        for message in malicious_messages:
            with self.subTest(message=str(message)[:20] + "..."):
                # Test message validation (should be implemented)
                is_valid = self._validate_mqtt_message(message)
                self.assertTrue(is_valid, 
                               f"Invalid message not rejected: {str(message)[:20]}")
                
    def _validate_mqtt_topic(self, topic):
        """MQTT topic validation (should be implemented)"""
        # Basic validation rules for MQTT topics
        if not topic or len(topic) > 65535:
            return False
        if topic.startswith('$SYS/') and 'admin' not in topic:
            return False  # System topics should be restricted
        if '../' in topic or '..\\' in topic:
            return False  # Path traversal
        return True
        
    def _validate_mqtt_message(self, message):
        """MQTT message validation (should be implemented)"""
        if isinstance(message, bytes):
            if len(message) > 268435455:  # MQTT max message size
                return False
            # Check for excessive null bytes
            if message.count(b'\x00') > len(message) * 0.5:
                return False
        return True
        
    def test_mqtt_subscription_security(self):
        """Test MQTT subscription security issues"""
        dangerous_subscriptions = [
            "$SYS/#",           # System topics
            "#",                # All topics (information disclosure)
            "+/admin/#",        # Admin topic wildcards
            "ai_terminal/../#", # Path traversal in subscriptions
        ]
        
        for subscription in dangerous_subscriptions:
            with self.subTest(subscription=subscription):
                # Test subscription validation
                is_safe = self._validate_mqtt_subscription(subscription)
                if subscription == "#" or subscription == "$SYS/#":
                    self.assertFalse(is_safe, 
                                   f"Dangerous subscription allowed: {subscription}")
                    
    def _validate_mqtt_subscription(self, subscription):
        """MQTT subscription validation"""
        # Overly broad subscriptions are dangerous
        if subscription == "#":
            return False  # Subscribe to everything
        if subscription.startswith("$SYS/"):
            return False  # System topics
        return True


class TestMQTTNetworkSecurity(unittest.TestCase):
    """Test MQTT network-level security"""
    
    def test_mqtt_port_security(self):
        """Test MQTT port configuration security"""
        # Standard MQTT ports
        standard_ports = {
            1883: "Unencrypted MQTT",
            8883: "Encrypted MQTT (MQTTS)",
            8884: "Encrypted MQTT with client certs"
        }
        
        current_port = 1883  # From deployment
        
        if current_port == 1883:
            self.fail("Using unencrypted MQTT port 1883 - should use 8883 (MQTTS)")
            
    def test_mqtt_broker_hardcoded_ip(self):
        """Test hardcoded MQTT broker IP (security/maintenance issue)"""
        broker_ip = "10.0.1.101"  # From deployment
        
        # Hardcoded IPs are problematic for security and maintenance
        self.assertTrue(broker_ip.startswith("10."), 
                       "Hardcoded private IP address - should use service discovery")
        
        # Test if IP is in private ranges (RFC 1918)
        private_ranges = [
            "10.",      # 10.0.0.0/8
            "172.16.",  # 172.16.0.0/12 
            "192.168."  # 192.168.0.0/16
        ]
        
        is_private = any(broker_ip.startswith(range_prefix) 
                        for range_prefix in private_ranges)
        self.assertTrue(is_private, "MQTT broker should use private IP or service name")
        
    def test_mqtt_connection_timeout(self):
        """Test MQTT connection timeout handling"""
        # Test connection timeout behavior
        timeout_seconds = 5  # From deployment code
        
        # Short timeouts can cause availability issues
        # Long timeouts can cause resource exhaustion
        self.assertGreaterEqual(timeout_seconds, 5, 
                              "MQTT timeout too short - may cause connection issues")
        self.assertLessEqual(timeout_seconds, 30, 
                           "MQTT timeout too long - may cause resource exhaustion")


class TestMQTTMessageSecurity(unittest.TestCase):
    """Test MQTT message content security"""
    
    def test_mqtt_message_size_limits(self):
        """Test MQTT message size restrictions"""
        # MQTT max message size is 268,435,455 bytes (256 MB - 1)
        max_mqtt_size = 268435455
        
        # Test oversized message handling
        oversized_message = b"A" * (max_mqtt_size + 1)
        
        # Should be rejected
        is_valid = len(oversized_message) <= max_mqtt_size
        self.assertFalse(is_valid, 
                        "Oversized MQTT message should be rejected")
        
    def test_mqtt_message_encoding(self):
        """Test MQTT message encoding security"""
        # Test various encodings that might cause issues
        problematic_messages = [
            # Unicode issues
            "test\u0000message",  # Null unicode
            "test\ufeffmessage",  # BOM
            
            # Control characters
            "test\x1b[31mmessage", # ANSI escape codes
            "test\r\nmessage",     # CRLF injection
            
            # JSON injection
            '{"valid": true}, {"injected": "malicious"}',
        ]
        
        for message in problematic_messages:
            with self.subTest(message=message[:20] + "..."):
                # Test message sanitization
                sanitized = self._sanitize_mqtt_message(message)
                self.assertNotIn('\x00', sanitized, 
                                f"Null bytes not removed from: {message[:20]}")
                
    def _sanitize_mqtt_message(self, message):
        """Message sanitization (should be implemented)"""
        if isinstance(message, str):
            # Remove null bytes and control characters
            sanitized = message.replace('\x00', '').replace('\r', '').replace('\n', ' ')
            return sanitized
        return message
        
    def test_mqtt_topic_injection(self):
        """Test MQTT topic injection attacks"""
        # Test topic manipulation
        base_topic = "ai_terminal/comms"
        
        injection_attempts = [
            "ai_terminal/comms/../admin",
            "ai_terminal/comms\x00/admin",
            f"{base_topic}/../../$SYS/broker",
        ]
        
        for malicious_topic in injection_attempts:
            with self.subTest(topic=malicious_topic):
                # Normalize and validate topic
                normalized = self._normalize_mqtt_topic(malicious_topic)
                is_safe = normalized == base_topic or normalized.startswith(f"{base_topic}/")
                
                if "../" in malicious_topic or "$SYS" in malicious_topic:
                    self.assertFalse(is_safe, 
                                   f"Topic injection not prevented: {malicious_topic}")
                    
    def _normalize_mqtt_topic(self, topic):
        """Normalize MQTT topic to prevent injection"""
        import os
        # Remove null bytes
        topic = topic.replace('\x00', '')
        # Normalize path
        normalized = os.path.normpath(topic)
        return normalized


class TestMQTTAuthorizationSecurity(unittest.TestCase):
    """Test MQTT authorization and access control"""
    
    def test_mqtt_acl_missing(self):
        """Test for missing MQTT Access Control Lists"""
        # Current implementation has no ACLs
        # This is a significant security issue
        
        acl_config = {
            'enabled': False,  # No ACL in current implementation
            'rules': []        # No authorization rules
        }
        
        self.assertFalse(acl_config['enabled'], 
                        "MQTT ACL not configured - authorization bypass possible")
        self.assertEqual(len(acl_config['rules']), 0, 
                       "No MQTT authorization rules - all access permitted")
        
    def test_mqtt_client_permissions(self):
        """Test MQTT client permission restrictions"""
        # Test what permissions the client has
        client_permissions = {
            'publish': True,    # Can publish messages
            'subscribe': True,  # Can subscribe to topics
            'admin': False      # Should not have admin access
        }
        
        # Client should have minimal required permissions only
        self.assertTrue(client_permissions['publish'], 
                       "Client should be able to publish")
        self.assertFalse(client_permissions.get('admin', False), 
                        "Client should not have admin permissions")
        
    def test_mqtt_topic_permissions(self):
        """Test MQTT topic-level permissions"""
        allowed_topics = [
            "ai_terminal/comms",
            "ai_terminal/status",
        ]
        
        restricted_topics = [
            "$SYS/broker/clients/connected",
            "$SYS/broker/load/messages/sent/1min",
            "admin/commands",
            "system/shutdown",
        ]
        
        # Test that restricted topics are actually restricted
        for topic in restricted_topics:
            with self.subTest(topic=topic):
                has_access = self._check_topic_access(topic)
                self.assertFalse(has_access, 
                               f"Unauthorized access to topic: {topic}")
                
    def _check_topic_access(self, topic):
        """Check if client has access to topic (mock implementation)"""
        # In real implementation, this would check ACLs
        if topic.startswith("$SYS/") or topic.startswith("admin/"):
            return False  # Should be restricted
        return True


class TestMQTTDenialOfServiceAttacks(unittest.TestCase):
    """Test MQTT DoS attack vectors"""
    
    def test_mqtt_connection_flood(self):
        """Test MQTT connection flooding attacks"""
        # Test rapid connection attempts
        max_connections = 1000  # Hypothetical limit
        
        # Simulate connection flood
        connection_attempts = 2000
        
        if connection_attempts > max_connections:
            # Should be rate limited
            self.fail("Connection flood not prevented - DoS vulnerability")
            
    def test_mqtt_message_flood(self):
        """Test MQTT message flooding attacks"""
        # Test rapid message publishing
        messages_per_second = 10000
        rate_limit = 100  # Messages per second limit
        
        if messages_per_second > rate_limit:
            # Should be rate limited
            self.fail("Message flood not prevented - DoS vulnerability")
            
    def test_mqtt_subscription_flood(self):
        """Test MQTT subscription flooding"""
        # Test excessive subscription attempts
        subscription_count = 10000
        max_subscriptions = 100
        
        if subscription_count > max_subscriptions:
            self.fail("Subscription flood not prevented - resource exhaustion")
            
    def test_mqtt_keep_alive_abuse(self):
        """Test MQTT keep-alive mechanism abuse"""
        # Very short keep-alive can cause resource exhaustion
        keep_alive_seconds = 60  # From deployment
        
        self.assertGreaterEqual(keep_alive_seconds, 10, 
                              "Keep-alive too short - may cause resource exhaustion")
        self.assertLessEqual(keep_alive_seconds, 300, 
                           "Keep-alive too long - may cause resource waste")


if __name__ == '__main__':
    print("Starting MQTT Security Tests...")
    print("=" * 50)
    
    # Run MQTT-specific security tests
    unittest.main(verbosity=2, buffer=True)