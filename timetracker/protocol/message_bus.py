"""
MessageBus for handling communication between frontend and backend.
"""
from typing import Dict, Callable, Any, Optional
import uuid
import logging
import json
from .generated_schema import BaseMessage, Request, Response
from .version import VERSION as PROTOCOL_VERSION

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Simple in-process message bus for communication between frontend and backend.
    """

    def __init__(self, protocol_version: str = PROTOCOL_VERSION):
        self._handlers: Dict[str, Callable] = {}  # Use message type string instead of enum
        self._message_counter = 0
        self._enable_debug_logging = False
        self._protocol_version = protocol_version
        
    def set_debug_logging(self, enable: bool):
        """Enable or disable debug logging of messages."""
        self._enable_debug_logging = enable
        if enable:
            logger.setLevel(logging.DEBUG)
            logger.info("Debug logging enabled for MessageBus")
            
    @property
    def protocol_version(self) -> str:
        """Get the protocol version being used."""
        return self._protocol_version
        
    @protocol_version.setter
    def protocol_version(self, version: str):
        """Set the protocol version to use."""
        self._protocol_version = version
        logger.info(f"MessageBus protocol version set to {version}")
            
    def register_handler(self, msg_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        logger.debug(f"Registering handler for message type: {msg_type}")
        self._handlers[msg_type] = handler
        
    def unregister_handler(self, msg_type: str):
        """Unregister a handler for a specific message type."""
        if msg_type in self._handlers:
            logger.debug(f"Unregistering handler for message type: {msg_type}")
            del self._handlers[msg_type]
            
    def send(self, message: BaseMessage, sender_protocol_version: Optional[str] = None) -> Optional[Response]:
        """
        Send a message to the appropriate handler.
        Returns a response if the message is a request.
        
        Args:
            message: The message to send
            sender_protocol_version: The protocol version of the sender, if different from the bus
        """
        self._message_counter += 1
        msg_id = self._message_counter
        
        # Handle protocol version differences if specified
        if sender_protocol_version and sender_protocol_version != self._protocol_version:
            try:
                logger.debug(
                    f"Translating message from protocol version {sender_protocol_version} "
                    f"to {self._protocol_version}"
                )
                
                # Get a dict representation of the message for translation
                if hasattr(message, "model_dump"):
                    # For Pydantic v2
                    message_dict = message.model_dump()
                else:
                    # For Pydantic v1 or plain dict
                    message_dict = message.dict() if hasattr(message, "dict") else dict(message)
                
                # Translate the message
                translated_dict = translate_message(
                    message_dict,
                    sender_protocol_version,
                    self._protocol_version
                )
                
                # Convert back to the appropriate message type
                message_type = type(message)
                message = message_type(**translated_dict)
                
                logger.debug("Message translation successful")
            except Exception as e:
                logger.error(f"Error translating message between protocol versions: {e}")
                if isinstance(message, Request):
                    error_response = Response(
                        msg_type="ERROR",
                        msg_id=str(uuid.uuid4()),
                        request_id=message.msg_id,
                        success=False,
                        error_message=f"Protocol version translation error: {e}"
                    )
                    return error_response
        
        # Log the message being sent
        if self._enable_debug_logging:
            self._log_message("SEND", msg_id, message)
            
        if message.msg_type not in self._handlers:
            logger.error(f"No handler registered for message type: {message.msg_type}")
            if isinstance(message, Request):
                error_response = Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=message.msg_id,
                    success=False,
                    error_message=f"No handler registered for message type: {message.msg_type}"
                )
                
                if self._enable_debug_logging:
                    self._log_message("RESPOND", msg_id, error_response, is_error=True)
                    
                return error_response
            return None
            
        logger.debug(f"Handling message of type: {message.msg_type}")
        handler = self._handlers[message.msg_type]
        
        try:
            result = handler(message)
            
            # Handle protocol version differences for the response
            if sender_protocol_version and sender_protocol_version != self._protocol_version and result:
                try:
                    logger.debug(
                        f"Translating response from protocol version {self._protocol_version} "
                        f"to {sender_protocol_version}"
                    )
                    
                    # Get a dict representation of the result
                    if hasattr(result, "model_dump"):
                        result_dict = result.model_dump()
                    else:
                        result_dict = result.dict() if hasattr(result, "dict") else dict(result)
                    
                    # Translate the result
                    translated_dict = translate_message(
                        result_dict,
                        self._protocol_version,
                        sender_protocol_version
                    )
                    
                    # Convert back to the appropriate result type
                    result_type = type(result)
                    result = result_type(**translated_dict)
                    
                    logger.debug("Response translation successful")
                except Exception as e:
                    logger.error(f"Error translating response between protocol versions: {e}")
                    if isinstance(message, Request):
                        error_response = Response(
                            msg_type="ERROR",
                            msg_id=str(uuid.uuid4()),
                            request_id=message.msg_id,
                            success=False,
                            error_message=f"Protocol version translation error for response: {e}"
                        )
                        return error_response
            
            # Log the response
            if self._enable_debug_logging and result:
                if hasattr(result, 'success') and not result.success:
                    self._log_message("RESPOND", msg_id, result, is_error=True)
                else:
                    self._log_message("RESPOND", msg_id, result)
                
            return result
        except Exception as e:
            logger.exception(f"Error handling message of type {message.msg_type}: {e}")
            if isinstance(message, Request):
                error_response = Response(
                    msg_type="ERROR",
                    msg_id=str(uuid.uuid4()),
                    request_id=message.msg_id,
                    success=False,
                    error_message=str(e)
                )
                
                if self._enable_debug_logging:
                    self._log_message("RESPOND", msg_id, error_response, is_error=True)
                    
                return error_response
            return None
            
    def _log_message(self, direction: str, msg_id: int, message: Any, is_error: bool = False):
        """
        Log message details in a structured format.
        
        Args:
            direction: 'SEND' or 'RESPOND' to indicate message direction
            msg_id: Message counter ID for correlating requests and responses
            message: The message object being logged
            is_error: Whether the message is an error response
        """
        try:
            # Extract message type
            msg_type = message.msg_type
            
            # Extract key fields from message
            msg_info = {
                "msg_id": message.msg_id,
                "msg_type": msg_type
            }
            
            # Add request_id for responses
            if hasattr(message, "request_id"):
                msg_info["request_id"] = message.request_id
                
            # Add success status for responses
            if hasattr(message, "success"):
                msg_info["success"] = message.success
                
            # Add payload summary (limited to keys to avoid large logs)
            if hasattr(message, "payload"):
                payload_data = message.payload
                if isinstance(payload_data, dict):
                    msg_info["payload_keys"] = list(payload_data.keys())
                    
                    # For certain message types, include more payload details
                    if len(payload_data) < 5:  # Only log small payloads in detail
                        msg_info["payload"] = payload_data
            
            # Add error message if applicable
            if hasattr(message, "error_message") and message.error_message:
                msg_info["error_message"] = message.error_message
            
            # Format the log message
            log_msg = f"{direction} [{msg_id}] {msg_type}"
            if is_error:
                logger.error(f"{log_msg} - {json.dumps(msg_info, default=str)}")
            else:
                logger.debug(f"{log_msg} - {json.dumps(msg_info, default=str)}")
                
        except Exception as e:
            logger.error(f"Error logging message: {e}")