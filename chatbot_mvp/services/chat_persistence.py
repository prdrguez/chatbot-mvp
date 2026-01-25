"""
Chat persistence service for storing and retrieving chat conversations.

This module provides:
- JSON-based chat storage
- Session management
- Message history retrieval
- Export functionality
- Search capabilities
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ChatPersistenceError(Exception):
    """Custom exception for chat persistence errors."""
    pass


class ChatPersistence:
    """Handles persistence of chat conversations."""
    
    def __init__(self, storage_dir: str = "data/chats"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.storage_dir / "sessions.json"
        self._ensure_sessions_file()
    
    def _ensure_sessions_file(self):
        """Ensure the sessions registry file exists."""
        if not self.sessions_file.exists():
            self.sessions_file.write_text(json.dumps({}))
    
    def _load_sessions(self) -> Dict:
        """Load sessions registry from file."""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            raise ChatPersistenceError(f"Error loading sessions: {exc}")
    
    def _save_sessions(self, sessions: Dict):
        """Save sessions registry to file."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            raise ChatPersistenceError(f"Error saving sessions: {exc}")
    
    def save_session(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        user_context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save a chat session to persistent storage.
        
        Args:
            session_id: Unique session identifier
            messages: List of chat messages
            user_context: Optional user context information
            metadata: Optional session metadata
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create session data
            session_data = {
                "session_id": session_id,
                "messages": messages,
                "user_context": user_context or {},
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages),
            }
            
            # Save individual session file
            session_file = self.storage_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Update sessions registry
            sessions = self._load_sessions()
            sessions[session_id] = {
                "created_at": session_data["created_at"],
                "updated_at": session_data["updated_at"],
                "message_count": session_data["message_count"],
                "has_user_context": bool(user_context),
                "preview": self._generate_preview(messages),
            }
            self._save_sessions(sessions)
            
            return True
            
        except Exception as exc:
            raise ChatPersistenceError(f"Error saving session: {exc}")
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """
        Load a chat session from storage.
        
        Args:
            session_id: Session identifier to load
            
        Returns:
            Session data or None if not found
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if not session_file.exists():
                return None
                
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as exc:
            raise ChatPersistenceError(f"Error loading session: {exc}")
    
    def get_recent_sessions(
        self, 
        limit: int = 10,
        include_empty: bool = False
    ) -> List[Dict]:
        """
        Get list of recent chat sessions.
        
        Args:
            limit: Maximum number of sessions to return
            include_empty: Whether to include sessions with no messages
            
        Returns:
            List of session summaries
        """
        try:
            sessions = self._load_sessions()
            
            # Filter and sort sessions
            filtered_sessions = [
                {
                    "session_id": session_id,
                    **data,
                }
                for session_id, data in sessions.items()
                if include_empty or data.get("message_count", 0) > 0
            ]
            
            # Sort by updated_at descending
            filtered_sessions.sort(
                key=lambda x: x.get("updated_at", ""), 
                reverse=True
            )
            
            return filtered_sessions[:limit]
            
        except Exception as exc:
            raise ChatPersistenceError(f"Error getting recent sessions: {exc}")
    
    def search_sessions(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Dict]:
        """
        Search through chat sessions for matching content.
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of matching sessions with highlights
        """
        try:
            sessions = self._load_sessions()
            results = []
            query_lower = query.lower()
            
            for session_id, session_data in sessions.items():
                # Search in preview first (faster)
                preview = session_data.get("preview", "")
                if query_lower in preview.lower():
                    results.append({
                        "session_id": session_id,
                        **session_data,
                        "match_type": "preview",
                    })
                    continue
                
                # Load full session and search in messages
                full_session = self.load_session(session_id)
                if full_session:
                    for message in full_session.get("messages", []):
                        content = message.get("content", "")
                        if query_lower in content.lower():
                            results.append({
                                "session_id": session_id,
                                **session_data,
                                "match_type": "message",
                                "matched_message": {
                                    "role": message.get("role"),
                                    "content": content[:100] + "..." if len(content) > 100 else content,
                                },
                            })
                            break
            
            # Sort by updated_at and limit results
            results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return results[:limit]
            
        except Exception as exc:
            raise ChatPersistenceError(f"Error searching sessions: {exc}")
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session from storage.
        
        Args:
            session_id: Session identifier to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Remove session file
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # Update sessions registry
            sessions = self._load_sessions()
            if session_id in sessions:
                del sessions[session_id]
                self._save_sessions(sessions)
                return True
            
            return False
            
        except Exception as exc:
            raise ChatPersistenceError(f"Error deleting session: {exc}")
    
    def export_session(
        self, 
        session_id: str, 
        format_type: str = "json"
    ) -> Optional[str]:
        """
        Export a chat session in specified format.
        
        Args:
            session_id: Session to export
            format_type: Export format ('json', 'txt', 'csv')
            
        Returns:
            Exported content as string or None if not found
        """
        session = self.load_session(session_id)
        if not session:
            return None
        
        try:
            if format_type.lower() == "json":
                return json.dumps(session, indent=2, ensure_ascii=False)
                
            elif format_type.lower() == "txt":
                return self._format_as_txt(session)
                
            elif format_type.lower() == "csv":
                return self._format_as_csv(session)
                
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as exc:
            raise ChatPersistenceError(f"Error exporting session: {exc}")
    
    def get_statistics(self) -> Dict:
        """Get usage statistics for all sessions."""
        try:
            sessions = self._load_sessions()
            
            total_sessions = len(sessions)
            total_messages = sum(s.get("message_count", 0) for s in sessions.values())
            sessions_with_context = sum(1 for s in sessions.values() if s.get("has_user_context", False))
            
            # Calculate date range
            dates = [
                datetime.fromisoformat(s.get("created_at", ""))
                for s in sessions.values()
                if s.get("created_at")
            ]
            
            if dates:
                oldest_date = min(dates)
                newest_date = max(dates)
                days_active = (newest_date - oldest_date).days + 1
            else:
                oldest_date = newest_date = None
                days_active = 0
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "sessions_with_context": sessions_with_context,
                "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0,
                "oldest_session": oldest_date.isoformat() if oldest_date else None,
                "newest_session": newest_date.isoformat() if newest_date else None,
                "days_active": days_active,
                "messages_per_day": total_messages / days_active if days_active > 0 else 0,
            }
            
        except Exception as exc:
            raise ChatPersistenceError(f"Error getting statistics: {exc}")
    
    def _generate_preview(self, messages: List[Dict[str, str]]) -> str:
        """Generate a preview text from messages."""
        if not messages:
            return ""
        
        # Get first user message for preview
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                return content[:50] + "..." if len(content) > 50 else content
        
        return "No user messages"
    
    def _format_as_txt(self, session: Dict) -> str:
        """Format session as plain text."""
        lines = [
            f"Chat Session: {session.get('session_id', 'unknown')}",
            f"Created: {session.get('created_at', 'unknown')}",
            f"Messages: {len(session.get('messages', []))}",
            "=" * 50,
        ]
        
        for message in session.get("messages", []):
            role = message.get("role", "unknown").upper()
            content = message.get("content", "")
            lines.append(f"\n{role}:")
            lines.append(content)
        
        return "\n".join(lines)
    
    def _format_as_csv(self, session: Dict) -> str:
        """Format session as CSV."""
        lines = ["session_id,created_at,updated_at,role,content"]
        
        session_id = session.get("session_id", "")
        created_at = session.get("created_at", "")
        updated_at = session.get("updated_at", "")
        for message in session.get("messages", []):
            role = message.get("role", "")
            content = message.get("content", "").replace('"', '""')  # Escape quotes
            lines.append(
                f'"{session_id}","{created_at}","{updated_at}","{role}","{content}"'
            )
        
        return "\n".join(lines)


# Factory function for creating persistence instances
def create_chat_persistence(storage_dir: str = "data/chats") -> ChatPersistence:
    """
    Factory function to create a ChatPersistence instance.
    
    Args:
        storage_dir: Directory for storing chat data
        
    Returns:
        Configured ChatPersistence instance
    """
    return ChatPersistence(storage_dir)
