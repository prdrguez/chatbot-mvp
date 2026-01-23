import reflex as rx
import hashlib
import time

from chatbot_mvp.config.settings import get_admin_password


class AuthState(rx.State):
    """
    Simple authentication state for admin access.
    
    Handles password-based authentication with session management
    for protecting admin routes.
    """
    
    # Authentication state
    is_authenticated: bool = False
    auth_error: str = ""
    login_attempt_count: int = 0
    last_attempt_time: float = 0.0
    session_timeout: int = 3600  # 1 hour in seconds
    login_time: float = 0.0
    
    # Login form state
    password_input: str = ""
    loading: bool = False
    
    @rx.var
    def is_locked_out(self) -> bool:
        """
        Check if user is temporarily locked out due to failed attempts.
        
        Returns:
            True if locked out, False otherwise
        """
        if self.login_attempt_count >= 3:
            time_since_last = time.time() - self.last_attempt_time
            return time_since_last < 300  # 5 minutes lockout
        return False
    
    @rx.var
    def lockout_time_remaining(self) -> int:
        """
        Calculate remaining lockout time in seconds.
        
        Returns:
            Seconds remaining until lockout expires
        """
        if self.is_locked_out:
            time_since_last = time.time() - self.last_attempt_time
            remaining = 300 - int(time_since_last)
            return max(0, remaining)
        return 0
    
    @rx.var
    def session_expired(self) -> bool:
        """
        Check if current session has expired.
        
        Returns:
            True if session expired, False otherwise
        """
        if not self.is_authenticated:
            return False
        
        time_since_login = time.time() - self.login_time
        return time_since_login > self.session_timeout
    
    def login(self) -> None:
        """
        Attempt to authenticate with provided password.
        """
        # Clear previous error
        self.auth_error = ""
        self.loading = True
        
        # Check if locked out
        if self.is_locked_out:
            self.auth_error = f"Demasiados intentos. Intenta en {self.lockout_time_remaining}s"
            self.loading = False
            return
        
        # Validate password
        if self._validate_password(self.password_input):
            self.is_authenticated = True
            self.login_time = time.time()
            self.login_attempt_count = 0
            self.password_input = ""
            self.auth_error = ""
        else:
            self.login_attempt_count += 1
            self.last_attempt_time = time.time()
            
            remaining_attempts = 3 - self.login_attempt_count
            if remaining_attempts > 0:
                self.auth_error = f"Contraseña incorrecta. {remaining_attempts} intentos restantes."
            else:
                self.auth_error = "Demasiados intentos. Espera 5 minutos."
        
        self.loading = False
    
    def _validate_password(self, password: str) -> bool:
        """
        Validate provided password against configured password.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password matches, False otherwise
        """
        if not password:
            return False
        
        # Get configured password
        admin_password = get_admin_password()
        if not admin_password:
            # No password configured - deny access
            return False
        
        # Use SHA-256 for comparison to avoid storing plain passwords
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        admin_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        return password_hash == admin_hash
    
    def logout(self) -> None:
        """
        Logout and clear authentication state.
        """
        self.is_authenticated = False
        self.login_time = 0.0
        self.auth_error = ""
        self.password_input = ""
        self.login_attempt_count = 0
    
    def check_session(self) -> None:
        """
        Check if current session is still valid.
        Called on page load to ensure session hasn't expired.
        """
        if self.is_authenticated and self.session_expired:
            self.logout()
    
    def set_password(self, value: str) -> None:
        """
        Set password input value.
        
        Args:
            value: Password input value
        """
        self.password_input = value
        # Clear error when user starts typing
        if self.auth_error and value:
            self.auth_error = ""