# app/processors/audio/processor.py
import logging
import os
import tempfile
from typing import Dict, Any, Optional, Union, BinaryIO
from datetime import datetime
import whisper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Processes audio files by transcribing them to text"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_name = "base"  # Use small model for faster processing
    
    async def extract(self, audio_content: Union[str, bytes, BinaryIO]) -> Dict[str, Any]:
        """Extract text content from audio via transcription
        
        Args:
            audio_content: Either a file path, bytes content, or file-like object
            
        Returns:
            Dict containing transcribed text and metadata
        """
        try:
            # Lazy load the model when needed
            if self.model is None:
                self.logger.info(f"Loading Whisper model: {self.model_name}")
                try:
                    self.model = whisper.load_model(self.model_name)
                    self.logger.info("Whisper model loaded successfully")
                except Exception as e:
                    self.logger.error(f"Error loading Whisper model: {str(e)}")
                    return {
                        "status": "error",
                        "message": f"Error loading transcription model: {str(e)}"
                    }
            
            # Process the audio content based on what was provided
            if isinstance(audio_content, str):
                # Check if it's a file path or base64
                if audio_content.startswith("data:audio"):
                    # Process base64 encoded audio
                    return await self._process_from_base64(audio_content)
                else:
                    # Treat as file path
                    return await self._process_from_path(audio_content)
            elif isinstance(audio_content, bytes) or hasattr(audio_content, 'read'):
                # Treat as bytes content or file-like object
                return await self._process_from_bytes(audio_content)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported audio content type: {type(audio_content)}"
                }
        
        except Exception as e:
            self.logger.error(f"Error processing audio content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing audio content: {str(e)}"
            }
    
    async def _process_from_path(self, file_path: str) -> Dict[str, Any]:
        """Process audio from a file path"""
        try:
            self.logger.info(f"Transcribing audio from file path: {file_path}")
            result = self.model.transcribe(file_path)
            return self._build_response(result, os.path.basename(file_path))
        except Exception as e:
            self.logger.error(f"Error transcribing audio file {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error transcribing audio file: {str(e)}"
            }
    
    async def _process_from_bytes(self, content: Union[bytes, BinaryIO]) -> Dict[str, Any]:
        """Process audio from bytes or file-like object"""
        try:
            # Save bytes to a temporary file for Whisper to process
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                # If it's a file-like object, read its content
                if hasattr(content, 'read'):
                    content_bytes = content.read()
                    if hasattr(content, 'name'):
                        filename = os.path.basename(content.name)
                    else:
                        filename = "audio_file"
                else:
                    content_bytes = content
                    filename = "audio_file"
                
                # Write bytes to temp file
                temp_file.write(content_bytes)
            
            self.logger.info(f"Transcribing audio from bytes (saved to temp file: {temp_path})")
            result = self.model.transcribe(temp_path)
            
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                self.logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
            return self._build_response(result, filename)
        except Exception as e:
            self.logger.error(f"Error transcribing audio from bytes: {str(e)}")
            return {
                "status": "error",
                "message": f"Error transcribing audio content: {str(e)}"
            }
    
    async def _process_from_base64(self, base64_data: str) -> Dict[str, Any]:
        """Process audio from base64 encoded data"""
        try:
            import base64
            from io import BytesIO
            
            # Extract the base64 data part and content type
            parts = base64_data.split(',')
            if len(parts) != 2:
                return {
                    "status": "error",
                    "message": "Invalid base64 audio data format"
                }
            
            header = parts[0]
            content_type = header.split(':')[1].split(';')[0] if ':' in header else "audio/unknown"
            
            # Determine file extension based on content type
            extension = ".wav"  # Default
            if "mp3" in content_type:
                extension = ".mp3"
            elif "m4a" in content_type or "mp4" in content_type:
                extension = ".m4a"
            
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(parts[1])
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)
            
            self.logger.info(f"Transcribing audio from base64 (saved to temp file: {temp_path})")
            result = self.model.transcribe(temp_path)
            
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                self.logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
            return self._build_response(result, f"audio_file{extension}")
        except Exception as e:
            self.logger.error(f"Error transcribing audio from base64: {str(e)}")
            return {
                "status": "error",
                "message": f"Error transcribing audio content: {str(e)}"
            }
    
    def _build_response(self, transcription_result: Dict, filename: str = "audio_file") -> Dict[str, Any]:
        """Build a structured response from the transcription result"""
        try:
            text = transcription_result.get("text", "").strip()
            
            # Extract metadata from the result
            segments = transcription_result.get("segments", [])
            duration = 0
            if segments and len(segments) > 0:
                duration = segments[-1].get("end", 0)
            
            # Format duration as MM:SS
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_formatted = f"{minutes:02d}:{seconds:02d}"
            
            # Create a title from the filename
            title = os.path.splitext(filename)[0].replace("_", " ").title()
            if title == "Audio File":
                # Try to create a title from the first line of transcribed text
                if text:
                    lines = text.split(".")
                    if lines and lines[0]:
                        potential_title = lines[0].strip()
                        if len(potential_title) > 10 and len(potential_title) < 100:
                            title = potential_title
            
            return {
                "status": "success",
                "title": title,
                "filename": filename,
                "text": text,
                "duration": duration_formatted,
                "duration_seconds": duration,
                "language": transcription_result.get("language", "unknown"),
                "summary": self._create_preview(text),
                "extracted_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error building response: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing transcription results: {str(e)}"
            }
    
    def _create_preview(self, text: str, max_length: int = 500) -> str:
        """Create a preview/summary of the transcribed text"""
        if not text:
            return "No transcription available"
        
        # For basic preview, truncate the text
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point (end of sentence)
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > 0:
            return truncated[:last_period + 1] + "..."
        
        return truncated + "..."