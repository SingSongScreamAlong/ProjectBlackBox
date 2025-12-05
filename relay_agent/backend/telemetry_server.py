#!/usr/bin/env python3
"""
BlackBox Relay Agent - Backend Telemetry Server

This module implements a WebSocket and UDP server for receiving telemetry data
from BlackBox Relay Agents and storing/processing it.
"""

import os
import sys
import json
import time
import logging
import asyncio
import signal
import zlib
import websockets
import redis
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telemetry_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TelemetryServer")

# Default configuration
DEFAULT_CONFIG = {
    "websocket_host": "0.0.0.0",
    "websocket_port": 8765,
    "udp_host": "0.0.0.0",
    "udp_port": 10000,
    "http_host": "0.0.0.0",
    "http_port": 8000,
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    "redis_password": None,
    "api_keys": ["test_api_key"],  # For testing only
    "data_retention_days": 30,
    "max_clients": 100,
    "compress_storage": True
}


class TelemetryServer:
    """
    Server for receiving and processing telemetry data from BlackBox Relay Agents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TelemetryServer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.running = False
        self.clients = {}
        self.sessions = {}
        self.redis = None
        self.websocket_server = None
        self.udp_server = None
        self.http_app = None
        self.http_runner = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        logger.info("TelemetryServer initialized")
    
    async def start(self) -> None:
        """Start the TelemetryServer."""
        if self.running:
            logger.warning("Server is already running")
            return
        
        self.running = True
        logger.info("Starting TelemetryServer")
        
        # Connect to Redis
        try:
            self.redis = redis.Redis(
                host=self.config["redis_host"],
                port=self.config["redis_port"],
                db=self.config["redis_db"],
                password=self.config["redis_password"]
            )
            # Use synchronous ping instead of async
            self.redis.ping()
            logger.info(f"Connected to Redis at {self.config['redis_host']}:{self.config['redis_port']}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Proceeding without Redis.")
            self.redis = None
        
        # Start WebSocket server
        self.websocket_task = asyncio.create_task(self.start_websocket_server())
        logger.info(f"WebSocket server task created, will listen on {self.config['websocket_host']}:{self.config['websocket_port']}")
        
        # Start UDP server
        self.udp_task = asyncio.create_task(self.start_udp_server())
        
        # Start HTTP server
        self.http_task = asyncio.create_task(self.start_http_server())
        
        try:
            # Wait for all servers to start
            await asyncio.gather(self.websocket_task, self.udp_task, self.http_task)
            logger.info("All server tasks started successfully")
        except Exception as e:
            logger.error(f"Error starting server tasks: {e}")
        
        logger.info("TelemetryServer started")
    
    async def stop(self) -> None:
        """Stop the TelemetryServer."""
        if not self.running:
            return
        
        logger.info("Stopping TelemetryServer")
        self.running = False
        
        # Close all client connections
        for client_id, client in self.clients.items():
            if 'websocket' in client:
                try:
                    await client['websocket'].close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket for client {client_id}: {e}")
        
        # Stop WebSocket server
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # Stop UDP server
        if self.udp_server:
            self.udp_server.close()
        
        # Stop HTTP server
        if self.http_runner:
            await self.http_runner.cleanup()
        
        # Close Redis connection
        if self.redis:
            await self.redis.close()
        
        logger.info("TelemetryServer stopped")
    
    async def start_websocket_server(self) -> None:
        """Start the WebSocket server."""
        try:
            host = self.config["websocket_host"]
            port = self.config["websocket_port"]
            
            self.websocket_server = await websockets.serve(
                self.handle_websocket,
                host,
                port
            )
            
            logger.info(f"WebSocket server started on ws://{host}:{port}")
            
            # Keep the server running
            await self.websocket_server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
    
    async def start_udp_server(self) -> None:
        """Start the UDP server."""
        try:
            host = self.config["udp_host"]
            port = self.config["udp_port"]
            
            # Create UDP endpoint
            loop = asyncio.get_running_loop()
            
            # Create datagram endpoint
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: UDPServerProtocol(self),
                local_addr=(host, port)
            )
            
            self.udp_server = transport
            
            logger.info(f"UDP server started on {host}:{port}")
            
            # Keep the server running until stopped
            while self.running:
                await asyncio.sleep(1)
                
            # Close the transport when stopped
            transport.close()
            
        except Exception as e:
            logger.error(f"Error starting UDP server: {e}")
    
    async def start_http_server(self) -> None:
        """Start the HTTP server for API endpoints."""
        try:
            host = self.config["http_host"]
            port = self.config["http_port"]
            
            # Create HTTP app
            app = web.Application()
            
            # Add routes
            app.add_routes([
                web.get('/api/v1/health', self.handle_health),
                web.get('/api/v1/sessions', self.handle_sessions),
                web.get('/api/v1/sessions/{session_id}', self.handle_session),
                web.get('/api/v1/sessions/{session_id}/telemetry', self.handle_session_telemetry),
                web.get('/api/v1/sessions/{session_id}/events', self.handle_session_events)
            ])
            
            # Start the server
            self.http_runner = web.AppRunner(app)
            await self.http_runner.setup()
            site = web.TCPSite(self.http_runner, host, port)
            await site.start()
            
            logger.info(f"HTTP server started on http://{host}:{port}")
            
            # Keep the server running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting HTTP server: {e}")
    
    async def handle_websocket(self, websocket) -> None:
        """
        Handle WebSocket connections.
        
        Args:
            websocket: WebSocket connection
        """
        client_id = str(uuid.uuid4())
        client = {
            'id': client_id,
            'websocket': websocket,
            'connected_at': time.time(),
            'session_id': None,
            'api_key': None,
            'authenticated': False,
            'last_message_time': time.time()
        }
        
        self.clients[client_id] = client
        logger.info(f"New WebSocket connection: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    # Check if message is binary (compressed)
                    if isinstance(message, bytes):
                        try:
                            # Decompress message
                            message = zlib.decompress(message).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error decompressing message: {e}")
                            continue
                    
                    # Parse message
                    data = json.loads(message)
                    
                    # Update last message time
                    client['last_message_time'] = time.time()
                    
                    # Process message
                    await self.process_message(client, data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message from client {client_id}")
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            # Clean up client
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def process_message(self, client: Dict[str, Any], message: Dict[str, Any]) -> None:
        """
        Process a message from a client.
        
        Args:
            client: Client information
            message: Message data
        """
        # Check message type
        message_type = message.get('type')
        
        if not message_type:
            logger.warning(f"Message from client {client['id']} has no type")
            return
        
        # Check authentication
        if not client['authenticated']:
            # Allow session_info messages for initial authentication
            if message_type == 'session_info':
                # Check API key
                api_key = message.get('api_key')
                if api_key and api_key in self.config['api_keys']:
                    client['authenticated'] = True
                    client['api_key'] = api_key
                    logger.info(f"Client {client['id']} authenticated")
                else:
                    logger.warning(f"Client {client['id']} failed authentication")
                    return
            else:
                logger.warning(f"Unauthenticated message from client {client['id']}")
                return
        
        # Process message based on type
        if message_type == 'session_info':
            await self.handle_session_info(client, message)
        elif message_type == 'telemetry':
            await self.handle_telemetry(client, message)
        else:
            logger.warning(f"Unknown message type from client {client['id']}: {message_type}")
    
    async def handle_session_info(self, client: Dict[str, Any], message: Dict[str, Any]) -> None:
        """
        Handle session info message.
        
        Args:
            client: Client information
            message: Message data
        """
        session_id = message.get('session_id')
        if not session_id:
            logger.warning(f"Session info message from client {client['id']} has no session_id")
            return
        
        # Update client session
        client['session_id'] = session_id
        
        # Store session info
        session_data = {
            'id': session_id,
            'created_at': time.time(),
            'client_id': client['id'],
            'info': message.get('data', {}),
            'last_update': time.time()
        }
        
        self.sessions[session_id] = session_data
        
        # Store in Redis if available
        if self.redis:
            try:
                await self.redis.set(
                    f"session:{session_id}",
                    json.dumps(session_data),
                    ex=self.config['data_retention_days'] * 86400  # TTL in seconds
                )
            except Exception as e:
                logger.error(f"Error storing session in Redis: {e}")
        
        logger.info(f"Received session info for session {session_id}")
    
    async def handle_telemetry(self, client: Dict[str, Any], message: Dict[str, Any]) -> None:
        """
        Handle telemetry message.
        
        Args:
            client: Client information
            message: Message data
        """
        session_id = message.get('session_id')
        if not session_id:
            logger.warning(f"Telemetry message from client {client['id']} has no session_id")
            return
        
        # Check if session exists
        if session_id not in self.sessions and not self.redis:
            logger.warning(f"Telemetry for unknown session {session_id}")
            return
        
        # Get timestamp
        timestamp = message.get('timestamp', time.time())
        
        # Store telemetry data
        telemetry_data = {
            'session_id': session_id,
            'timestamp': timestamp,
            'data': message.get('data', {}),
            'events': message.get('events', [])
        }
        
        # Store in Redis if available
        if self.redis:
            try:
                # Store telemetry in a time series
                telemetry_key = f"telemetry:{session_id}:{int(timestamp * 1000)}"
                
                # Compress if configured
                if self.config['compress_storage']:
                    await self.redis.set(
                        telemetry_key,
                        zlib.compress(json.dumps(telemetry_data).encode('utf-8')),
                        ex=self.config['data_retention_days'] * 86400  # TTL in seconds
                    )
                else:
                    await self.redis.set(
                        telemetry_key,
                        json.dumps(telemetry_data),
                        ex=self.config['data_retention_days'] * 86400  # TTL in seconds
                    )
                
                # Add to session timeline
                await self.redis.zadd(
                    f"timeline:{session_id}",
                    {telemetry_key: timestamp}
                )
                
                # Set expiration on timeline
                await self.redis.expire(
                    f"timeline:{session_id}",
                    self.config['data_retention_days'] * 86400  # TTL in seconds
                )
                
                # Store events if any
                for event in message.get('events', []):
                    event_data = {
                        'session_id': session_id,
                        'timestamp': timestamp,
                        'event': event,
                        'telemetry': message.get('data', {})
                    }
                    
                    event_key = f"event:{session_id}:{event}:{int(timestamp * 1000)}"
                    
                    await self.redis.set(
                        event_key,
                        json.dumps(event_data),
                        ex=self.config['data_retention_days'] * 86400  # TTL in seconds
                    )
                    
                    # Add to event timeline
                    await self.redis.zadd(
                        f"events:{session_id}",
                        {event_key: timestamp}
                    )
                    
                    # Set expiration on event timeline
                    await self.redis.expire(
                        f"events:{session_id}",
                        self.config['data_retention_days'] * 86400  # TTL in seconds
                    )
            
            except Exception as e:
                logger.error(f"Error storing telemetry in Redis: {e}")
        
        # Log events if any
        if message.get('events'):
            logger.info(f"Received telemetry with events {message['events']} for session {session_id}")
        else:
            # Log telemetry receipt periodically to avoid flooding logs
            if int(timestamp) % 10 == 0:  # Log every ~10 seconds
                logger.debug(f"Received telemetry for session {session_id}")
    
    async def handle_health(self, request) -> web.Response:
        """
        Handle health check endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            web.Response: HTTP response
        """
        # Check Redis connection if available
        redis_status = "connected" if self.redis else "disconnected"
        
        response_data = {
            "status": "ok",
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            "clients": len(self.clients),
            "sessions": len(self.sessions),
            "redis": redis_status
        }
        
        return web.json_response(response_data)
    
    async def handle_sessions(self, request) -> web.Response:
        """
        Handle sessions endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            web.Response: HTTP response
        """
        # Check API key
        api_key = request.headers.get('Authorization')
        if not api_key or api_key.replace('Bearer ', '') not in self.config['api_keys']:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        # Get sessions
        sessions = []
        for session_id, session in self.sessions.items():
            sessions.append({
                "id": session_id,
                "created_at": session['created_at'],
                "last_update": session['last_update'],
                "info": session['info']
            })
        
        return web.json_response({"sessions": sessions})
    
    async def handle_session(self, request) -> web.Response:
        """
        Handle session endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            web.Response: HTTP response
        """
        # Check API key
        api_key = request.headers.get('Authorization')
        if not api_key or api_key.replace('Bearer ', '') not in self.config['api_keys']:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        # Get session ID
        session_id = request.match_info['session_id']
        
        # Check if session exists
        if session_id not in self.sessions:
            return web.json_response({"error": "Session not found"}, status=404)
        
        # Get session
        session = self.sessions[session_id]
        
        return web.json_response({
            "id": session_id,
            "created_at": session['created_at'],
            "last_update": session['last_update'],
            "info": session['info']
        })
    
    async def handle_session_telemetry(self, request) -> web.Response:
        """
        Handle session telemetry endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            web.Response: HTTP response
        """
        # Check API key
        api_key = request.headers.get('Authorization')
        if not api_key or api_key.replace('Bearer ', '') not in self.config['api_keys']:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        # Get session ID
        session_id = request.match_info['session_id']
        
        # Check if Redis is available
        if not self.redis:
            return web.json_response({"error": "Redis not available"}, status=503)
        
        # Get query parameters
        start = float(request.query.get('start', 0))
        end = float(request.query.get('end', time.time()))
        limit = int(request.query.get('limit', 100))
        
        # Get telemetry from Redis
        try:
            # Get timeline
            timeline_key = f"timeline:{session_id}"
            telemetry_keys = await self.redis.zrangebyscore(
                timeline_key,
                start,
                end,
                start=0,
                num=limit
            )
            
            telemetry = []
            for key in telemetry_keys:
                # Get telemetry data
                data = await self.redis.get(key)
                
                if data:
                    # Decompress if needed
                    if self.config['compress_storage']:
                        data = zlib.decompress(data)
                    
                    # Parse JSON
                    telemetry_data = json.loads(data)
                    telemetry.append(telemetry_data)
            
            return web.json_response({"telemetry": telemetry})
            
        except Exception as e:
            logger.error(f"Error retrieving telemetry: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def handle_session_events(self, request) -> web.Response:
        """
        Handle session events endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            web.Response: HTTP response
        """
        # Check API key
        api_key = request.headers.get('Authorization')
        if not api_key or api_key.replace('Bearer ', '') not in self.config['api_keys']:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        # Get session ID
        session_id = request.match_info['session_id']
        
        # Check if Redis is available
        if not self.redis:
            return web.json_response({"error": "Redis not available"}, status=503)
        
        # Get query parameters
        start = float(request.query.get('start', 0))
        end = float(request.query.get('end', time.time()))
        limit = int(request.query.get('limit', 100))
        event_type = request.query.get('type')
        
        # Get events from Redis
        try:
            # Get timeline
            events_key = f"events:{session_id}"
            event_keys = await self.redis.zrangebyscore(
                events_key,
                start,
                end,
                start=0,
                num=limit
            )
            
            events = []
            for key in event_keys:
                # Get event data
                data = await self.redis.get(key)
                
                if data:
                    # Parse JSON
                    event_data = json.loads(data)
                    
                    # Filter by event type if specified
                    if event_type and event_data.get('event') != event_type:
                        continue
                    
                    events.append(event_data)
            
            return web.json_response({"events": events})
            
        except Exception as e:
            logger.error(f"Error retrieving events: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    def handle_exit(self, signum, frame) -> None:
        """Handle exit signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down")
        
        # Create event loop if needed
        if not asyncio.get_event_loop().is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Stop the server
        asyncio.create_task(self.stop())


