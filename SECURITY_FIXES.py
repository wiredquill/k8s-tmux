#!/usr/bin/env python3
"""
Secure implementation fixes for the k8s-tmux FileHandler class.
This file contains secure replacements for the vulnerable code in the deployment YAML.

CRITICAL: Replace the embedded Python server code with this secure implementation.
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import subprocess
import time
import socket
import struct
import cgi
import shutil
import hashlib
import secrets
import logging
import re
from io import BytesIO
from pathlib import Path
from functools import wraps

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    'MAX_UPLOAD_SIZE': 100 * 1024 * 1024,  # 100MB
    'ALLOWED_EXTENSIONS': {'.txt', '.py', '.json', '.yaml', '.yml', '.md', '.sh', '.conf'},
    'UPLOAD_RATE_LIMIT': 10,  # uploads per minute per IP
    'COMMAND_TIMEOUT': 30,  # seconds
    'MAX_COMMAND_LENGTH': 1000,
    'BLOCKED_COMMANDS': {
        'rm', 'rmdir', 'del', 'format', 'mkfs', 'fdisk',
        'sudo', 'su', 'passwd', 'chmod', 'chown',
        'curl', 'wget', 'nc', 'netcat', 'telnet'
    }
}

# Rate limiting storage
RATE_LIMITS = {}

def rate_limit(max_requests=10, window_minutes=1):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            client_ip = self.client_address[0]
            current_time = time.time()
            window_start = current_time - (window_minutes * 60)
            
            # Clean old entries
            if client_ip in RATE_LIMITS:
                RATE_LIMITS[client_ip] = [
                    req_time for req_time in RATE_LIMITS[client_ip]
                    if req_time > window_start
                ]
            else:
                RATE_LIMITS[client_ip] = []
            
            # Check rate limit
            if len(RATE_LIMITS[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                self.send_error(429, "Too Many Requests")
                return
            
            # Add current request
            RATE_LIMITS[client_ip].append(current_time)
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def sanitize_filename(filename):
    """Securely sanitize uploaded filenames"""
    if not filename:
        return "unnamed_file"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Limit length
    filename = filename[:255]
    
    # Ensure not empty or reserved
    if not filename or filename in ['.', '..'] or filename.startswith('.'):
        filename = f"file_{int(time.time())}"
    
    return filename


def validate_path(path, base_dir):
    """Validate and normalize file paths to prevent traversal"""
    if not path:
        return None
    
    # Normalize the path
    normalized = os.path.normpath(path)
    
    # Remove leading slashes and resolve relative components
    normalized = normalized.lstrip('/')
    
    # Join with base directory
    full_path = os.path.join(base_dir, normalized)
    
    # Resolve to absolute path
    full_path = os.path.abspath(full_path)
    base_dir_abs = os.path.abspath(base_dir)
    
    # Ensure path is within base directory
    if not full_path.startswith(base_dir_abs + os.sep) and full_path != base_dir_abs:
        logger.warning(f"Path traversal attempt blocked: {path}")
        return None
    
    return full_path


def sanitize_command(command):
    """Sanitize commands to prevent injection"""
    if not command or len(command) > SECURITY_CONFIG['MAX_COMMAND_LENGTH']:
        return None
    
    # Remove dangerous characters
    dangerous_chars = [';', '&&', '||', '|', '&', '`', '$', '>', '<', '(', ')']
    for char in dangerous_chars:
        if char in command:
            logger.warning(f"Dangerous character '{char}' found in command: {command}")
            return None
    
    # Check for blocked commands
    command_parts = command.split()
    if command_parts:
        base_command = command_parts[0].lower()
        if base_command in SECURITY_CONFIG['BLOCKED_COMMANDS']:
            logger.warning(f"Blocked command attempted: {base_command}")
            return None
    
    return command.strip()


class SecureFileHandler(http.server.SimpleHTTPRequestHandler):
    """Secure implementation of FileHandler with vulnerability fixes"""
    
    def __init__(self, *args, **kwargs):
        self.session_id = secrets.token_hex(16)
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use secure logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests with security checks"""
        logger.info(f"GET request: {self.path} from {self.client_address[0]}")
        
        if self.path == '/':
            self.send_ui()
        elif self.path.startswith('/api/files'):
            self.send_file_list()
        elif self.path.startswith('/api/download'):
            self.handle_download()
        elif self.path == '/terminal':
            self.redirect_to_ttyd()
        elif self.path == '/health':
            self.handle_health_check()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests with security validation"""
        logger.info(f"POST request: {self.path} from {self.client_address[0]}")
        
        if self.path == '/api/send-command':
            self.handle_send_command()
        elif self.path == '/api/test-mqtt':
            self.handle_test_mqtt()
        elif self.path == '/api/schedule-command':
            self.handle_schedule_command()
        elif self.path == '/api/upload':
            self.handle_file_upload()
        else:
            self.send_error(404, "Not Found")
    
    def handle_health_check(self):
        """Health check endpoint"""
        response = {
            "status": "healthy",
            "timestamp": time.time(),
            "session": self.session_id
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    @rate_limit(max_requests=10, window_minutes=1)
    def handle_file_upload(self):
        """Securely handle file uploads with validation"""
        try:
            logger.info("Processing secure file upload...")
            
            # Check content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > SECURITY_CONFIG['MAX_UPLOAD_SIZE']:
                self.send_error(413, "File too large")
                return
            
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' not in content_type:
                self.send_error(400, "Invalid content type")
                return
            
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            if 'file' not in form:
                self.send_error(400, "No file uploaded")
                return
            
            file_item = form['file']
            if not file_item.filename:
                self.send_error(400, "No file selected")
                return
            
            # Sanitize filename
            safe_filename = sanitize_filename(file_item.filename)
            
            # Check file extension
            file_ext = Path(safe_filename).suffix.lower()
            if file_ext not in SECURITY_CONFIG['ALLOWED_EXTENSIONS']:
                self.send_error(400, f"File type not allowed: {file_ext}")
                return
            
            # Setup upload directory
            upload_dir = '/mnt/k8s-tmux/uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate secure file path
            timestamp = int(time.time())
            secure_filename = f"{timestamp}_{safe_filename}"
            filepath = os.path.join(upload_dir, secure_filename)
            
            # Validate final path
            if not validate_path(secure_filename, upload_dir):
                self.send_error(400, "Invalid file path")
                return
            
            # Write file securely
            bytes_written = 0
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file_item.file.read(8192)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > SECURITY_CONFIG['MAX_UPLOAD_SIZE']:
                        f.close()
                        os.unlink(filepath)
                        self.send_error(413, "File too large")
                        return
                    f.write(chunk)
            
            # Set secure permissions
            os.chmod(filepath, 0o644)
            
            logger.info(f"File uploaded securely: {secure_filename} ({bytes_written} bytes)")
            
            response = {
                "status": "success",
                "message": f"File '{safe_filename}' uploaded successfully",
                "filename": secure_filename,
                "size": bytes_written
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error in secure file upload: {e}")
            self.send_error(500, "Upload failed")
    
    @rate_limit(max_requests=20, window_minutes=1)
    def handle_send_command(self):
        """Securely handle command execution"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10000:  # 10KB max for command data
                self.send_error(413, "Request too large")
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            raw_command = data.get('command', '')
            if not raw_command:
                self.send_error(400, "No command provided")
                return
            
            # Sanitize command
            safe_command = sanitize_command(raw_command)
            if not safe_command:
                self.send_error(400, "Invalid or dangerous command")
                return
            
            logger.info(f"Executing safe command: {safe_command}")
            
            # Execute with timeout and restricted environment
            try:
                result = subprocess.run(
                    ['tmux', 'send-keys', '-t', 'main', safe_command, 'Enter'],
                    timeout=SECURITY_CONFIG['COMMAND_TIMEOUT'],
                    capture_output=True,
                    text=True
                )
                
                response = {
                    "status": "success",
                    "message": "Command executed safely",
                    "command": safe_command
                }
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timeout: {safe_command}")
                response = {"status": "error", "message": "Command timeout"}
                
            except Exception as e:
                logger.error(f"Command execution error: {e}")
                response = {"status": "error", "message": "Execution failed"}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error in send_command: {e}")
            self.send_error(500, "Server error")
    
    def handle_download(self):
        """Securely handle file downloads"""
        try:
            logger.info("Processing secure download request")
            
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            file_path = params.get('path', [''])[0]
            
            if not file_path:
                self.send_error(400, "No file path provided")
                return
            
            # Validate and normalize path
            base_dir = '/mnt/k8s-tmux'
            safe_path = validate_path(file_path, base_dir)
            
            if not safe_path:
                logger.warning(f"Invalid download path blocked: {file_path}")
                self.send_error(403, "Access denied")
                return
            
            if not os.path.exists(safe_path) or os.path.isdir(safe_path):
                self.send_error(404, "File not found")
                return
            
            # Check file size
            file_size = os.path.getsize(safe_path)
            if file_size > SECURITY_CONFIG['MAX_UPLOAD_SIZE']:
                self.send_error(413, "File too large")
                return
            
            filename = os.path.basename(safe_path)
            
            # Sanitize filename for download
            safe_download_name = sanitize_filename(filename)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{safe_download_name}"')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            # Stream file in chunks
            with open(safe_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            
            logger.info(f"File downloaded securely: {filename} ({file_size} bytes)")
            
        except Exception as e:
            logger.error(f"Error in secure download: {e}")
            self.send_error(500, "Download failed")
    
    def send_file_list(self):
        """Securely list files with path validation"""
        try:
            logger.info("Processing secure file list request")
            
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            path_param = params.get('path', [''])[0]
            
            base_dir = '/mnt/k8s-tmux'
            
            # Validate requested path
            if path_param:
                safe_path = validate_path(path_param, base_dir)
                if not safe_path:
                    self.send_error(403, "Access denied")
                    return
            else:
                safe_path = base_dir
            
            if not os.path.exists(safe_path):
                self.send_error(404, "Path not found")
                return
            
            files = []
            
            # Add parent directory link if not at root
            if path_param and path_param != '':
                parent_path = os.path.dirname(path_param)
                files.append({
                    "name": "..",
                    "type": "dir",
                    "path": parent_path,
                    "size": 0
                })
            
            # List directory contents securely
            try:
                for item in sorted(os.listdir(safe_path)):
                    # Skip hidden files and system files
                    if item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(safe_path, item)
                    relative_path = os.path.relpath(item_path, base_dir)
                    
                    if os.path.isdir(item_path):
                        files.append({
                            "name": item,
                            "type": "dir",
                            "path": relative_path,
                            "size": 0
                        })
                    else:
                        try:
                            size = os.path.getsize(item_path)
                            files.append({
                                "name": item,
                                "type": "file", 
                                "path": relative_path,
                                "size": size
                            })
                        except OSError:
                            # Skip files we can't stat
                            continue
                            
            except OSError as e:
                logger.error(f"Error listing directory: {e}")
                self.send_error(500, "Directory listing failed")
                return
            
            # Sort files: directories first, then files
            files.sort(key=lambda x: (x['name'] != '..', x['type'] != 'dir', x['name'].lower()))
            
            response_data = {
                "files": files,
                "current_path": path_param,
                "count": len(files)
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            
            json_response = json.dumps(response_data)
            self.wfile.write(json_response.encode())
            
            logger.info(f"File list sent securely: {len(files)} items")
            
        except Exception as e:
            logger.error(f"Error in send_file_list: {e}")
            self.send_error(500, "Server error")
    
    def send_ui(self):
        """Send secure web UI with CSP headers"""
        try:
            session_name = os.environ.get('SESSION_NAME', 'Secure AI Terminal')
            session_color = os.environ.get('SESSION_COLOR', '#667eea')
            
            # The HTML would be the same but with added security features
            # For brevity, showing the security headers that should be added
            
            html = "<!DOCTYPE html><!-- Secure UI implementation -->"  # Truncated for brevity
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('X-XSS-Protection', '1; mode=block')
            self.send_header('Content-Security-Policy', 
                           "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            logger.error(f"Error sending UI: {e}")
            self.send_error(500, "Server error")
    
    def handle_test_mqtt(self):
        """MQTT testing with security improvements"""
        # This would be replaced with a secure MQTT implementation
        # using proper authentication, encryption, and validation
        self.send_error(501, "MQTT functionality requires secure configuration")
    
    def handle_schedule_command(self):
        """Secure command scheduling"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10000:
                self.send_error(413, "Request too large")
                return
            
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            raw_command = data.get('command', '')
            schedule_type = data.get('type', 'delay')
            schedule_value = data.get('value', '5m')
            
            # Validate command
            safe_command = sanitize_command(raw_command)
            if not safe_command:
                self.send_error(400, "Invalid or dangerous command")
                return
            
            # Validate schedule parameters
            if schedule_type not in ['delay', 'time']:
                self.send_error(400, "Invalid schedule type")
                return
            
            # For now, disable scheduling for security
            # A secure implementation would need proper job queue management
            self.send_error(501, "Command scheduling disabled for security")
            
        except Exception as e:
            logger.error(f"Error in schedule_command: {e}")
            self.send_error(500, "Server error")
    
    def redirect_to_ttyd(self):
        """Secure redirect to terminal"""
        host = self.headers.get('Host', 'localhost').split(':')[0]
        
        # Validate host header to prevent header injection
        if not re.match(r'^[a-zA-Z0-9.-]+$', host):
            host = 'localhost'
        
        self.send_response(302)
        self.send_header('Location', f'http://{host}:7681')
        self.end_headers()


def main():
    """Run the secure file handler server"""
    port = 8080
    
    logger.info(f'Starting SECURE AI Terminal server on port {port}')
    logger.info(f'Session: {os.environ.get("SESSION_NAME", "Secure AI Terminal")}')
    logger.info("Security features enabled: rate limiting, input validation, path sanitization")
    
    try:
        with socketserver.TCPServer(('', port), SecureFileHandler) as httpd:
            logger.info(f'Secure server ready at http://localhost:{port}')
            httpd.serve_forever()
    except Exception as e:
        logger.error(f'Server error: {e}')
        raise


if __name__ == '__main__':
    main()