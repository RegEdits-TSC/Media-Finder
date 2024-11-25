class EnvFileCreationError(Exception):
    """Exception raised for errors in the creation of the .env file."""
    def __init__(self, file_path, message="Failed to create .env file"):
        self.file_path = file_path
        self.message = f"{message}: {file_path}"
        super().__init__(self.message)

class MissingEnvironmentVariableError(Exception):
    """Exception raised for missing environment variables."""
    def __init__(self, missing_vars):
        self.missing_vars = missing_vars
        super().__init__(f"Missing required environment variables: {', '.join(missing_vars)}")

class NoValidTrackersError(Exception):
    """Exception raised when no valid trackers are found."""
    def __init__(self, message="No valid tracker API key and URL pairs found."):
        super().__init__(message)

class MissingArgumentError(Exception):
    """Exception raised for missing required arguments."""
    def __init__(self, message="Missing required argument."):
        self.message = message
        super().__init__(self.message)

class InvalidTMDbIDError(Exception):
    """Exception raised for invalid TMDb ID."""
    def __init__(self, message="Invalid TMDb ID."):
        self.message = message
        super().__init__(self.message)

class NoSuitableResultError(Exception):
    """Exception raised when no suitable result is selected."""
    def __init__(self, message="No suitable result selected."):
        self.message = message
        super().__init__(self.message)

class NoResultsError(Exception):
    """Exception raised when there are no results to process."""
    def __init__(self, message="No results to process."):
        self.message = message
        super().__init__(self.message)

class NoResultsFoundError(Exception):
    """Exception raised when there are no results based on search."""
    def __init__(self, message="No results for current search query."):
        self.message = message
        super().__init__(self.message)

class InvalidChoiceError(Exception):
    """Exception raised when the user makes an invalid choice."""
    def __init__(self, message="Invalid choice made by the user."):
        self.message = message
        super().__init__(self.message)