class UDPServerProtocol:
    """UDP Server Protocol for handling UDP telemetry data."""
    
    def __init__(self, server):
        """
        Initialize the UDP Server Protocol.
        
        Args:
            server: TelemetryServer instance
        """
        self.server = server
    
    def connection_made(self, transport):
        """
        Called when a connection is made.
        
        Args:
            transport: Transport instance
        """
        self.transport = transport
    
    def datagram_received(self, data, addr):
        """
        Called when a datagram is received.
        
        Args:
            data: Received data
            addr: Address of sender
        """
        try:
            # Check if data is compressed
            try:
                # Decompress data
                data = zlib.decompress(data)
            except Exception:
                # Not compressed, continue
                pass
            
            # Parse JSON
            message = json.loads(data.decode('utf-8'))
            
            # Create a client object for this UDP message
            client_id = f"udp:{addr[0]}:{addr[1]}"
            client = {
                'id': client_id,
                'addr': addr,
                'connected_at': time.time(),
                'session_id': None,
                'api_key': None,
                'authenticated': False,
                'last_message_time': time.time()
            }
            
            # Check authentication
            api_key = message.get('api_key')
            if api_key and api_key in self.server.config['api_keys']:
                client['authenticated'] = True
                client['api_key'] = api_key
            else:
                logger.warning(f"Unauthenticated UDP message from {addr}")
                return
            
            # Process message
            asyncio.create_task(self.server.process_message(client, message))
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from UDP client {addr}")
        except Exception as e:
            logger.error(f"Error processing UDP message from {addr}: {e}")


async def main():
    """Main entry point for the TelemetryServer."""
    # Create and start server
    server = TelemetryServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        await server.stop()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        await server.stop()


if __name__ == "__main__":
    # Set start time
    TelemetryServer.start_time = time.time()
    
    # Run the server
    asyncio.run(main())
