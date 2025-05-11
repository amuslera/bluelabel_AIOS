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
                if audio_content.startswith("data:audio") or audio_content.startswith("data:mp3") or audio_content.startswith("data:"):
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
            
            # Create a temp dir with short path to avoid command line length issues
            temp_dir = tempfile.mkdtemp(prefix="a_")
            filename = os.path.basename(file_path)
            extension = os.path.splitext(filename)[1] if os.path.splitext(filename)[1] else ".wav"
            temp_path = os.path.join(temp_dir, f"a{extension}")
            
            try:
                # Copy the file to a short path location
                import shutil
                shutil.copy(file_path, temp_path)
                
                # Use audio loader to handle the file without full ffmpeg command
                import numpy as np
                try:
                    # Try direct transcription first
                    result = self.model.transcribe(temp_path)
                except Exception as e:
                    self.logger.warning(f"Direct transcription failed, trying alternate method: {str(e)}")
                    # If that fails, try loading the audio as an array first
                    import librosa
                    audio_array, sr = librosa.load(temp_path, sr=16000)
                    result = self.model.transcribe(audio_array)
                
                return self._build_response(result, filename)
            finally:
                # Clean up the temporary directory and all files in it
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temporary directory {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary directory {temp_dir}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error transcribing audio file {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error transcribing audio file: {str(e)}"
            }
    
    async def _process_from_bytes(self, content: Union[bytes, BinaryIO]) -> Dict[str, Any]:
        """Process audio from bytes or file-like object"""
        try:
            # Create a temp dir with short path to avoid command line length issues
            temp_dir = tempfile.mkdtemp(prefix="a_")
            temp_path = os.path.join(temp_dir, "a.wav")
            
            try:
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
                
                # Write bytes to temp file with a short path
                with open(temp_path, 'wb') as f:
                    f.write(content_bytes)
                
                self.logger.info(f"Transcribing audio from bytes (saved to temp file: {temp_path})")
                
                # Use audio loader to handle the file without full ffmpeg command
                import numpy as np
                try:
                    # Try direct transcription first
                    result = self.model.transcribe(temp_path)
                except Exception as e:
                    self.logger.warning(f"Direct transcription failed, trying alternate method: {str(e)}")
                    # If that fails, try loading the audio as an array first
                    import librosa
                    audio_array, sr = librosa.load(temp_path, sr=16000)
                    result = self.model.transcribe(audio_array)
                
                return self._build_response(result, filename)
            finally:
                # Clean up the temporary directory and all files in it
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temporary directory {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary directory {temp_dir}: {str(e)}")
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
            import shutil
            
            # Don't use the full base64_data string in logs or filenames to avoid "filename too long" errors
            self.logger.info(f"Processing base64 audio data (length: {len(base64_data)})")
            
            # Special handling for data URI format
            content_type = "audio/unknown"
            base64_part = base64_data
            
            # If it's a data URI (e.g., data:audio/mp3;base64,XXXX)
            if base64_data.startswith('data:'):
                # Extract the content type and base64 part carefully
                # Parse without using the full string in error messages
                header_end = base64_data.find(',')
                if header_end > 0:
                    header = base64_data[:header_end]
                    base64_part = base64_data[header_end + 1:]
                    
                    # Get content type
                    if ':' in header:
                        type_parts = header.split(':')
                        if len(type_parts) > 1 and ';' in type_parts[1]:
                            content_type = type_parts[1].split(';')[0]
                        else:
                            content_type = type_parts[1]
                else:
                    self.logger.warning("Invalid base64 data format, missing comma separator")
                    return {
                        "status": "error",
                        "message": "Invalid base64 audio data format"
                    }
            else:
                # If it's just base64 data without the prefix
                base64_part = base64_data
            
            # Determine file extension based on content type
            extension = ".wav"  # Default
            if "mp3" in content_type:
                extension = ".mp3"
            elif "m4a" in content_type or "mp4" in content_type:
                extension = ".m4a"
            
            # Create a temp dir with very short path
            temp_dir = tempfile.mkdtemp(prefix="a_")
            temp_path = os.path.join(temp_dir, f"a{extension}")
            
            try:
                # Decode and write base64 to the temp file
                try:
                    audio_bytes = base64.b64decode(base64_part)
                    with open(temp_path, 'wb') as f:
                        f.write(audio_bytes)
                except Exception as decode_error:
                    self.logger.error(f"Failed to decode base64 data: {str(decode_error)}")
                    return {
                        "status": "error",
                        "message": f"Failed to decode audio data: {str(decode_error)}"
                    }
                
                self.logger.info(f"Transcribing audio from base64 (saved to temp file: {temp_path})")
                
                # Use audio loader to handle the file without full ffmpeg command
                import numpy as np
                try:
                    # Try direct transcription first
                    result = self.model.transcribe(temp_path)
                except Exception as e:
                    self.logger.warning(f"Direct transcription failed, trying alternate method: {str(e)}")
                    # If that fails, try loading the audio as an array first
                    import librosa
                    audio_array, sr = librosa.load(temp_path, sr=16000)
                    result = self.model.transcribe(audio_array)
                
                return self._build_response(result, f"audio_file{extension}")
            finally:
                # Clean up the temporary directory and all files in it
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temporary directory {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary directory {temp_dir}: {str(e)}")
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